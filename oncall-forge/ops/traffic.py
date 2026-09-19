"""Generates steady checkout traffic against the demo service, mixing
valid, empty, and unknown discount codes so the seeded bug shows up as a
realistic partial error rate rather than an all-or-nothing outage.
"""

import random
import time

import httpx

DEMO_URL = "http://localhost:8000"
CODES = ["SAVE10", "SAVE20", "WELCOME", "", "NOTREAL"]
REQ_PER_SEC = 5

if __name__ == "__main__":
    with httpx.Client(timeout=5) as client:
        while True:
            start = time.time()
            for _ in range(REQ_PER_SEC):
                code = random.choice(CODES)
                cart_total = round(random.uniform(10, 200), 2)
                try:
                    client.post(f"{DEMO_URL}/checkout", json={"cart_total": cart_total, "code": code})
                except httpx.HTTPError:
                    pass
            elapsed = time.time() - start
            time.sleep(max(0, 1 - elapsed))
