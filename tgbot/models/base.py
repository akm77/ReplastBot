import logging
from typing import List, Optional

from sqlalchemy import DateTime, Column, Table, inspect, MetaData, func, event, types
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from tgbot.config import Config
from tgbot.misc.utils import value_to_decimal


meta = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})
MAX_SQLITE_INT = 2 ** 63 - 1


class VeryBigInt(types.TypeDecorator):
    impl = types.Integer
    cache_ok = False

    def process_bind_param(self, value, dialect):
        return hex(value) if value > MAX_SQLITE_INT else value

    def process_result_value(self, value, dialect):
        return int(value, 16) if isinstance(value, str) else value


class FinanceInteger(types.TypeDecorator):
    impl = types.Integer
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return int(value * 100) if value is not None else None

    def process_result_value(self, value, dialect):
        return value_to_decimal(value / 100, decimal_places=2) if value is not None else None


class AccountingInteger(types.TypeDecorator):
    impl = types.Integer
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return int(value * 10_000) if value is not None else None

    def process_result_value(self, value, dialect):
        return value_to_decimal(value / 10_000, decimal_places=4) if value is not None else None


def column_list(db_class) -> Optional[list]:
    return inspect(db_class).columns.keys()


Base = declarative_base(metadata=meta)


class BaseModel(Base):
    __abstract__ = True

    def __str__(self):
        model = self.__class__.__name__
        table: Table = inspect(self.__class__)
        primary_key_columns: List[Column] = table.columns
        values = {
            column.name: "{column.type} -> Primary key" if column.primary_key else f"{column.type}"
            for column in primary_key_columns
        }
        values_str = " ".join(f"{name}={value!r}" for name, value in values.items())
        return f"<{model} {values_str}>"


class TimedBaseModel(BaseModel):
    __abstract__ = True

    __mapper_args__ = {"eager_defaults": True}

    created_at = Column(DateTime(True), server_default=func.datetime('now', 'localtime'))
    updated_at = Column(
        DateTime(True), default=func.datetime('now', 'localtime'),
        onupdate=func.datetime('now', 'localtime'),
        server_default=func.datetime('now', 'localtime'))


async def create_db_session(config: Config) -> sessionmaker:
    logger = logging.getLogger(__name__)
    # dialect[+driver]: // user: password @ host / dbname[?key = value..],

    if config.db.dialect.startswith('sqlite'):
        database_uri = f"{config.db.dialect}:///{config.db.database}"
    else:
        database_uri = f"{config.db.dialect}://{config.db.user}:{config.db.password}" \
                       f"@{config.db.host}/{config.db.database}"

    engine = create_async_engine(
        database_uri,
        echo=config.db.echo,
        future=True
    )

    if config.db.dialect.startswith('sqlite'):
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    Session: sessionmaker = sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    logger.info(f"Database {database_uri} session successfully configured")
    return Session
