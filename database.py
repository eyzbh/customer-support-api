
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
