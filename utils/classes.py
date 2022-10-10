import json


class ControllerEmoji:
    PLAY_EMOJI = "<:play_green:1010166365249884270>"
    STOP_EMOJI = "<:stop_red:1010166366961156136>"
    PAUSE_EMOJI = "<:pause_light_green:1010167932023738459>"
    SKIP_EMOJI = "<:skip:1010162273819562085>"
    SHUFFLE_EMOJI = "<:shuffle:1010163081202126898>"
    LOOP_MODE_EMOJI = "<:rep:1010164285638443029>"


class Config:
    _config = json.load(open("config.json"))
    TOKEN: str = _config["TOKEN"]
    LAVA_HOST: str = _config["LAVA_HOST"]
    LAVA_PORT: int = _config["LAVA_PORT"]
    LAVA_PASS: str = _config["LAVA_PASS"]
    DJ_ROLE_ID: int = _config["DJ_ROLE_ID"]
    MUSIC_CHANNEL: int = _config["MUSIC_CHANNEL"]
    GUILD_IDS: list[int] = _config["GUILD_IDS"]
    SPOTIFY_CLIENT_ID: str = _config["SPOTIFY_CLIENT_ID"]
    SPOTIFY_SECRET: str = _config["SPOTIFY_SECRET"]


class PlayerControls:
    PLAY = "musicplayer_play"
    STOP = "musicplayer_stop"
    PAUSE = "musicplayer_pause"
    SKIP = "musicplayer_skip"
    SHUFFLE = "musicplayer_shuffle"
    LOOP_MODE = "musicplayer_loop_mode"
    ADD_TO_PLAYLIST = "musicplayer_add_to_playlist"
    REMOVE_FROM_PLAYLIST = "musicplayer_remove_from_playlist"
