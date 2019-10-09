import json
import pprint
import telepot
from nasa import earth
from typing import NamedTuple, Any
from tqdm import tqdm
import pendulum
import os


os.environ.setdefault(
    'NASA_API_KEY',
    'xkPcYAoU93O1PeqPrKXyjpGChT1FkQ8TjA7Neg7V',
)


DATA = None  # Storage of shots to access them easily


class Bound:
    """
    Represents the value of the array as interval
    """
    def __init__(self, sub_bound, sup_bound):
        self._sub_bound = sub_bound
        self._sup_bound = sup_bound

    @property
    def sub_bound(self):
        return self._sub_bound

    @property
    def sup_bound(self):
        return self._sup_bound

    def set_sub(self, value):
        self._sub_bound = value

    def set_sup(self, value):
        self._sup_bound = value


class Shot(NamedTuple):
    """
    Represents a shot from Landsat. The asset is the output of the listing
    and the image contains details about the actual image.
    """

    asset: Any
    image: Any


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


def update_bounds(value):

    """
    Update the bounds according to the user input
    :param value: boolean as user input Yes/No
    :return: integer, boolean as the new mid value and if the bisection process can't go further
    """

    global DATA
    mid, end = None, False

    print(f'SUB_BOUND: {bound.sub_bound}')
    print(f'SUP_BOUND: {bound.sup_bound}')

    right = bound.sup_bound - 1

    if bound.sub_bound + 1 < right:
        mid = int((bound.sub_bound + right) / 2)

        print(f'mid: {mid}')

        if value:
            bound.set_sup(mid)
        else:
            bound.set_sub(mid)
    else:
        end = True

    print(f'NEW SUB_BOUND: {bound.sub_bound}')
    print(f'NEW SUP_BOUND: {bound.sup_bound}')

    return mid, end


def handle(msg):

    """
    Check the input of the user to redirect it in the correct way
    :param msg: input from the user
    :return: string as message to display to the user with some customization
    """

    global DATA

    content_type, chat_type, chat_id = telepot.glance(msg)
    print(f'Content type: {content_type} || chat type: {chat_type} || chat id: {chat_id}')

    if content_type == 'text':

        user_input = msg.get("text").lower()  # transform message input to non case sensitive input

        if user_input == '/start':

            mid = int((bound.sub_bound + bound.sup_bound) / 2)
            message = '? ' + DATA[mid].asset.date + ' - do you see it ? '
            bot.sendMessage(chat_id, DATA[mid].image.url)
            bot.sendMessage(chat_id, message)

        elif user_input == 'yes':

            mid, end = update_bounds(value=True)
            if end:
                message = 'Potential date of starting => ' + DATA[bound.sub_bound].asset.date
                bot.sendMessage(chat_id, message)
            else:
                message = '? ' + DATA[mid].asset.date + ' - do you see it ? '
                bot.sendMessage(chat_id, DATA[mid].image.url)
                bot.sendMessage(chat_id, message)

        elif user_input == 'no':

            mid, end = update_bounds(value=False)
            if end:
                message = 'Potential date of starting => ' + DATA[bound.sub_bound].asset.date
                bot.sendMessage(chat_id, message)
            else:
                message = '? ' + DATA[mid].asset.date + ' - do you see it ? '
                bot.sendMessage(chat_id, DATA[mid].image.url)
                bot.sendMessage(chat_id, message)

    else:
        raise ValueError('Nothing except text is allowed for now !')


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

    bisector = LandsatBisector(LON, LAT)
    DATA = bisector.shots

    bound = Bound(0, len(DATA))  # Instantiate class to update the bisection process

    bot.message_loop(handle, run_forever=True)

