"""Apply versioned SQL and prepare the read-only analytics runtime role."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import psycopg
from psycopg import sql


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IDENTIFIER_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


def _required_environment(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _validated_identifier(name: str) -> str:
    value = _required_environment(name)
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise RuntimeError(
            f"{name} must contain only lowercase letters, numbers, and underscores"
        )
    return value


def _connect() -> psycopg.Connection:
    return psycopg.connect(
        host=_required_environment("POSTGRES_HOST"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=_required_environment("POSTGRES_DB"),
        user=_required_environment("POSTGRES_USER"),
        password=_required_environment("POSTGRES_PASSWORD"),
        connect_timeout=10,
    )


def _ensure_change_history(connection: psycopg.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS public.database_change_history (
            change_kind text NOT NULL CHECK (change_kind IN ('migration', 'seed')),
            change_name text NOT NULL,
            checksum_sha256 text NOT NULL,
            applied_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (change_kind, change_name)
        )
        """
    )
    connection.commit()


def _apply_sql_directory(
    connection: psycopg.Connection,
    directory: Path,
    change_kind: str,
) -> None:
    scripts = sorted(directory.glob("*.sql"))
    if not scripts:
        raise RuntimeError(f"No SQL files found in {directory}")

    for script_path in scripts:
        script = script_path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(script.encode("utf-8")).hexdigest()
        recorded = connection.execute(
            """
            SELECT checksum_sha256
            FROM public.database_change_history
            WHERE change_kind = %s AND change_name = %s
            """,
            (change_kind, script_path.name),
        ).fetchone()
        connection.commit()

        if recorded:
            if recorded[0] != checksum:
                raise RuntimeError(
                    f"Applied {change_kind} changed on disk: {script_path.name}. "
                    "Create a new SQL file or reset the local database volume."
                )
            print(f"Skipping applied {change_kind}: {script_path.name}")
            continue

        with connection.transaction():
            connection.execute(script)
            connection.execute(
                """
                INSERT INTO public.database_change_history (
                    change_kind, change_name, checksum_sha256
                ) VALUES (%s, %s, %s)
                """,
                (change_kind, script_path.name, checksum),
            )
        print(f"Applied {change_kind}: {script_path.name}")


def _ensure_readonly_role(connection: psycopg.Connection) -> None:
    owner = _validated_identifier("POSTGRES_USER")
    runtime_role = _validated_identifier("ANALYTICS_DATABASE_READONLY_USER")
    runtime_password = _required_environment(
        "ANALYTICS_DATABASE_READONLY_PASSWORD"
    )
    timeout_ms = int(
        os.getenv("ANALYTICS_DATABASE_STATEMENT_TIMEOUT_MS", "15000")
    )
    if runtime_role == owner:
        raise RuntimeError("The runtime role must be different from the database owner")
    if timeout_ms <= 0:
        raise RuntimeError("ANALYTICS_DATABASE_STATEMENT_TIMEOUT_MS must be positive")

    role_exists = connection.execute(
        "SELECT 1 FROM pg_roles WHERE rolname = %s", (runtime_role,)
    ).fetchone()
    role_identifier = sql.Identifier(runtime_role)
    password_literal = sql.Literal(runtime_password)

    if role_exists:
        connection.execute(
            sql.SQL("ALTER ROLE {} WITH PASSWORD {}").format(
                role_identifier, password_literal
            )
        )
    else:
        connection.execute(
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                role_identifier, password_literal
            )
        )

    connection.execute(
        sql.SQL(
            "ALTER ROLE {} WITH LOGIN NOINHERIT NOSUPERUSER "
            "NOCREATEDB NOCREATEROLE NOREPLICATION"
        ).format(role_identifier)
    )
    connection.execute(
        sql.SQL("ALTER ROLE {} SET default_transaction_read_only TO on").format(
            role_identifier
        )
    )
    connection.execute(
        sql.SQL("ALTER ROLE {} SET statement_timeout TO {}").format(
            role_identifier, sql.Literal(f"{timeout_ms}ms")
        )
    )
    connection.execute(
        sql.SQL("ALTER ROLE {} SET search_path TO analytics, public").format(
            role_identifier
        )
    )

    database_identifier = sql.Identifier(connection.info.dbname)
    connection.execute(
        sql.SQL("REVOKE TEMPORARY ON DATABASE {} FROM PUBLIC").format(
            database_identifier
        )
    )
    connection.execute(
        sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
            database_identifier, role_identifier
        )
    )
    connection.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
    connection.execute("REVOKE ALL PRIVILEGES ON SCHEMA analytics FROM PUBLIC")
    connection.execute(
        sql.SQL("REVOKE ALL PRIVILEGES ON SCHEMA analytics FROM {}").format(
            role_identifier
        )
    )
    connection.execute(
        sql.SQL("GRANT USAGE ON SCHEMA analytics TO {}").format(role_identifier)
    )
    connection.execute(
        sql.SQL(
            "REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics FROM {}"
        ).format(role_identifier)
    )
    connection.execute(
        sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO {}").format(
            role_identifier
        )
    )
    connection.execute(
        sql.SQL(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA analytics "
            "GRANT SELECT ON TABLES TO {}"
        ).format(role_identifier)
    )
    connection.commit()
    print(f"Prepared read-only runtime role: {runtime_role}")


def main() -> None:
    with _connect() as connection:
        _ensure_change_history(connection)
        _apply_sql_directory(
            connection, PROJECT_ROOT / "db" / "migrations", "migration"
        )
        _apply_sql_directory(
            connection, PROJECT_ROOT / "data" / "seeds", "seed"
        )
        _ensure_readonly_role(connection)


if __name__ == "__main__":
    main()
