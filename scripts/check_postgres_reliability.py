"""Run lease/idempotency tests against a new disposable local PostgreSQL database."""

import os
import subprocess
import sys
from uuid import uuid4

import psycopg
from psycopg import sql

LOCAL = "postgresql://frametrace:local-development-only@127.0.0.1:5432/frametrace"


def main():
    name = "frametrace_reliability_test_" + uuid4().hex
    with psycopg.connect(LOCAL, autocommit=True) as admin:
        admin.execute(sql.SQL("create database {}").format(sql.Identifier(name)))
        try:
            environment = os.environ.copy()
            environment["FRAMETRACE_TEST_DATABASE_URL"] = (
                "postgresql+psycopg://frametrace:local-development-only@127.0.0.1:5432/"
                + name
            )
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "services/api/tests/test_reliability.py",
                    "services/api/tests/test_accounts.py",
                    "-q",
                ],
                env=environment,
                check=True,
            )
        finally:
            admin.execute(sql.SQL("drop database {}").format(sql.Identifier(name)))


if __name__ == "__main__":
    main()
