import logging
import random
import pandas as pd
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.airbnb_login import get_driver, login_airbnb, click_until_button_disappears
from utils.scrape_status import scrape_table
from utils.airbnb_scrape_data_store import store_listing_status

logger = logging.getLogger(__name__)



def fetch_listing_status(username, password):
    logger.info(f"Processing account {username}")

    pd.set_option("display.max_columns", None)

    with get_driver() as driver:
        # login and fetch status
        driver.get("https://www.airbnb.ca/hosting/listings")

        time.sleep(random.uniform(3, 5))
        login_success = login_airbnb(driver, username, password, wait_time=20)
        if not login_success:
            logger.info("Login failed, exiting the program.")
            sys.exit(1)

        logger.info("Login success")

        # fetch status
        listing_status_df = scrape_table(driver)
        status_df = pd.DataFrame(listing_status_df).astype(str)
        logger.info("Done fetching status")
        store_listing_status(status_df)


# fetch_listing_private_info("data.bnb@NovaVacation.com", "Data@2024*")