from sqlalchemy import create_engine, MetaData
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.automap import automap_base
from config import SBConfig
from sqlalchemy import Table, Column, Integer, ForeignKey, String, DateTime
from datetime import datetime
from sqlalchemy.orm import Session


db_conf = SBConfig.get_db_config() + '/gcd'
engine = create_engine(db_conf)
print(engine.table_names())
metadata = MetaData()
metadata.reflect(engine)

Base = automap_base(metadata=metadata)
Base.prepare()

G_Issues = Base.classes.gcd_issue
G_Series = Base.classes.gcd_series
G_Publisher = Base.classes.gcd_publisher
G_Story = Base.classes.gcd_story
G_Brand = Base.classes.gcd_brand
G_Language = Base.classes.stddata_language

gcd_db_session = Session(engine)

#gcd_db_session = scoped_session(sessionmaker(autocommit=False,
#                                         autoflush=False,
#                                         bind=engine))
#Session = sessionmaker(bind=engine)
