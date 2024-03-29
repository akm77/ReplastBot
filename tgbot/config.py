from dataclasses import dataclass
from typing import Any, Tuple, Optional

from environs import Env
from google.oauth2.service_account import Credentials


@dataclass
class DbConfig:
    dialect: str
    user: str
    password: str
    host: str
    database: str
    echo: bool


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]
    use_redis: bool


@dataclass
class Miscellaneous:
    tzinfo: str
    journal_chat: int
    shift_duration: int
    google_sheet_title: str
    scoped_credentials: Any = None
    calendar_locale: Tuple[Optional[str], Optional[str]] = (None, None)
    other_params: str = None


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    misc: Miscellaneous


def get_scoped_credentials(credentials, scopes):
    def prepare_credentials():
        return credentials.with_scopes(scopes)

    return prepare_credentials


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    scopes = [
        "https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
        "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"
    ]
    google_credentials = Credentials.from_service_account_file('tgbot/config-google.json')
    scoped_credentials = get_scoped_credentials(google_credentials, scopes)

    try:
        nl_langinfo, CODESET, *_ = list(map(str, env.list("CALENDAR_LOCALE")))
    except:
        nl_langinfo, CODESET = None, None

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMINS"))),
            use_redis=env.bool("USE_REDIS"),
        ),
        db=DbConfig(
            dialect=env.str('DB_DIALECT'),
            user=env.str('DB_USER'),
            password=env.str('DB_PASS'),
            database=env.str('DB_NAME'),
            host=env.str('DB_HOST'),
            echo=env.bool('DB_ECHO')
        ),
        misc=Miscellaneous(
            tzinfo=env.str('TZINFO'),
            journal_chat=env.int('JOURNAL_CHAT'),
            shift_duration=env.int('SHIFT_DURATION'),
            google_sheet_title=env.str('GOOGLE_SHEET_TITLE'),
            scoped_credentials=scoped_credentials,
            calendar_locale=(nl_langinfo, CODESET)
        )
    )
