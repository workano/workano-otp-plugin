import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy_utils import database_exists, create_database
from xivo_dao.helpers.db_manager import Base, Session   # reuse them

# Base = declarative_base()

logger = logging.getLogger(__name__)
# ScopedSession = scoped_session(sessionmaker())


def init_db(db_uri):
    engine = create_engine(db_uri, pool_pre_ping=True)
    if not database_exists(engine.url):
        logger.info('creating db')
        create_database(engine.url)
    Session.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine, checkfirst=True)
