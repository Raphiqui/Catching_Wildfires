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
import pygame
import os


os.environ.setdefault(
    'NASA_API_KEY',
    'xkPcYAoU93O1PeqPrKXyjpGChT1FkQ8TjA7Neg7V',
)


DATA = None


class Size(NamedTuple):
    """
    Represents a size
    """

    width: int
    height: int


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


def bisect(n, mapper, tester):
    """
    Runs a bisection.

    - `n` is the number of elements to be bisected
    - `mapper` is a callable that will transform an integer from "0" to "n"
      into a value that can be tested
    - `tester` returns true if the value is within the "right" range
    """

    if n < 1:
        raise ValueError('Cannot bissect an empty array')

    left = 0
    right = n - 1

    while left + 1 < right:
        mid = int((left + right) / 2)

        val = mapper(mid)

        if tester(val):
            right = mid
        else:
            left = mid

    return mapper(right)


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

    # def blit(self, disp):
    #     if not self.image:
    #         img = self.shot.image
    #         pil_img = img.image
    #         buf = pil_img.tobytes()
    #         size = pil_img.width, pil_img.height
    #         self.image = pygame.image.frombuffer(buf, size, 'RGB')
    #
    #     disp.blit(self.image, (0, 0))


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

        # data = {}
        # data['shots'] = []

        out = []

        for asset in tqdm(assets):
            img = asset.get_asset_image(cloud_score=True)
            if (img.cloud_score or 1.0) <= MAX_CLOUD_SCORE:
                out.append(Shot(asset, img))
                # data['shots'].append({
                #     'date': asset.date,
                #     'id': asset.id,
                #     'url': img.url
                # })
                # with open('data.json', 'w') as outfile:
                #     json.dump(data, outfile, indent=4)

        # print(f'Length of array: {len(out)}')

        return out

    # def blit(self, disp):
    #     """
    #     Draws the current picture.
    #     """
    #
    #     self.image.blit(disp)


def confirm(title):
    """
    Asks a yes/no question to the user
    """

    return prompt([{
        'type': 'confirm',
        'name': 'confirm',
        'message': f'{title} - do you see it?',
    }])['confirm']


# class RandomAsset:
#
#     def __init__(self):
#         self.asset = self.get_random_asset()
#
#     @property
#     def asset(self):
#         return self.asset
#
#     @asset.setter
#     def asset(self, value):
#         self.asset = value
#
#     def get_random_asset(self):
#
        # random_value = random.randint(0, len(DATA) - 1)
        # print(f'Random value: {random_value}')
        # test = DATA[random_value]
#         return test


def handle(msg):
    """
    Check the input of the user to redirect it in the correct part of the game
    :param msg: input from the user
    :return: string ad message to display to the user with some customization
    """
    # Receive message and pass the command to call the corresponding func

    content_type, chat_type, chat_id = telepot.glance(msg)
    print(f'Content type: {content_type} || chat type: {chat_type} || chat id: {chat_id}')
    # you can add more content type, like if someone send a picture
    if content_type == 'text':
        if msg['text'] == '/start':
            random_value = random.randint(0, len(DATA) - 1)
            print(f'Random value: {random_value}')
            test = DATA[random_value]
            pprint.pprint(test)
            message = '? ' + test.asset.date + ' - do you see it ? '
            bot.sendMessage(chat_id, test.image.url)
            bot.sendMessage(chat_id, message)
    else:
        raise ValueError('Nothing except text is allowed for now !')


def main(bot):
    global DATA
    """
    Runs a bisection algorithm on a series of Landsat pictures in order
    for the user to find the approximate date of the fire.

    Images are displayed using pygame, but the interactivity happens in
    the terminal as it is much easier to do.
    """

    # pygame.init()

    bisector = LandsatBisector(LON, LAT)
    DATA = bisector.shots

    # disp = pygame.display.set_mode(DISPLAY_SIZE)

    bot.message_loop(handle, run_forever=True)

    def mapper(n):
        """
        In that case there is no need to map (or rather, the mapping
        is done visually by the user)
        """

        return n

    def tester(n):
        """
        Displays the current candidate to the user and asks them to
        check if they see wildfire damages.
        """

        bisector.index = n
        disp.fill(BLACK)
        bisector.blit(disp)
        # pygame.display.update()

        return confirm(bisector.date)

    # culprit = bisect(bisector.count, mapper, tester)
    # bisector.index = culprit
    #
    # print(f"Found! First apparition = {bisector.date}")
    #
    # pygame.quit()
    # exit()


def fetch_conf():
    """
    Parses the configuration file to fetch the bot's token
    :return: token as string from telegram bot application
    """
    with open('conf.json') as json_data_file:
        data = json.load(json_data_file)
    return data["bot_token"]


# def fetch_assets():
#     with open('data.json') as json_data_file:
#         data = json.load(json_data_file)
#     return data["shots"]


if __name__ == '__main__':
    bot_token = fetch_conf()
    bot = telepot.Bot(bot_token)

    # DATA = fetch_assets()
    # pprint.pprint(len(DATA))

    main(bot)