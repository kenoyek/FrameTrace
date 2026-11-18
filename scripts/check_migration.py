"""Check every migration and client-role boundary in disposable local PostgreSQL.

Uses only the local Compose database; creates/drops a uniquely named test database.
Does not establish hosted Supabase Auth, deployment-role or network readiness.
"""

from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql

LOCAL = "postgresql://frametrace:local-development-only@127.0.0.1:5432/frametrace"
TABLES = {
    "reference_media",
    "recognition_jobs",
    "recognition_matches",
    "recognition_execution",
    "recognition_accounts",
    "query_objects",
    "recognition_feedback",
    "catalog_audit",
}


def must_fail(connection, statement, error):
    try:
        connection.execute(statement)
    except error:
        return
    raise AssertionError(f"Expected {error.__name__}")


def check_constraints(connection):
    connection.execute(
        "insert into recognition_jobs (id, token_hash, status) values ('migration-job', 'test-only', 'completed')"
    )
    connection.execute(
        "insert into recognition_feedback (job_id, rating) values ('migration-job', 'helpful')"
    )
    must_fail(
        connection,
        "insert into recognition_feedback values ('migration-job', 'unsure')",
        psycopg.errors.UniqueViolation,
    )
    must_fail(
        connection,
        "update recognition_feedback set rating = 'invented'",
        psycopg.errors.CheckViolation,
    )
    must_fail(
        connection,
        "insert into recognition_feedback values ('missing-job', 'helpful')",
        psycopg.errors.ForeignKeyViolation,
    )
    connection.execute(
        "insert into catalog_audit (id, reference_id, action, actor, reason) values ('migration-event', 'reference-label', 'revoke', 'test-operator', 'Test only')"
    )
    must_fail(
        connection,
        "update catalog_audit set action = 'invented'",
        psycopg.errors.CheckViolation,
    )


def check_client_roles(connection):
    for role in ("anon", "authenticated"):
        flags = connection.execute(
            "select rolsuper, rolbypassrls from pg_roles where rolname = %s", (role,)
        ).fetchone()
        assert flags == (False, False), (role, flags)
        connection.execute(sql.SQL("set role {}").format(sql.Identifier(role)))
        try:
            for table in sorted(TABLES):
                for operation in (
                    "select * from public.{}",
                    "insert into public.{} default values",
                    "update public.{} set "
                    + (
                        "id = id"
                        if table
                        in {"catalog_audit", "reference_media", "recognition_jobs"}
                        else "job_id = job_id"
                    )
                    + " where false",
                    "delete from public.{} where false",
                ):
                    must_fail(
                        connection,
                        sql.SQL(operation).format(sql.Identifier(table)),
                        psycopg.errors.InsufficientPrivilege,
                    )
        finally:
            connection.execute("reset role")
        # Defense in depth: even a future accidental SELECT grant must not expose rows.
        for table in sorted(TABLES):
            connection.execute(
                sql.SQL("grant select on public.{} to {}").format(
                    sql.Identifier(table), sql.Identifier(role)
                )
            )
        connection.execute(sql.SQL("set role {}").format(sql.Identifier(role)))
        try:
            for table in sorted(TABLES):
                rows = connection.execute(
                    sql.SQL("select * from public.{}").format(sql.Identifier(table))
                ).fetchall()
                assert not rows, (role, table, "RLS exposed rows")
        finally:
            connection.execute("reset role")
            for table in sorted(TABLES):
                connection.execute(
                    sql.SQL("revoke select on public.{} from {}").format(
                        sql.Identifier(table), sql.Identifier(role)
                    )
                )


def main():
    database = "frametrace_migration_test_" + uuid4().hex
    with psycopg.connect(LOCAL, autocommit=True) as admin:
        for role in ("anon", "authenticated"):
            if not admin.execute(
                "select 1 from pg_roles where rolname = %s", (role,)
            ).fetchone():
                admin.execute(
                    sql.SQL("create role {} nologin").format(sql.Identifier(role))
                )
        admin.execute(sql.SQL("create database {}").format(sql.Identifier(database)))
        try:
            dsn = LOCAL.rsplit("/", 1)[0] + "/" + database
            with psycopg.connect(dsn, autocommit=True) as connection:
                migrations = sorted(Path("supabase/migrations").glob("*.sql"))
                assert migrations, "No migrations found; run from the repository root"
                for migration in migrations:
                    connection.execute(migration.read_text())
                rows = connection.execute(
                    "select c.relname, c.relrowsecurity from pg_class c join pg_namespace n on n.oid = c.relnamespace where n.nspname = 'public' and c.relkind = 'r'"
                ).fetchall()
                assert {name for name, _ in rows} == TABLES, rows
                assert all(enabled for _, enabled in rows), rows
                check_constraints(connection)
                check_client_roles(connection)
                connection.execute(
                    "delete from recognition_jobs where id = 'migration-job'"
                )
                assert (
                    connection.execute(
                        "select count(*) from recognition_feedback"
                    ).fetchone()[0]
                    == 0
                )
                assert (
                    connection.execute("select count(*) from catalog_audit").fetchone()[
                        0
                    ]
                    == 1
                )
                print(
                    f"{len(migrations)} migrations applied; RLS and client CRUD denial checked on {len(TABLES)} tables; feedback constraints/cascade and independent audit retention passed."
                )
        finally:
            admin.execute(sql.SQL("drop database {}").format(sql.Identifier(database)))


if __name__ == "__main__":
    main()
