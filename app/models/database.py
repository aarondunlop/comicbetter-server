from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import SBConfig
from sqlalchemy import Table, Column, Integer, ForeignKey, String, DateTime
from datetime import datetime

engine = create_engine((SBConfig.get_db_config()), convert_unicode=False)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Main = declarative_base()
Main.query = db_session.query_property()

Session = sessionmaker(bind=engine)

# Define a base model for other database tables to inherit
class Base(Main):

    __abstract__  = True
    id      = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated = Column(DateTime, default=datetime.utcnow, nullable=False)

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import cbserver.models.arc
    import cbserver.models.character
    import cbserver.models.creator
    import cbserver.models.comicpages
    import cbserver.models.device
    import cbserver.models.issue
    import cbserver.models.publisher
    import cbserver.models.series
    import cbserver.models.settings
    import cbserver.models.team
    import cbserver.models.user
    Base.metadata.create_all(bind=engine)

def reset_db():
    Base.metadata.drop_all(bind=engine)
