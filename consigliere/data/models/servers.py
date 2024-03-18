from sqlalchemy import Column, Integer, String
from consigliere.data.db.database import Base

class Server(Base):
    __tablename__ = 'servers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    is_voiceActive = Column(Integer)
