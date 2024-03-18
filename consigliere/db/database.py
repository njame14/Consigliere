import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Define path for database

#Get directory of database.py
dirPath = os.path.dirname(__loader__.path)
DB_PATH = os.path.join(dirPath, 'database.db')
Base = declarative_base()

class ApplicationDatabaseCtx:
    from db.models.music_data import MusicData
    from db.models.servers import Server

class ApplicationDatabase:
    def __init__(self):
        print('Initializing database...')

        # Initialize the engine and session
        self.engine = self.initialize_engine()
        self.Session = sessionmaker(bind=self.engine)

        # Set up context for models
        self.context = ApplicationDatabaseCtx()

        # Create tables
        self.create_tables()

    def initialize_engine(self):
        # Check if the database file exists, and create it if not
        if not os.path.isfile(DB_PATH):
            print('No database file located. Creating database file.')
        else:
            print('Database file located.')

        # Create an engine with echo set to False
        engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
        return engine

    def create_tables(self):
        # Create tables in the database for each model
        self.context.Server.__table__.create(bind=self.engine, checkfirst=True)
        self.context.MusicData.__table__.create(bind=self.engine, checkfirst=True)

    # Method to drop all tables
    def drop_tables(self):
        Base.metadata.drop_all(self.engine)
