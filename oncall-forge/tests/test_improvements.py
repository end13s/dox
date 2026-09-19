import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import time

import httpx
import pytest

STAGE = Path(__file__).resolve().parents[1]
APP_ROOT = STAGE if (STAGE / 'app').exists() else STAGE.parent / 'checkout-service-demo'
sys.path.insert(0, str(APP_ROOT))
sys.path.insert(0, str(STAGE / 'ops'))
from app.telemetry import Telemetry
from app.log_records import recent_records
from incident_monitor import Monitor, Store, apply_event


def test_window_survives_restart_and_requires_live_traffic(tmp_path):
    path = tmp_path / 'events.sqlite3'
    ledger = Telemetry(path)
    for second in range(40):
        ledger.record(second % 5 == 0, now=1000+second)
    reopened = Telemetry(path)
    assert reopened.metrics(now=1040)['errors'] == 8
    assert not reopened.metrics(now=1040)['recovery_ready']
    assert reopened.history(now=1040)[-1]['value'] == 20
    assert not reopened.metrics(now=1110)['traffic_active']
    assert not reopened.metrics(now=1110)['recovery_ready']
    for second in range(40):
        reopened.record(False, now=1120+second)
    assert reopened.metrics(now=1160)['recovery_ready']


def test_logs_keep_tracebacks_severity_and_expire_injection(tmp_path):
    path = tmp_path / 'app.log'
    path.write_text(
        '2026-09-19T12:00:00Z ERROR ops: PROMPT-INJECTION TEST stale\n'
        '2026-09-19T12:10:00Z ERROR checkout: failed\nTraceback (most recent call last):\n  line\nKeyError: NOTREAL\n'
        '2026-09-19T12:10:01Z CRITICAL checkout: critical\n'
        '2026-09-19T12:10:02Z INFO checkout: okay\n', encoding='utf-8')
    from datetime import datetime, timezone
    now = datetime(2026, 9, 19, 12, 10, 3, tzinfo=timezone.utc).timestamp()
    result = recent_records(path, now=now)
    assert len(result) == 2
    assert 'Traceback' in result[0] and 'KeyError' in result[0]
    assert 'stale' not in '\n'.join(result)
    path.write_text('2026-09-19T12:10:00Z ERROR ops: PROMPT-INJECTION TEST fresh\n'
                    '2026-09-19T12:10:01Z ERROR checkout: failed\n', encoding='utf-8')
    assert len(recent_records(path, limit=1, now=now)) == 1


class FakeForge:
    def __init__(self):
        self.posts = []
        self.fail_turn = False

    def agent(self): return 'agent-id'
    def existing(self, *args): return None
    def events(self, *args): return []
    def lookup(self, *args): return []
    def post(self, path, body):
        self.posts.append((path, body))
        if self.fail_turn and path.endswith('/turns'):
            raise TimeoutError('lost response')
        return {'id': 'session-id'}


BAD = dict(requests=300, errors=60, error_rate=.2, traffic_active=True, recovery_ready=False)
GOOD = dict(requests=300, errors=0, error_rate=0, traffic_active=True, recovery_ready=True)


def test_two_incident_cycles_and_monitor_restart_no_duplicates(tmp_path):
    remote = FakeForge()
    store = Store(tmp_path / 'incident.json')
    monitor = Monitor(store, remote)
    for clock in (0, 5, 10): monitor.tick(BAD, clock)
    assert len(remote.posts) == 2
    monitor = Monitor(store, remote)
    for clock in (15, 20, 25): monitor.tick(BAD, clock)
    assert len(remote.posts) == 2
    monitor.state['_terminal'] = True
    monitor.state['_pending'] = [{'type': 'tool.approval_required'}]
    for clock in (30, 65, 95): monitor.tick(GOOD, clock)
    assert not monitor.state['_armed']  # Healthy telemetry cannot dismiss an approval.
    monitor.state['_pending'] = []
    monitor.tick(GOOD, 100)
    assert monitor.state['_armed']
    for clock in (110, 115, 120): monitor.tick(BAD, clock)
    assert len(remote.posts) == 4


def test_uncertain_turn_is_not_resent(tmp_path):
    remote = FakeForge(); remote.fail_turn = True
    store = Store(tmp_path / 'incident.json')
    monitor = Monitor(store, remote)
    monitor.tick(BAD, 0)
    with pytest.raises(TimeoutError): monitor.tick(BAD, 10)
    restarted = Monitor(store, remote)
    with pytest.raises(RuntimeError, match='unconfirmed'): restarted.tick(BAD, 20)
    assert len(remote.posts) == 2


def test_progress_uses_tool_results_not_agent_claims():
    state = {}
    apply_event(state, {'type': 'model.message', 'content': 'Merged and recovered!'})
    assert not state.get('_merged')
    call = {'id': 'merge', 'function': {'name': 'call_tool', 'arguments': json.dumps({
        'tool_name': 'merge_pull_request', 'input': {'owner': 'bombert34', 'repo': 'checkout-service-demo'}})}}
    apply_event(state, {'type': 'model.message', 'tool_calls': [call]})
    apply_event(state, {'type': 'tool.response', 'tool_call_id': 'merge', 'content': '{"error":"403 denied"}'})
    assert not state.get('_merged')
    apply_event(state, {'type': 'tool.approval_required', 'id': 'approval', 'tool_calls': [{'id': 'merge'}]})
    assert state['stage'] == 'Waiting for human approval'
    apply_event(state, {'type': 'tool.response', 'tool_call_id': 'merge', 'content': '{"merged":true}'})
    assert state['_merged']


@pytest.mark.parametrize('cycle', [1, 2])
def test_real_process_incident_restart_and_recovery(tmp_path, cycle):
    """Two isolated HTTP rehearsals; no GitHub mutations or production outage."""
    appdir = tmp_path / 'app'; shutil.copytree(APP_ROOT / 'app', appdir)
    (appdir / '__init__.py').touch()
    pricing = appdir / 'pricing.py'
    healthy = 'def apply_discount(total, code):\n    return round(total*(1-{"SAVE10":.1}.get(code,0)),2)\n'
    broken = 'def apply_discount(total, code):\n    return round(total*(1-{"SAVE10":.1}[code]),2)\n'
    pricing.write_text(broken)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    env = os.environ.copy(); env['PYTHONPATH'] = str(tmp_path); env['DOX_DATA_DIR'] = str(tmp_path / 'logs')
    def start():
        proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', str(port)],
                                cwd=tmp_path, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            try:
                if httpx.get(url+'/health', timeout=.5).status_code == 200: return proc
            except httpx.HTTPError: pass
            if proc.poll() is not None: pytest.fail('Test service failed to start')
            time.sleep(.1)
        proc.kill(); proc.wait(); pytest.fail('Timed out starting test service')
    proc = start()
    try:
        with httpx.Client(base_url=url) as client:
            assert client.post('/checkout', json={'cart_total':100,'code':'NOTREAL'}).status_code == 500
            assert client.post('/checkout', json={'cart_total':100,'code':'SAVE10'}).status_code == 200
            before = client.get('/metrics').json()
            assert before['errors'] == 1
        proc.terminate(); proc.wait(timeout=10)
        pricing.write_text(healthy)
        proc = start()
        with httpx.Client(base_url=url) as client:
            persisted = client.get('/metrics').json()
            assert persisted['errors'] == 1  # Restart cannot erase the incident.
            assert not persisted['recovery_ready']
            assert client.post('/checkout', json={'cart_total':100,'code':'NOTREAL'}).json() == {'total':100.0}
            html = client.get('/status').text
            assert 'Pull requests ↗' not in html
            assert '<h1 class="wordmark">dox</h1>' in html
            ledger = Telemetry(tmp_path/'logs'/'telemetry.sqlite3')
            # Advance the persisted samples outside the window without a minute-long sleep.
            with ledger.connect() as db: db.execute('UPDATE requests SET ts=ts-120')
            now=time.time()
            for second in range(40): ledger.record(False, now=now-40+second)
            recovered=client.get('/metrics').json()
            assert recovered['recovery_ready'] and recovered['requests'] == 40
            data=client.get('/status-data').json()
            assert data['history'] and data['commit']
    finally:
        proc.terminate(); proc.wait(timeout=10)
