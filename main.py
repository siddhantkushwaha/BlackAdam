import os

from pydub import AudioSegment

import params
from fingerprint import process
from recognize import get_matches

from db.database import Database
from db.models import Song, Fingerprint, SongFingerprintAssociation


def learn(db: Database, audio_segment: AudioSegment, sname: str):
    fingerprints = process(audio_segment)

    sid, mratio = get_matches(db, fingerprints)
    if mratio > 0.8:
        print(f'Found match: {sid}, ratio: {mratio}, skipping.')
    else:
        song = Song(title=sname)
        for binary, offset in fingerprints:
            fingerprint = Fingerprint(binary=binary.encode())

            sfa = SongFingerprintAssociation(offset=offset)
            sfa.fingerprint = fingerprint
            song.fingerprints.append(sfa)

        db.session.merge(song)
        db.session.commit()


if __name__ == '__main__':
    db_url = f"{params.db_config['engine']}{params.db_config['path']}"
    songs_dir = params.data_path

    db = Database(engine_url=db_url)
    songs = [(os.path.join(songs_dir, name), name) for name in os.listdir(songs_dir) if name.endswith('.mp4')]
    for pt, name in songs:
        print(f'Learning: {name}')
        audio_file = AudioSegment.from_mp3(pt)
        learn(db, audio_file, name)
