import params
from db.database import Database
from db.models import *


def clear(engine_url):
    db = Database(engine_url)
    for model in models:
        db.drop_table(model)
        db.create_table(model)


if __name__ == '__main__':
    db_url = f"{params.db_config['engine']}{params.db_config['path']}"
    clear(db_url)
