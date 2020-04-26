from pydub import AudioSegment

from db.database import Database
from fingerprint import process
from db.models import Song, Fingerprint


def get_matches(db: Database, fingerprints):
    """Not considering offset and time alignment for now"""

    hashes = {i[0].encode(): i[1] for i in fingerprints}

    result = db.session.query(Song.id, Fingerprint.binary) \
        .join(Song.fingerprints, Fingerprint) \
        .filter(Fingerprint.binary.in_(hashes)) \
        .distinct()

    count = {}
    for item in result:
        count[item[0]] = count.get(item[0], 0) + 1

    closes_match_song_id = max(count, key=lambda key: count[key])
    match_ratio = count[closes_match_song_id] / len(hashes)

    if match_ratio > 1:
        raise Exception(f'Invalid match ratio: {match_ratio}.')

    return closes_match_song_id, match_ratio


def recognize(db: Database, audio_segment: AudioSegment):
    fingerprints = process(audio_segment)
    return get_matches(db, fingerprints)
