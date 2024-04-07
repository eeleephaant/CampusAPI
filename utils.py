import base64
import hashlib
import os
import re
import string
from datetime import datetime
import random
import dbmanager

from icecream import ic

import settings

logging_enabled = True


class CryptUtils:
    @classmethod
    def get_hash_512(cls, text: str):
        return hashlib.sha512(text.encode('utf-8')).hexdigest()

    @classmethod
    def image_to_base64(cls, relative_image_path: str):
        with open(relative_image_path, 'rb') as image:
            return f"data:image/jpeg;base64,{base64.b64encode(image.read()).decode('utf-8')}"


def generate_api_key():
    prefix = "campus_"
    key_main = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
    while dbmanager.api_key_exists(prefix + key_main) is True:
        key_main = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
    return prefix + key_main


class OpStatus:
    def __init__(self, message: str, status: bool):
        """
        Создаёт статус операции, который автоматически выводит сообщение в консоль
        :param message: Подробности о статусе операции
        :param status: Успешность операции
        """
        self.message = message
        self.status = status
        now = datetime.now()
        self.formatted_message = f"[{now.strftime('%d/%m/%Y %H:%M:%S')}] | {'''Success''' if self.status else '''Error'''} operation!\n Message: {self.message}"
        global logging_enabled
        if logging_enabled:
            self.__create_log()
        ic(self.formatted_message)

    def __create_log(self):
        now = datetime.now()
        current_log_file = now.strftime('%d.%m.%Y') + ".log"
        if os.path.exists(settings.get_logs_dir() + "/" + current_log_file):
            with open(settings.get_logs_dir() + "/" + current_log_file, 'a') as log:
                log.write(self.formatted_message + '\n')
        else:
            with open(settings.get_logs_dir() + "/" + current_log_file, "w") as log:
                log.write(self.formatted_message + '\n')

    def is_success(self):
        return self.status


def email_is_valid(email: str) -> bool:
    pat = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if re.match(pat, email):
        return True
    else:
        return False
