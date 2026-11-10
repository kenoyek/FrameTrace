"""Validate the initial migration in a disposable local PostgreSQL database.

Only use with the local Compose instance: it needs database/role creation privileges.
Does not validate hosted Supabase Auth, JWTs, or tenant policies.
"""

from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql

LOCAL = "postgresql://frametrace:local-development-only@127.0.0.1:5432/frametrace"


def main():
    database = "frametrace_migration_test_" + uuid4().hex
    with psycopg.connect(LOCAL, autocommit=True) as admin:
        # These are unprivileged client roles in local PostgreSQL, not real auth accounts.
        for role in ["anon", "authenticated"]:
            exists = admin.execute(
                "select 1 from pg_roles where rolname = %s", (role,)
            ).fetchone()
            if not exists:
                admin.execute(
                    sql.SQL("create role {} nologin").format(sql.Identifier(role))
                )
        admin.execute(sql.SQL("create database {}").format(sql.Identifier(database)))
        try:
            dsn = LOCAL.rsplit("/", 1)[0] + "/" + database
            with psycopg.connect(dsn, autocommit=True) as connection:
                for migration in sorted(Path("supabase/migrations").glob("*.sql")):
                    connection.execute(migration.read_text())
                rows = connection.execute(
                    "select relname, relrowsecurity from pg_class where relname in ('reference_media', 'recognition_jobs', 'recognition_matches', 'recognition_execution', 'recognition_accounts', 'query_objects')"
                ).fetchall()
                assert len(rows) == 6 and all(enabled for _, enabled in rows), rows
                for role in ["anon", "authenticated"]:
                    connection.execute(
                        sql.SQL("set role {}").format(sql.Identifier(role))
                    )
                    for table in [
                        "reference_media",
                        "recognition_jobs",
                        "recognition_matches",
                        "recognition_execution",
                        "recognition_accounts",
                        "query_objects",
                    ]:
                        try:
                            connection.execute(
                                sql.SQL("select * from public.{}").format(
                                    sql.Identifier(table)
                                )
                            )
                        except psycopg.errors.InsufficientPrivilege:
                            pass
                        else:
                            raise AssertionError(f"{role} could read {table}")
                    connection.execute("reset role")
                print(
                    "Migrations applied; RLS enabled on 6 tables; both client roles denied direct reads."
                )
        finally:
            admin.execute(sql.SQL("drop database {}").format(sql.Identifier(database)))


if __name__ == "__main__":
    main()
