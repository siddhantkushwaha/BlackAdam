from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship

Base = declarative_base()


class SongFingerprintAssociation(Base):
    __tablename__ = 'song_fingerprint_association'

    id = Column(Integer, primary_key=True)
    song_id = Column(Integer, ForeignKey('song.id'))
    fingerprint_id = Column(Integer, ForeignKey('fingerprint.binary'))

    offset = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    song = relationship('Song', back_populates='fingerprints')
    fingerprint = relationship('Fingerprint', back_populates='songs')


class Song(Base):
    __tablename__ = 'song'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    fingerprints = relationship('SongFingerprintAssociation', back_populates='song', cascade='all, delete-orphan')


class Fingerprint(Base):
    __tablename__ = 'fingerprint'
    binary = Column(Binary, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    songs = relationship('SongFingerprintAssociation', back_populates='fingerprint', cascade='all, delete-orphan')


models = [
    Song,
    Fingerprint,
    SongFingerprintAssociation
]
