import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS user_models (
                    user_id INTEGER PRIMARY KEY,
                    default_model TEXT NOT NULL
                )
            """
            )

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()

    def get_user_model(self, user_id: int) -> str:
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT default_model FROM user_models WHERE user_id=?", (user_id,)
            )
            result = c.fetchone()
            return result[0] if result else "qwen2.5"

    def set_user_model(self, user_id: int, model: str) -> None:
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO user_models (user_id, default_model) VALUES (?, ?)",
                (user_id, model),
            )

    def add_to_history(self, user_id: int, role: str, content: str) -> None:
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content),
            )

    def get_chat_history(self, user_id: int, limit: int = 10) -> List[Dict[str, str]]:
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT role, content FROM chat_history 
                WHERE user_id=? AND timestamp >= datetime('now', '-30 minutes')
                ORDER BY timestamp ASC LIMIT ?
            """,
                (user_id, limit),
            )
            return [
                {"role": role, "content": content} for role, content in c.fetchall()
            ]

    def reset_chat_history(self, user_id: int) -> None:
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))

    def cleanup_old_history(self) -> None:
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(
                "DELETE FROM chat_history WHERE timestamp < datetime('now', '-30 minutes')"
            )


db = Database("user_data.db")
