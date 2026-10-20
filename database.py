
import sqlite3

DATABASE_NAME = "support.db"


def get_connection(database_name: str = DATABASE_NAME):
    connection = sqlite3.connect(database_name)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'open'
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS approval_requests (
                request_id TEXT PRIMARY KEY,
                action TEXT NOT NULL
                    CHECK (action IN ('close_ticket', 'reopen_ticket')),
                ticket_id INTEGER NOT NULL,
                requested_by TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'rejected')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                decided_at TEXT,
                decided_by TEXT,
                executed_at TEXT,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            )
            """
        )
