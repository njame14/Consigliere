from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base

class MusicData(Base):
    __tablename__ = 'music_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    requester_id = Column(Integer)
    server_id = Column(Integer, ForeignKey('servers.id'))
    server = relationship('Server')
    url = Column(String)
    queue_pos = Column(Integer)