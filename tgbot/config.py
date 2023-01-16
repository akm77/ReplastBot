from dataclasses import dataclass

from environs import Env


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
    other_params: str = None


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    misc: Miscellaneous


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

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
            tzinfo=env.str('TZINFO')
        )
    )
