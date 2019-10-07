import json
import time
import pprint
import telepot
import requests
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def fetch_conf():
    """
    Parses the configuration file to fetch the bot's token
    :return: token as string from telegram bot application
    """
    with open('conf.json') as json_data_file:
        data = json.load(json_data_file)
    return data["bot_token"]


if __name__ == '__main__':
    bot_token = fetch_conf()
    bot = telepot.Bot(bot_token)

    print('Listening ...')
    while True:
        time.sleep(1)