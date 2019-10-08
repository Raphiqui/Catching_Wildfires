import json
import time
import random
import pprint
import telepot
import requests
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from nasa import earth
from typing import NamedTuple, Any
from tqdm import tqdm
from PyInquirer import prompt
import pendulum
import os


os.environ.setdefault(
    'NASA_API_KEY',
    'xkPcYAoU93O1PeqPrKXyjpGChT1FkQ8TjA7Neg7V',
)


DATA = None
SUB_BOUND = None
SUP_BOUND = None


class Size(NamedTuple):
    """
    Represents a size
    """

    width: int
    height: int


class Bound:

    def __init__(self):
        self._sub_bound = None
        self._sup_bound = None

    @property
    def sub_bound(self):
        return self.sub_bound

    @property
    def sup_bound(self):
        return self.sup_bound

    @sub_bound.setter
    def sub_bound(self, value):
        self._sub_bound = value

    @sup_bound.setter
    def sup_bound(self, value):
        self._sup_bound = value


class Color(NamedTuple):
    """
    8-bit components of a color
    """

    r: int
    g: int
    b: int


class Shot(NamedTuple):
    """
    Represents a shot from Landsat. The asset is the output of the listing
    and the image contains details about the actual image.
    """

    asset: Any
    image: Any


DISPLAY_SIZE = Size(512, 512)
BLACK = Color(0, 0, 0)
MAX_CLOUD_SCORE = 0.5

LON = -120.70418
LAT = 38.32974


class LandsatImage:
    """
    Utility class to manage the display of a landsat image using
    pygame.
    """

    def __init__(self):
        self.image = None
        self._shot = None

    @property
    def shot(self):
        return self._shot

    @shot.setter
    def shot(self, value):
        self._shot = value
        self.image = None


class LandsatBisector:
    """
    Manages the different assets from landsat to facilitate the bisection
    algorithm.
    """

    def __init__(self, lon, lat):
        self.lon, self.lat = lon, lat
        self.shots = self.get_shots()
        self.image = LandsatImage()
        self.index = 0

        print(f'First = {self.shots[0].asset.date}')
        print(f'Last = {self.shots[-1].asset.date}')
        print(f'Count = {len(self.shots)}')

    @property
    def count(self):
        return len(self.shots)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        self.image.shot = self.shots[index]
        self._index = index

    @property
    def date(self):
        return self.shots[self.index].asset.date

    def get_shots(self):
        """
        Not all returned assets are useful (some have clouds). This function
        does some filtering in order to remove those useless assets and returns
        pre-computed shots which can be used more easily.
        """

        begin = '2000-01-01'
        end = pendulum.now('UTC').date().isoformat()

        assets = earth.assets(lat=self.lat, lon=self.lon, begin=begin, end=end)

        out = []

        for asset in tqdm(assets):
            img = asset.get_asset_image(cloud_score=True)
            if (img.cloud_score or 1.0) <= MAX_CLOUD_SCORE:
                out.append(Shot(asset, img))

        return out


def setup_bounds():
    global SUB_BOUND, SUP_BOUND, DATA

    SUB_BOUND = 0
    SUP_BOUND = len(DATA)
    mid = int((SUB_BOUND + SUP_BOUND) / 2)

    print(f'SUB_BOUND: {SUB_BOUND}')
    print(f'SUP_BOUND: {SUP_BOUND}')
    print(f'mid: {mid}')

    return mid


def bob(value):
    global SUB_BOUND, SUP_BOUND, DATA
    mid, left, right, end = None, None, None, False
    print(value)
    print(f'SUB_BOUND: {SUB_BOUND}')
    print(f'SUP_BOUND: {SUP_BOUND}')

    if SUB_BOUND + 1 < SUP_BOUND:
        mid = int((SUB_BOUND + SUP_BOUND) / 2)

        print(f'mid: {mid}')

        if value:
            SUP_BOUND = mid
        else:
            SUB_BOUND = mid
    else:
        end = True

    print(f'NEW SUB_BOUND: {SUB_BOUND}')
    print(f'NEW SUP_BOUND: {SUP_BOUND}')

    return mid, end


def handle(msg):
    global SUB_BOUND, SUP_BOUND

    content_type, chat_type, chat_id = telepot.glance(msg)
    print(f'Content type: {content_type} || chat type: {chat_type} || chat id: {chat_id}')

    if content_type == 'text':
        msg.get("text").lower()

        if msg['text'] == '/start':

            mid = setup_bounds()
            message = '? ' + DATA[mid].asset.date + ' - do you see it ? '
            bot.sendMessage(chat_id, DATA[mid].image.url)
            bot.sendMessage(chat_id, message)

        elif msg['text'] == 'yes':

            mid, end = bob(value=True)
            if end:
                message = 'Potential date of starting => ' + DATA[SUB_BOUND].asset.date
                bot.sendMessage(chat_id, message)
            else:
                message = '? ' + DATA[mid].asset.date + ' - do you see it ? '
                bot.sendMessage(chat_id, DATA[mid].image.url)
                bot.sendMessage(chat_id, message)

        elif msg['text'] == 'no':

            mid, end = bob(value=False)
            if end:
                message = 'Potential date of starting => ' + DATA[SUB_BOUND].asset.date
                bot.sendMessage(chat_id, message)
            else:
                message = '? ' + DATA[mid].asset.date + ' - do you see it ? '
                bot.sendMessage(chat_id, DATA[mid].image.url)
                bot.sendMessage(chat_id, message)

    else:
        raise ValueError('Nothing except text is allowed for now !')


def main(bot):
    global DATA

    bisector = LandsatBisector(LON, LAT)
    DATA = bisector.shots

    bot.message_loop(handle, run_forever=True)


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

    main(bot)
