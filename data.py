import json
import sqlite3
from typing import Union

import dbmanager
import settings

import utils


class RolesManager:
    """
    A class for managing roles from the database.

    Attributes:
        roles (dict): A dictionary containing role IDs as keys and their corresponding names as values.
    """

    def __init__(self):
        self.roles = self.__load_roles_from_bd()

    def __load_roles_from_bd(self) -> dict:
        roles: dict = {}
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM roles")
            result = cursor.fetchall()
            for role in result:
                roles[role[0]] = role[1]
            return roles

    def validate_role(self, role_name: str) -> bool:
        return role_name in self.roles

    def get_role_by_id(self, id: int) -> str:
        return self.roles[id]


class Competence:
    def __init__(self, name: str, id: int):
        self.comp_id = id
        self.name = name


class CompetenciesManager:
    def __init__(self):
        self.competencies = self.__load_competencies_from_bd()

    def get_name_by_id(self, id: int) -> str:
        return self.competencies[id]

    def __load_competencies_from_bd(self) -> dict:
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM competencies")
            competencies = {}
            result = cursor.fetchall()
            for comp in result:
                competencies[comp[0]] = comp[1]
            return competencies


class CampusAccount:
    def __init__(self, user_id: int, first_name: str, second_name: str, third_name: str, email: str, university_id: int,
                 role_id: int):
        self.comp_manager = CompetenciesManager()
        self.user_id = user_id
        self.first_name = first_name
        self.second_name = second_name
        self.third_name = third_name
        self.email = email
        self.university_id = university_id
        self.role_id = role_id
        self.competencies = self.__get_competencies()

    def account_info_json_self(self) -> str:
        """
            Returns a JSON string containing the user's account information.
            """
        return json.dumps({
            "user_id": self.user_id,
            "first_name": self.first_name,
            "second_name": self.second_name,
            "third_name": self.third_name,
            "email": self.email,
            "university_id": self.university_id,
            "role_id": self.role_id,
            "competencies": self.competencies
        })

    def get_info_json_as(self, as_role: str) -> str:
        if as_role == "Асессор":
            return json.dumps({
                "user_id": self.user_id,
                "first_name": self.first_name,
                "second_name": self.second_name,
                "third_name": self.third_name,
                "email": self.email,
                "university_id": self.university_id,
                "role_id": self.role_id,
                "competencies": self.competencies
            })
        if as_role == "Студент":
            return json.dumps({
                "user_id": self.user_id,
                "first_name": self.first_name,
                "second_name": self.second_name,
                "third_name": self.third_name,
                "email": self.email,
                "university_id": self.university_id,
                "role_id": self.role_id
            })
        if as_role == "Организатор":
            return json.dumps({
                "user_id": self.user_id,
                "first_name": self.first_name,
                "second_name": self.second_name,
                "third_name": self.third_name,
                "email": self.email,
                "university_id": self.university_id,
                "role_id": self.role_id,
                "competencies": self.competencies
            })

    def get_role_name(self) -> str:
        return RolesManager().get_role_by_id(self.role_id)

    @classmethod
    def get_by_id(cls, user_id: int) -> Union["CampusAccount", None]:
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT firstname, secondname, thirdname, email, univercities_id, role_id FROM users WHERE id = ?",
                (user_id,))
            result = cursor.fetchone()
            if result is not None:
                first_name, second_name, third_name, email, university_id, role_id = result
                return CampusAccount(user_id, first_name, second_name, third_name, email, university_id, role_id)
            return None

    def __get_competencies(self) -> list:
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT points, competencies_id FROM user_competencies WHERE user_id = ?",
                (self.user_id,))
            result = cursor.fetchall()
            competencies = []
            for competence in result:
                competencies.append((competence[1], competence[0],))
            return competencies

    def edit(self, first_name: str = None, second_name: str = None, third_name: str = None, email: str = None,
             university: int = -999):
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()

            if first_name is not None:
                cursor.execute(
                    "UPDATE users SET firstname = ? WHERE id = ?", (first_name, self.user_id,))
            if second_name is not None:
                cursor.execute(
                    "UPDATE users SET secondname = ? WHERE id = ?", (second_name, self.user_id,))
            if third_name is not None:
                cursor.execute(
                    "UPDATE users SET thirdname = ? WHERE id = ?", (third_name, self.user_id,))
            if email is not None:
                cursor.execute(
                    "UPDATE users SET email = ? WHERE id = ?", (email, self.user_id,))
            if university != -999 and university <= 5:
                cursor.execute(
                    "UPDATE users SET univercities_id = ? WHERE id = ?", (university, self.user_id,))
            conn.commit()

    @classmethod
    def get_from_api_key(cls, api_key: str) -> Union["CampusAccount", None]:
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            user_id = dbmanager.get_user_id_from_api_key(api_key)
            if user_id is not None:
                cursor.execute(
                    "SELECT firstname, secondname, thirdname, email, univercities_id, role_id FROM users WHERE id = ?",
                    (user_id,))
                result = cursor.fetchone()
                if result is not None:
                    first_name, second_name, third_name, email, university_id, role_id = result
                    return CampusAccount(user_id, first_name, second_name, third_name, email, university_id, role_id)
                return None
            return None

    @classmethod
    def get_from_credentials(cls, email: str, password_raw: str) -> Union["CampusAccount", None]:
        """
        Returns a CampusAccount object for the given login and password.
        """
        password_hashed = utils.CryptUtils.get_hash_512(password_raw)
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM users WHERE email = ? AND password = ?", (email, password_hashed))
            result = cursor.fetchone()
            if result is not None:
                user_id = result[0]
                return CampusAccount.get_by_id(user_id)
            else:
                return None

    def create_new_api_key(self, useragent: str, ip: str) -> str:
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            api_key_raw = utils.generate_api_key()
            api_key_hashed = utils.CryptUtils.get_hash_512(api_key_raw)

            cursor.execute(
                "INSERT INTO user_api_keys (api_key, user_id, ip_address, last_useragent, last_access) VALUES (?,?,?,?,CURRENT_TIMESTAMP)",
                (str(api_key_hashed), int(self.user_id), str(ip), str(useragent)))
            return api_key_raw

    def get_account_competencies(self) -> list[Competence]:
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ")

    def get_sessions(self) -> dict:
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, ip_address, last_useragent, last_access, created_at FROM user_api_keys WHERE user_id = ?",
                (self.user_id,))
            result = cursor.fetchall()
            if result is not None:
                pass

    @classmethod
    def register(cls, first_name: str, last_name: str, third_name: str, email: str, password_raw: str,
                 university: int, ip_addr: str, user_agent: str) -> str | utils.OpStatus:
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            try:
                if university > 5:
                    return utils.OpStatus("University index invalid", False)

                password_hashed = utils.CryptUtils.get_hash_512(password_raw)

                cursor.execute(
                    "INSERT INTO users (firstname, secondname, thirdname, email, password, univercities_id, role_id) VALUES (?,?,?,?,?,?,?)",
                    (first_name, last_name, third_name, email, password_hashed, university, 1))

                conn.commit()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                user_id = cursor.fetchone()[0]

                api_key_raw = utils.generate_api_key()
                api_key_hashed = utils.CryptUtils.get_hash_512(api_key_raw)

                cursor.execute(
                    "INSERT INTO user_api_keys (api_key, user_id, ip_address, last_useragent, last_access) VALUES (?,?,?,?,CURRENT_TIMESTAMP)",
                    (str(api_key_hashed), int(user_id), str(ip_addr), str(user_agent)))

                conn.commit()

                return api_key_raw
            except sqlite3.DatabaseError as e:
                return utils.OpStatus(f"Error with db {e.sqlite_errorname}", False)

    @classmethod
    def login(cls, email: str, password_raw: str, ip_address: str, user_agent: str) -> str | utils.OpStatus:
        account = cls.get_from_credentials(email, password_raw)
        if account is not None:
            return account.create_new_api_key(user_agent, ip_address)
        else:
            return utils.OpStatus("Invalid credentials", False)
