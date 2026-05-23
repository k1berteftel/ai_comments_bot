from dataclasses import dataclass

from environs import Env

'''
    При необходимости конфиг базы данных или других сторонних сервисов
'''


@dataclass
class tg_bot:
    token: str
    admin_ids: list[int]


@dataclass
class DB:
    dns: str


@dataclass
class NatsConfig:
    servers: list[str]


@dataclass
class UserBot:
    api_id: int
    api_hash: str


@dataclass
class APIMart:
    api_key: str


@dataclass
class Config:
    bot: tg_bot
    user_bot: UserBot
    db: DB
    nats: NatsConfig
    apimart: APIMart


def load_config(path: str | None = None) -> Config:
    env: Env = Env()
    env.read_env(path)

    return Config(
        bot=tg_bot(
            token=env('token'),
            admin_ids=list(map(int, env.list('admins')))
        ),
        user_bot=UserBot(
            api_id=int(env('api_id')),
            api_hash=env('api_hash')
        ),
        db=DB(
            dns=env('dns')
        ),
        nats=NatsConfig(
            servers=env.list('nats')
        ),
        apimart=APIMart(
            api_key=env('apimart_api_key')
        )
    )
