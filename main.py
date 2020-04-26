import os
import random
import subprocess

from pydub import AudioSegment

import params
from fingerprint import process
from recognize import get_matches

from db.database import Database
from db.models import Song, Fingerprint, SongFingerprintAssociation


def learn(db: Database, audio_segment: AudioSegment, sname: str):
    print('Getting fingerprints..')
    fingerprints = process(audio_segment)

    print('Getting matches...')
    sid, mratio = get_matches(db, random.sample(fingerprints, 5000))

    if mratio > 0.8:
        print(f'Found match: {sid}, ratio: {mratio}, skipping.')
    else:
        print('Saving...')
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

    songs = [(os.path.join(songs_dir, name), name) for name in os.listdir(songs_dir)]
    random.shuffle(songs)

    for pt, name in songs:
        if name.endswith('.mp4'):
            print(f'Converting: {pt}')
            subprocess.call([
                'ffmpeg', '-i', pt, pt.replace('.mp4', '.mp3')
            ])
            os.remove(pt)
            name = name.replace('.mp4', '.mp3')
            pt = pt.replace('.mp4', '.mp3')
        if name.endswith('.mp3'):
            print(f'Learning: {pt}')
            audio_file = AudioSegment.from_mp3(pt)
            learn(db, audio_file, name)
