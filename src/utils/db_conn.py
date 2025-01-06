from sqlalchemy import create_engine
import psycopg2

from config import db_config

def get_db_connection(db):
    db_config_entry = db_config[db]
    connection_string = (
        f"postgresql+psycopg2://{db_config_entry['USER']}:{db_config_entry['PASSWORD']}@"
        f"{db_config_entry['SERVER']}:{db_config_entry['PORT']}/{db_config_entry['DATABASE']}"
    )
    engine = create_engine(connection_string)
    return engine

