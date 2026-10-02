import discord
import datetime 
import pytz

import logging
from rich.logging import RichHandler


TEST_SERVER = 943488228084813864
PROJECT_EULER_SERVER = 903915097804652595
GUILD_IDS = [PROJECT_EULER_SERVER]

BOT_APPLICATION_ID = 930813331512635413

ADMINISTRATOR_ROLE = 905683104461619261
MODERATOR_ROLE = 1103325920028266607

# Initial condition
STARTING_TIME = datetime.datetime.now(pytz.utc)

# In order to keep track of the last time the solves of members were checked
REPEATS_SINCE_START = 0
REPEATS_SUCCESSFUL_SINCE_START = 0
ROUNDS_NEEDED_TO_ANNOUNCE_RSS = 60

# Basic Discord stuff
intents = discord.Intents.all()
bot = discord.Bot(guild_ids=GUILD_IDS, intents=intents)

# Time between each check of solves, in seconds
AWAIT_TIME = 60

# Previously, the prefix that was used to make commands
PREFIX = "&"

# The IDs of the channels in which solves and achievements are announced
CHANNELS_TO_ANNOUNCE = [944372979809255483, 1002176082713256028]
MAIN_ANNOUNCEMENT_CHANNEL = 1132762771356922036
SPECIAL_CHANNELS_TO_ANNOUNCE = [944372979809255483, 1004530709760847993]
TESTING_CHANNEL_TO_ANNOUNCE = 1179793930993283144
BRAINSTORMING_CHANNEL = 1268346986810183680
SMALL_ANNOUNCEMENTS_CHANNEL = 1268526845318529034
THREADS_CHANNEL = 904251551474942002

SOLVE_ROLES = [904255861503975465, 905987654083026955, 975720598741331988, 905987783892561931, 975722082996473877, 905987999949529098, 975722386559225878, 975722571473498142, 1051483511749619722, 1351315236879073301]
PERFECTIONIST_ROLE = 1135697719319609384

# Constants for text
GREEN_CIRCLE = "🟢"
ORANGE_CIRCLE = "🟠"
RED_CIRCLE = "🔴"

FIRST_PLACE_EMOJI = "🥇"
SECOND_PLACE_EMOJI = "🥈"
THIRD_PLACE_EMOJI = "🥉"

AWARDING_SENTENCES = [
    "{0} is the first solver for problem [#{1}: '{2}'](<https://projecteuler.net/problem={1}>)! Congratulations! " + FIRST_PLACE_EMOJI,
    "{0} is the second solver for problem [#{1}: '{2}'](<https://projecteuler.net/problem={1}>)! Congratulations! " + SECOND_PLACE_EMOJI,
    "{0} is the third solver for problem [#{1}: '{2}'](<https://projecteuler.net/problem={1}>)! Congratulations! " + THIRD_PLACE_EMOJI,
    "{0} solved the problem [#{1}: '{2}'](<https://projecteuler.net/problem={1}>) which has been solved by {3} people, well done!"
]

THREAD_DEFAULT_NAME_FORMAT = "Problem #{0} discussion"

AUTHORS = {
    '124347516878585858': [561, 580, 599, 648, 670, 671, 821, 989], # griff
    '373553739531026432': [962, 994, 1010], # swistakk
    '1039557073073098794': [870, 899, 900, 915, 927, 937, 950], # univsersal set
    '624812149855748096': [939, 963], # philiplu
    '143174781561339904': [909, 910], # icy
    '694167474027102288': [936], # pjt
    '535780093272915978': [984], # jy
    '387012368812736514': [726, 968], # radewoosh
    '674014962422775809': [862, 893], # patryqss
    '277513085714038784': [989], # hacatu
    '442461159409451010': [780, 851, 930], # endagorion
    '1382925676528795668': [992], # byhill
    '677976899166797828': [653, 996] # Yoni
}

MAX_CONCURRENT_REQUESTS = 1


logging.basicConfig(
    level=logging.INFO,
    handlers=[RichHandler()],
    format="%(message)s",
)

log = logging.getLogger("app")


def pe_discord_api_setup(channels: dict):

    global CHANNELS_TO_ANNOUNCE, SPECIAL_CHANNELS_TO_ANNOUNCE, SMALL_ANNOUNCEMENTS_CHANNEL, THREADS_CHANNEL

    CHANNELS_TO_ANNOUNCE = channels["solve_channel"]
    SPECIAL_CHANNELS_TO_ANNOUNCE = channels["award_channel"]
    SMALL_ANNOUNCEMENTS_CHANNEL = channels["small_channel"]
    THREADS_CHANNEL = channels["thread_channel"]


def pe_unix_from_time(s: str):
    return int(datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timestamp())






