"""Exercise the local Compose broker-outage path using a real clip.

Requires --exercise-outage: briefly stops only this project's local Redis/worker/scheduler.
Restarts them in finally. Never run against a production stack.
"""

import argparse
import secrets
import subprocess
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def compose(*args):
    subprocess.run(["docker", "compose", *args], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exercise-outage", action="store_true", required=True)
    args = parser.parse_args()
    if not args.exercise_outage:
        parser.error("Explicit local outage opt-in required")
    token = secrets.token_urlsafe(32)
    headers = {"X-Submission-Token": token}
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=30) as client:
        client.get("/health").raise_for_status()
        try:
            compose("stop", "scheduler", "worker", "redis")

            def submit():
                with (ROOT / "var/fixtures/clean.mp4").open("rb") as clip:
                    return client.post(
                        "/v1/recognitions",
                        headers=headers,
                        files={"file": ("clip.mp4", clip, "video/mp4")},
                    )

            first = submit()
            assert first.status_code == 202, first.text
            credentials = first.json()
            replay = submit()
            assert replay.status_code == 202, replay.text
            assert replay.json()["id"] == credentials["id"], (
                "Retry created a duplicate job"
            )
            path = f"/v1/recognitions/{credentials['id']}"
            auth = {"Authorization": f"Bearer {credentials['access_token']}"}
            assert client.get(path, headers=auth).json()["status"] == "queued"
            print(
                "Redis offline: accepted and retained one queued job; retry reused its ID."
            )
        finally:
            compose("up", "-d", "--wait", "redis", "worker", "scheduler")
        deadline = time.monotonic() + 90
        while True:
            response = client.get(path, headers=auth)
            response.raise_for_status()
            job = response.json()
            if job["status"] in ["completed", "failed"]:
                break
            if time.monotonic() >= deadline:
                raise AssertionError("Scheduler recovery exceeded 90 seconds")
            time.sleep(0.5)
        assert job["status"] == "completed", job
        assert job["result"]["classification"] == "matching_segment", job
        assert abs(job["result"]["candidates"][0]["start_seconds"] - 4) <= 0.5, job
        assert client.delete(path, headers=auth).status_code == 204
        print(
            "Redis restored: scheduler dispatched retained clip; real worker matched at 4 seconds."
        )


if __name__ == "__main__":
    main()
