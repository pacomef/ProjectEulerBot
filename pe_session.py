import traceback

import requests
from requests import TooManyRedirects

import faulthandler

from anticaptchaofficial.imagecaptcha import *

import json
import random
import re

import pe_api
import phone_api
import pe_global_objects as pe_global

from rich.console import Console
from pe_global_objects import log
import os

import asyncio

console = Console()

MAX_TRIES = 3
CAPTCHA_KEY = None
PROFILE_NAME = None
PE_USERNAME = None
PE_PASSWORD = None

PHPSESS_NAME = "__Host-PHPSESSID"


def session_setup(captcha: str, profile: str, pe_username: str, pe_password: str) -> None:

    global CAPTCHA_KEY, PROFILE_NAME, PE_USERNAME, PE_PASSWORD
    CAPTCHA_KEY = captcha
    PROFILE_NAME = profile
    PE_USERNAME = pe_username
    PE_PASSWORD = pe_password



def solve(image_name: str, human: bool = False):
    
    if human:
        return input("Human CAPTCHA: ")
    
    solver = imagecaptcha()
    solver.set_key(CAPTCHA_KEY)
    solver.set_numeric(1)
    solver.set_minLength(5)
    solver.set_maxLength(5)
    captcha_text = solver.solve_and_return_solution(image_name)

    phone_api.bot_info("Consumed a CAPTCHA token")
    
    return str(captcha_text)


def try_fetching_cookies(human: bool = False):

    url = "https://projecteuler.net/sign_in"
    captcha_url = "https://projecteuler.net/captcha/show_captcha.php"
    filename = "web_utils/current-captcha.png"

    bot_password = PE_PASSWORD or os.environ.get("BOT_KEY")
    if not bot_password:
        log.error("Missing Project Euler password, cannot fetch cookies.")
        return []

    if 'web_utils' not in os.listdir('.'):
        os.mkdir('web_utils')

    try:
        session = requests.Session()

        form = session.get(url, timeout=30)
        form.raise_for_status()
        csrf_token = re.search(
            r'name="sign_in_form".*?name="csrf_token" value="([^"]+)"', form.text, re.S
        ).group(1)

        captcha = session.get(f"{captcha_url}?{random.random()}", timeout=30)
        captcha.raise_for_status()
        with open(filename, "wb") as f:
            f.write(captcha.content)

        captcha_result = solve(filename, human)
        log.info(f"[-] Tried to guess {captcha_result} as Captcha")

        session.post(url, data={
            "csrf_token": csrf_token,
            "username": PE_USERNAME,
            "password": bot_password,
            "captcha": captcha_result,
            "remember_me": "1",
            "sign_in": "Sign In",
        }, timeout=30)

        return [{"name": c.name, "value": c.value} for c in session.cookies]

    except Exception as e:
        log.exception(e)
        return []


def refresh_tokens():

    faulthandler.enable()

    human = False

    current_tries = 0
    found_keepalive = False

    values = {PHPSESS_NAME: None, "keep_alive": None} # [PHPSESSID, keep_alive]

    while not found_keepalive and current_tries < MAX_TRIES:

        cookies = try_fetching_cookies(human)
        current_tries += 1

        log.info(f"Making try #{current_tries} to refresh cookies")

        for cookie in cookies:

            log.info(f'{cookie["name"]}, {cookie["value"]}')
            if cookie["name"] == PHPSESS_NAME:
                values[PHPSESS_NAME] = cookie["value"]

            if cookie["name"] == "keep_alive":
                found_keepalive = True
                values["keep_alive"] = cookie["value"]
    
    if values["keep_alive"] is not None:
        phone_api.bot_info("Token refreshed automatically")
        log.info(f"Token refreshed automatically {values[PHPSESS_NAME]}")
    else:
        phone_api.bot_crashed("Failed to refresh token")
        log.error("Failed to refresh token")

    with open(PROFILE_NAME, "r") as f:
        data = json.load(f)

    data["session_keys"] = values

    with open(PROFILE_NAME, "w") as f:
        json.dump(data, f, indent=4)

    pe_api.COOKIES = values
    return values




async def is_connected() -> bool:
    try:
        pe_request = await pe_api.ProjectEulerRequest.fetch("https://projecteuler.net/minimal=connected", True)
    except TooManyRedirects as exc:
        pe_api.console.log(exc, traceback.format_exc())
        log.exception(exc)
        return False
    except pe_api.EulerRequestFail:
        return False
    return PE_USERNAME in pe_request.response


async def is_website_active() -> bool:
    try:
        pe_request = await pe_api.ProjectEulerRequest.fetch("https://projecteuler.net/minimal=connected", False)
    except pe_api.EulerRequestFail as _:
        return False
    return pe_request.status == 200



if __name__ == "__main__":
    pass