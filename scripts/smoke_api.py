"""Exercise a running API and independent Celery worker against real media."""

import argparse
import time
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--fixtures", type=Path, default=Path("var/fixtures"))
    args = parser.parse_args()
    with httpx.Client(base_url=args.base_url, timeout=30) as client:
        client.get("/health").raise_for_status()
        for name, expected in [("clean", "matching_segment"), ("negative", "no_match")]:
            with (args.fixtures / f"{name}.mp4").open("rb") as file:
                response = client.post(
                    "/v1/recognitions",
                    files={"file": (f"{name}.mp4", file, "video/mp4")},
                )
            assert response.status_code == 202, response.text
            access = response.json()
            path = f"/v1/recognitions/{access['id']}"
            headers = {"Authorization": f"Bearer {access['access_token']}"}
            assert client.get(path).status_code == 404
            deadline = time.monotonic() + 45
            while True:
                response = client.get(path, headers=headers)
                response.raise_for_status()
                job = response.json()
                if job["status"] in ["completed", "failed"]:
                    break
                if time.monotonic() > deadline:
                    raise AssertionError("Worker did not finish within 45 seconds")
                time.sleep(0.25)
            assert job["status"] == "completed", job
            assert job["result"]["classification"] == expected, job
            if name == "clean":
                assert (
                    abs(job["result"]["candidates"][0]["start_seconds"] - 4) <= 0.5
                ), job
            assert client.delete(path, headers=headers).status_code == 204
            assert client.get(path, headers=headers).status_code == 404
            print(
                f"{name}: {expected}; worker completed; ownership and deletion verified"
            )


if __name__ == "__main__":
    main()
