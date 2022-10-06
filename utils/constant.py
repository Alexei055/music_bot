import re
from disnake.ui import Button
from disnake import ButtonStyle
from .classes import *

URL_REG = re.compile(r'https?://(?:www\.)?.+')
DEFAULT_IMAGE_URL = "https://cdn.discordapp.com/attachments/991847730500604056/1010153812645924864/unknown.png"
MUSIC_EMBED_GIF = "https://cdn.discordapp.com/attachments/991847730500604056/1011315514875858965/post-59648-1198508549.gif"
MUSIC_EMBED_GIF_2 = "https://eartensifier.net/images/cd.png"
TRACK_POSITION_EMBED_EMOJI = "■"
TRACK_LEFT_EMOJI = "□"
SECONDS_FOR_UPDATE_PLAYER_MESSAGE = 5
PLAYER_TIMEOUT = 300

CONTROLLER_BUTTON = [
    Button(custom_id=PlayerControls.PAUSE,
           emoji=ControllerEmoji.PAUSE_EMOJI,
           style=ButtonStyle.gray),
    Button(custom_id=PlayerControls.STOP,
           emoji=ControllerEmoji.STOP_EMOJI,
           style=ButtonStyle.gray),
    Button(custom_id=PlayerControls.SKIP,
           emoji=ControllerEmoji.SKIP_EMOJI,
           style=ButtonStyle.gray),
    Button(custom_id=PlayerControls.SHUFFLE,
           emoji=ControllerEmoji.SHUFFLE_EMOJI,
           style=ButtonStyle.gray),
    Button(custom_id=PlayerControls.LOOP_MODE,
           emoji=ControllerEmoji.LOOP_MODE_EMOJI,
           style=ButtonStyle.gray),
    Button(custom_id=PlayerControls.ADD_TO_PLAYLIST,
           label="Добавить в плейлист",
           row=2,
           style=ButtonStyle.green),
    Button(custom_id=PlayerControls.REMOVE_FROM_PLAYLIST,
           label="Убрать из плейлиста",
           row=2,
           style=ButtonStyle.red),
]
