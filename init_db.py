from db.database import Database
from db.models import *


def clear():
    db = Database()
    for model in models:
        db.drop_table(model)
        db.create_table(model)


if __name__ == '__main__':
    clear()
