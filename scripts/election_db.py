#!/usr/bin/env python3
"""Shared MySQL helpers for election data scripts."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import mysql.connector
from mysql.connector import MySQLConnection


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"


def _parse_env_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    if "=" in line:
        key, value = line.split("=", 1)
    elif ":" in line:
        key, value = line.split(":", 1)
    else:
        return None

    return key.strip(), value.strip().strip("\"'")


def load_db_config(env_path: Path = ENV_PATH) -> dict[str, Any]:
    config: dict[str, Any] = {
        "host": os.environ.get("DB_HOST") or os.environ.get("MYSQL_HOST"),
        "port": os.environ.get("DB_PORT") or os.environ.get("MYSQL_PORT") or "3306",
        "user": os.environ.get("DB_USER") or os.environ.get("MYSQL_USER"),
        "password": os.environ.get("DB_PASSWORD") or os.environ.get("MYSQL_PASSWORD") or "",
        "database": os.environ.get("DB_NAME") or os.environ.get("MYSQL_DATABASE"),
    }

    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            parsed = _parse_env_line(raw_line)
            if parsed is None:
                continue
            key, value = parsed
            match key:
                case "DB_HOST" | "MYSQL_HOST" | "host":
                    config["host"] = value
                case "DB_PORT" | "MYSQL_PORT" | "port":
                    config["port"] = value
                case "DB_USER" | "MYSQL_USER" | "user":
                    config["user"] = value
                case "DB_PASSWORD" | "MYSQL_PASSWORD" | "pass" | "password":
                    config["password"] = value
                case "DB_NAME" | "MYSQL_DATABASE" | "database" | "db":
                    config["database"] = value

    missing = [key for key in ("host", "user", "database") if not config.get(key)]
    if missing:
        raise RuntimeError(f"Missing database config values: {', '.join(missing)}")

    config["port"] = int(config["port"])
    return config


def connect() -> MySQLConnection:
    return mysql.connector.connect(**load_db_config(), autocommit=False)


def fetch_one_id(cursor: Any, query: str, params: tuple[Any, ...]) -> int | None:
    cursor.execute(query, params)
    row = cursor.fetchone()
    return int(row[0]) if row else None

