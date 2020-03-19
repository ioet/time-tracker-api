"""
Agnostic database assets

Put here your utils and class independent of
the database solution.
To know more about protocols and subtyping check out PEP-0544
"""
import abc
import enum
from datetime import datetime

from flask import Flask


class DATABASE_TYPE(enum.Enum):
    IN_MEMORY = 'in-memory'
    SQL = 'sql'


class CRUDDao(abc.ABC):
    @abc.abstractmethod
    def get_all(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, id):
        raise NotImplementedError

    @abc.abstractmethod
    def create(self, project):
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, id, data):
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, id):
        raise NotImplementedError


class Seeder(abc.ABC):
    @abc.abstractmethod
    def run(self):
        """Provision database"""
        raise NotImplementedError

    @abc.abstractmethod
    def fresh(self):
        """will drop all tables and seed again the database"""
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        self.run()


class DatabaseModel:
    """
    Represents a model of a particular database, 
    e.g. SQL Model
    """

    def to_dto(self):
        """Override this in case you need a DTO instead of a model"""
        return self


def convert_result_to_dto(f):
    def convert_if_necessary(result):
        if hasattr(result, 'to_dto'):
            return result.to_dto()
        elif issubclass(type(result), list):
            return list(map(convert_if_necessary, result))
        return result

    def to_dto(*args, **kw):
        """
        Decorator that converts any result that is a
        DatabaseModel into its correspondent dto.
        """
        result = f(*args, **kw)
        return convert_if_necessary(result)

    return to_dto


seeder: Seeder = None


def init_app(app: Flask) -> None:
    """Make the app ready to use the database"""
    database_strategy = app.config['DATABASE']
    with app.app_context():
        globals()["use_%s" % database_strategy.name.lower()](app)


def use_sql(app: Flask) -> None:
    from time_tracker_api.sql_repository import init_app, SQLSeeder
    init_app(app)
    global seeder
    seeder = SQLSeeder()
