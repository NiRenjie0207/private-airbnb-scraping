import sys
import os
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db_conn import get_db_connection
logger = logging.getLogger(__name__)


def store_listing_status(status_df):
    engine = get_db_connection('local')

    try:
        with engine.connect() as conn:
            with conn.begin() as transaction:
                if not status_df.empty:
                    update_query = text("""
                        INSERT INTO private_airbnb.listing_status (
                            property_code, title, listing_id, image_url, location, 
                            status, sync_status, last_updated, last_modified
                        )
                        VALUES (
                            :property_code, :title, :listing_id, :image_url, :location,
                            :status, :sync_status, :last_updated, null
                        )
                        ON CONFLICT (listing_id) 
                        DO UPDATE SET
                            title = EXCLUDED.title,
                            property_code = EXCLUDED.property_code,
                            image_url = EXCLUDED.image_url,
                            location = EXCLUDED.location,
                            status = EXCLUDED.status,
                            sync_status = EXCLUDED.sync_status,
                            last_updated = EXCLUDED.last_updated
                    """)

                    today = datetime.today().strftime('%Y-%m-%d')
                    params = [{
                        'property_code': row['property_code'],
                        'title': row['title'],
                        'listing_id': row['listing_id'],
                        'image_url': row['image_url'],
                        'location': row['location'],
                        'status': row['status'],
                        'sync_status': row['sync_status'],
                        'last_updated': today
                    } for _, row in status_df.iterrows()]

                    conn.execute(update_query, params)
                    transaction.commit()
                    logger.info("Successfully merged status data")
                else:
                    logger.info("Status data is empty")

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise
    finally:
        engine.dispose()