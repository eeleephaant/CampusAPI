import json
import sqlite3
from datetime import datetime
from time import strptime
from typing import Union

import dbmanager
import settings

import utils


class University:
    def __init__(self, name: str, university_id: int):
        self.name = name
        self.university_id = university_id


class UniversityManager:

    @classmethod
    def get_all_universities_as_json(cls) -> str:
        """
        Returns a JSON string containing all universities from the database.
        """
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, id FROM univercities")
            result = cursor.fetchall()
            return json.dumps(
                [{"name": name, "university_id": university_id} for name, university_id in result])


class Indicator:
    def __init__(self, name: str, indicator_id: int, type: bool):
        self.name = name
        self.indicator_id = indicator_id
        self.type = type

    @classmethod
    def get_by_id(cls, indicator_id: int) -> Union["Indicator", None]:
        """
        Returns the indicator with the given ID.
        """
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, type FROM indicators WHERE id = ?", (indicator_id,))
            result = cursor.fetchone()
            if result is None:
                return None
            return cls(result[0], indicator_id, bool(result[1]))


class IndicatorsManager:
    def __init__(self, indicators: list):
        self.indicators = indicators

    @classmethod
    def get_all_indicators_as_json(cls) -> str:
        """
        Returns a JSON string containing all indicators from the database.
        """
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, indicator_id, type FROM indicators")
            result = cursor.fetchall()
            return json.dumps(
                [{"name": name, "indicator_id": indicator_id, "type": bool(ind_type)} for name, indicator_id, ind_type
                 in result])


class Event:
    """
    A class for getting events.

    Attributes:
        event_id (int): The unique identifier of the event.
        date (datetime): The date and time of the event.
        name (str): The name of the event.
        address (str): The address of the event.
        description (str): A description of the event.
        organizer_id (int): The unique identifier of the event organizer.
        verified (int): A flag indicating whether the event has been verified.
        relative_image_path (str): The relative path to the image representing the event.
    """

    def __init__(self, name: str, event_id: int, organizer_id: int, verified: int, date: datetime, address: str,
                 description: str, indicators: list[Indicator]):
        self.event_id = event_id
        self.date = date
        self.name = name
        self.address = address
        self.description = description
        self.organizer_id = organizer_id
        self.verified = verified
        self.relative_image_path = self.__get_relative_picture_path()
        self.indicators = indicators

    def get_json_info(self) -> str:
        return json.dumps({
            "event_id": self.event_id,
            "date": self.date.strftime("%Y-%m-%d %H:%M:%S"),
            "name": self.name,
            "address": self.address,
            "description": self.description,
            "organizer_id": self.organizer_id,
            "verified": self.verified,
            "indicators": [{"indicator_id": indicator.indicator_id, "name": indicator.name} for indicator in
                           self.indicators],
            "preview_picture": utils.CryptUtils.image_to_base64(self.relative_image_path)
        })

    def __get_relative_picture_path(self) -> str | None:
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT path_to_picture FROM events_pictures WHERE event_id =?",
                (self.event_id,))
            result = cursor.fetchone()
            return result[0]

    @classmethod
    def get_by_id(cls, event_id: int) -> Union["Event", None]:
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT organizer_id, verified, date, address, name, description FROM events WHERE id = ?",
                (event_id,))
            result = cursor.fetchone()
            if result is None:
                return None
            organizer_id, verified, date, address, name, description = result
            return cls(name, event_id, organizer_id, verified, strptime(date, "%Y-%m-%d %H:%M:%S"), address,
                       description)


class EventsManager:

    @classmethod
    def get_event_list_as_json(cls) -> str:
        """
        Retrieves a list of events from the database and returns a JSON string with the list of events,
        containing only the necessary attributes.

        Returns:
        - str: A JSON string containing a list of events with only the necessary attributes.

        Raises:
        - sqlite3.DatabaseError: If there is an error with the database.
        """
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, organizer_id, verified, date, address, name, description FROM events")
            result = cursor.fetchall()
            return json.dumps([{"event_id": event_id, "organizer_id": organizer_id, "verified": verified,
                                "date": date.strftime("%Y-%m-%d %H:%M:%S"), "address": address,
                                "name": name, "description": description} for
                               event_id, organizer_id, verified, date, address, name, description in result])

    @classmethod
    def verify_event(cls, event_id: int):
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE events SET verified = 1 WHERE id = ?", (event_id,))
            conn.commit()

    @classmethod
    def edit_event(cls, event_id: int, name: str = None, description: str = None, date: datetime = None,
                   address: str = None,
                   relative_pic_path: str = None,
                   indicators: list[Indicator] = None
                   ):
        """
        Edits an event in the database.

        Parameters:
        - event_id (int): The ID of the event to be edited.
        - name (str): The new name of the event. If not provided, the current name will remain unchanged.
        - description (str): The new description of the event. If not provided, the current description will remain unchanged.
        - date (datetime): The new date and time of the event. If not provided, the current date and time will remain unchanged.
        - address (str): The new address of the event location. If not provided, the current address will remain unchanged.
        - relative_pic_path (str): The new relative path of the event's picture. If not provided, the current relative path will remain unchanged.

        Returns:
        - None: This method does not return any value.

        Raises:
        - sqlite3.DatabaseError: If there is an error with the database.
        """
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            if name is not None:
                cursor.execute("UPDATE events SET name = ? WHERE id = ?", (name, event_id))
            if description is not None:
                cursor.execute("UPDATE events SET description = ? WHERE id = ?", (description, event_id))
            if date is not None:
                cursor.execute("UPDATE events SET date = ? WHERE id = ?",
                               (date.strftime("%Y-%m-%d %H:%M:%S"), event_id))
            if address is not None:
                cursor.execute("UPDATE events SET address = ? WHERE id = ?", (address, event_id))
            if relative_pic_path is not None:
                cursor.execute("UPDATE events_pictures SET path_to_picture = ? WHERE event_id = ?",
                               (relative_pic_path, event_id))
            if indicators is not None:
                cursor.execute("DELETE FROM indicators_events WHERE event_id =?", (event_id,))
                for indicator in indicators:
                    cursor.execute("INSERT INTO indicators_events (indicator_id, event_id) VALUES (?,?)",
                                   (indicator.indicator_id, event_id))

            conn.commit()

    @classmethod
    def add_event(cls, name: str, description: str, date: datetime, address: str, relative_pic_path: str,
                  organizer_id: int) -> int:
        """
        Adds a new event to the database.

        Parameters:
        - name (str): The name of the event.
        - description (str): A brief description of the event.
        - date (datetime): The date and time of the event.
        - address (str): The address of the event location.
        - relative_pic_path (str): The relative path to the picture representing the event.

        Returns:
        - int: The ID of the newly added event.

        Raises:
        - sqlite3.DatabaseError: If there is an error with the database.
        """
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO events (name, description, date, address, verified, organizer_id) VALUES (?,?,?,?,0,?)",
                (name, description, date.strftime("%Y-%m-%d %H:%M:%S"), address, organizer_id))

            conn.commit()

            cursor.execute(
                "SELECT id FROM events WHERE name = ? AND description =? AND date =? AND address =?",
                (name, description, date.strftime("%Y-%m-%d %H:%M:%S"), address, relative_pic_path))
            result = cursor.fetchone()

            cursor.execute("INSERT INTO events_pictures (id, path_to_picture, event_id) VALUES (?, ?)",
                           (result[0], relative_pic_path, result[0],))
            conn.commit()
            return result[0]


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

    def get_suggested_events(self) -> list[Event]:
        """
            Returns a list of suggested events for the user.
        """
        events = []
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM events WHERE verified = 1", (self.user_id,))
            list_of_verified_events_id = cursor.fetchall()
            indicators = self.get_indicators()

            for event_id in list_of_verified_events_id:
                event_id = event_id[0]
                for indicator in indicators:
                    cursor.execute("SELECT * FROM events_indicators WHERE event_id = ? AND indicator_id = ?",
                                   (event_id, indicator.indicator_id,))
                    result = cursor.fetchone()
                    if result is not None:
                        events.append(Event.get_by_id(event_id))
        return events

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

    def __reset_preferences_competence(self):
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_preferences_competencies WHERE user_id = ?", (self.user_id,))
            conn.commit()

    def __reset_indicators(self):
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_indicators WHERE user_id = ?", (self.user_id,))
            conn.commit()

    def set_indicators(self, indicators: list[Indicator]):
        self.__reset_indicators()
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            for ind in indicators:
                cursor.execute(
                    "INSERT INTO user_indicators (indicator_id, user_id) VALUES (?,?)",
                    (ind.indicator_id, self.user_id,)
                )
            conn.commit()

    def get_indicators(self) -> list[Indicator]:
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT indicator_id FROM user_indicators WHERE user_id = ?",
                (self.user_id,))
            result = cursor.fetchall()
            indicators = []
            for ind in result:
                indicators.append(Indicator.get_by_id(ind[0]))
            return indicators

    def set_preference_competencies(self, comp_list: list[Competence]):
        self.__reset_preferences_competence()
        with sqlite3.connect(settings.get_main_db_path()) as conn:
            cursor = conn.cursor()
            for comp in comp_list:
                cursor.execute(
                    "INSERT INTO user_preferences_competencies (competence_id, user_id) VALUES (?,?)",
                    (comp.comp_id, self.user_id,)
                )
            conn.commit()

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
