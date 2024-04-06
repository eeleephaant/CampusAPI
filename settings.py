import json
import os

from icecream import ic

settings_file = "./settings.json"


def get_main_db_path() -> str:
    with open(settings_file, 'r') as file:
        db = json.load(file)["paths"]["main_db"]
        return db


def get_logs_dir() -> str:
    with open(settings_file, 'r') as file:
        return json.load(file)["paths"]["logs_dir"]


def get_images_dir() -> str:
    with open(settings_file, 'r') as file:
        return json.load(file)["paths"]["images_dir"]
