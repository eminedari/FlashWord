import os
import sys

import psycopg2 as dbapi2

INIT_STATEMENTS = [
    """
    create table if not exists users(
        id serial primary key,
        username varchar unique not null,
        password varchar not null,
        first_name varchar not null,
        last_name varchar not null,
        contact varchar unique not null
    )
    """,
    """
    create table if not exists languages(
        id serial primary key,
        name varchar unique not null
    )
    """,
    """
    create table if not exists spoken_languages(
        user_id integer not null,
        lang_id integer not null,
        level varchar,

        foreign key(user_id) references users(id) on delete cascade,
        foreign key(lang_id) references languages(id) on delete restrict,        
        primary key(user_id,lang_id)
    )""",
    """
    create table if not exists decks(
        id serial primary key,
        title varchar not null,
        card_count integer default 0,
        front_lang integer not null,
        back_lang integer not null,
        owning_user integer not null,
        quiz_score float(2) default 0,
        privacy bool not null,
        foreign key(owning_user) references users(id) on delete cascade,
        foreign key(front_lang) references languages(id) on delete restrict,
        foreign key(back_lang) references languages(id) on delete restrict
    )
    """,
    """
    create table if not exists flashcards(
        id serial primary key,
        front varchar not null,
        back varchar not null,
        belonging_deck integer not null,
        
        foreign key(belonging_deck) references decks(id) on delete cascade
    )
    """,
    """
    create table if not exists shared_decks(
        user_id integer not null,
        deck_id integer not null,
        quiz_score float(2) default 0, 

        foreign key(deck_id) references decks(id) on delete cascade,
        foreign key(user_id) references users(id) on delete cascade,
        
        primary key(user_id,deck_id)
    )
    """,
    """
    create table if not exists keywords(
        id serial primary key,
        keyword varchar unique not null 
    )
    """,
    """
    create table if not exists deck_keyword(
        deck_id integer not null,
        keyword_id integer not null, 

        foreign key(deck_id) references decks(id) on delete cascade,
        foreign key(keyword_id) references keywords(id) on delete cascade,
        primary key(deck_id,keyword_id)
    )
    """            
]


def initialize(url):
    with dbapi2.connect(url) as connection:
        cursor = connection.cursor()
        for statement in INIT_STATEMENTS:
            cursor.execute(statement)
        cursor.close()

#heroku için

if __name__ == "__main__":
    url = os.getenv("DATABASE_URL")
    if url is None:
        print("Usage: DATABASE_URL=url python db_init.py")  # , file=sys.stderr)
        sys.exit(1)
    initialize(url)