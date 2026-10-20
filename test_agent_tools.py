
import sqlite3

import agent_tools


def test_get_ticket_returns_ticket_by_id(tmp_path, monkeypatch):
    test_db = tmp_path / "test_support.db"

    with sqlite3.connect(test_db) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute(
            """
            CREATE TABLE tickets (
                id INTEGER PRIMARY KEY,
                customer_name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO tickets
                (id, customer_name, email, subject, description, priority, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                "Test Customer",
                "test@example.com",
                "Cannot log in",
                "I forgot my password.",
                "high",
                "open",
            ),
        )

    def get_test_connection():
        connection = sqlite3.connect(test_db)
        connection.row_factory = sqlite3.Row
        return connection

    monkeypatch.setattr(
        agent_tools,
        "get_connection",
        get_test_connection,
    )

    ticket = agent_tools.get_ticket(1)

    assert ticket is not None
    assert ticket["id"] == 1
    assert ticket["subject"] == "Cannot log in"
    assert ticket["status"] == "open"


def test_get_ticket_returns_none_for_missing_ticket(tmp_path, monkeypatch):
    test_db = tmp_path / "test_support.db"

    with sqlite3.connect(test_db) as connection:
        connection.execute(
            """
            CREATE TABLE tickets (
                id INTEGER PRIMARY KEY,
                customer_name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )

    def get_test_connection():
        connection = sqlite3.connect(test_db)
        connection.row_factory = sqlite3.Row
        return connection

    monkeypatch.setattr(
        agent_tools,
        "get_connection",
        get_test_connection,
    )

    assert agent_tools.get_ticket(-999999) is None
