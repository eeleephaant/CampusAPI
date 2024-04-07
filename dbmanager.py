import sqlite3

import settings
import utils


def account_exists(email: str) -> bool:
    """
    Check if an account with the given email exists.
    """
    with sqlite3.connect(settings.get_main_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        return result is not None


def api_key_exists(api_key_raw: str) -> bool:
    with sqlite3.connect(settings.get_main_db_path()) as conn:
        cursor = conn.cursor()
        hashed_key = utils.CryptUtils.get_hash_512(api_key_raw)
        cursor.execute("SELECT * FROM user_api_keys WHERE api_key = ?", (hashed_key,))
        result = cursor.fetchone()
        return result is not None


def get_user_id_from_api_key(api_key_raw: str) -> int | None:
    """
    Returns the user ID associated with the given API key.
    """
    with sqlite3.connect(settings.get_main_db_path()) as conn:
        cursor = conn.cursor()
        hashed_key = utils.CryptUtils.get_hash_512(api_key_raw)
        cursor.execute("SELECT user_id FROM user_api_keys WHERE api_key = ?", (hashed_key,))
        result = cursor.fetchone()
        return result[0]


def is_new_ip_for_user(ip_address: str, user_id: int) -> bool:
    """
    Returns whether or not the given IP address is associated with the given user ID.
    """
    with sqlite3.connect(settings.get_main_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_api_keys WHERE ip_address = ? AND user_id = ?", (ip_address, user_id))
        result = cursor.fetchone()
        return result is None


def generate_dummy_indicators():
    with sqlite3.connect(settings.get_main_db_path()) as conn:
        cursor = conn.cursor()
        for i in range(50):
            ind_type = 1
            if i % 2 == 0:
                ind_type = 0
            cursor.execute(
                "INSERT INTO indicators (id, type, name) VALUES (?, ?, ?)",
                (i, ind_type, f"Индикатор {i}",)
            )
        conn.commit()
