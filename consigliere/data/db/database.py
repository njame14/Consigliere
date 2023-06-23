import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

DB_PATH = f"{os.getcwd()}/consigliere/data/db/database.db"
Base = declarative_base()

def dbFileCreator():
    if os.path.isfile(DB_PATH):
        print('Database file located.')
        return
    else:
        print('No database file located. Creating database file.')
        try:
            file = open(DB_PATH, 'w')
            # Close the file
            file.close()
            print("Database file created successfully.")
        except Exception as e:
            raise e
        

class ApplicationDatabase:
    def __init__(self, guilds):
        print('Initializing database...')
        dbFileCreator()
        self.engine = create_engine(f'sqlite:///{DB_PATH}', echo=True)
        self.Session = sessionmaker(bind=self.engine)


    #Creates tables as specified in db.models
    def create_tables(self):
        #Models
        from consigliere.data.models.servers import Server
        Server.__table__.create(bind=self.engine)
        from consigliere.data.models.music_data import MusicData
        MusicData.__table__.create(bind=self.engine)
        Base.metadata.create_all(self.engine)
    
    #Drops all tables
    def drop_tables(self):
        Base.metadata.drop_all(self.engine)

#####################################################################################
#Db Functions(Probably not needed)
#####################################################################################

    #Decorator allows you to run db function within a transaction
    def with_commit(func):
        def inner(*args, **kwargs):
            with session() as session:
                func(session, *args, **kwargs)
                session.commit()
        return inner

    def autosave(self):
        self.Session.commit()

    def field(self, command, *values):
        """
        Executes a SQL command and returns a single value from the result.
        """
        return self.Session.execute(command, values).scalar()

    def record(self, command, *values):
        """
        Executes a SQL command and returns a single record (row) from the result.
        """
        return self.Session.execute(command, values).fetchone()

    def records(self, command, *values):
        """
        Executes a SQL command and returns all records (rows) from the result.
        """
        return self.Session.execute(command, values).fetchall()

    def column(self, command, *values):
        """
        Executes a SQL command and returns a single column from the result as a list.
        """
        return [item[0] for item in self.Session.execute(command, values).fetchall()]

    def execute(self, command, *values):
        """
        Executes a SQL command.
        """
        self.Session.execute(command, values)

    def multiexec(self, command, valueset):
        """
        Executes a SQL command multiple times with different parameter values.
        """
        self.Session.execute(command, valueset)

# event.listen(ApplicationDatabase.Session, 'after_commit', ApplicationDatabase.autosave)