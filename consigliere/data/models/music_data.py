from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from consigliere.data.db.database import Base

class MusicData(Base):
    __tablename__ = 'musicData'
    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(Integer, ForeignKey('servers.id'))
    server = relationship('Server')
    url = Column(String)
    queue_pos = Column(Integer)