import time

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import random
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.airbnb_login import get_driver, login_airbnb, click_until_button_disappears

logger = logging.getLogger(__name__)

def get_element_text(parent_element, xpath: str) -> str:
    elements = parent_element.find_elements(By.XPATH, xpath)
    return elements[0].text if elements else "N/A"

def get_image_url(parent_element) -> str:
    elements = parent_element.find_elements(By.TAG_NAME, "img")
    return elements[0].get_attribute("src") if elements else "N/A"


def process_row(row):
    listing_id = row.get_attribute("data-testid")
    if not listing_id:
        return None

    cells = row.find_elements(By.TAG_NAME, "td")
    if len(cells) < 4:
        return None

    status = get_element_text(cells[2], ".//span")
    sync_status = get_element_text(cells[3], ".//span")

    listing_cell = cells[0]
    return {
        "property_code": get_element_text(listing_cell, ".//div[contains(@class, 's3ujbf2')]"),
        "title": get_element_text(listing_cell, ".//h2"),
        "listing_id": listing_id,
        "image_url": get_image_url(listing_cell),
        "location": cells[1].text if len(cells) > 1 else "N/A",
        "status": status,
        "sync_status": sync_status
    }

def scrape_table(driver: webdriver.Chrome, wait_time: int = 20) -> pd.DataFrame:
    for attempt in range(5):
        try:
            button_xpath = "/html/body/div[5]/div/div/div[1]/div/div/main/section/div/div/button"
            click_until_button_disappears(driver, button_xpath)
            table = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 't8twbde')]"))
            )
            tbody = table.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            logger.info(f"Found {len(rows)} rows of data")

            new_data = []
            for row in rows:
                try:
                    row_data = process_row(row)
                    if row_data:
                        new_data.append(row_data)
                except StaleElementReferenceException:
                    logger.warning("Stale element, skipping row")
                    continue
                except Exception as e:
                    logger.error(f"Error processing row data: {str(e)}")
                    continue

            if new_data:
                df = pd.DataFrame(new_data)
                df.drop_duplicates(inplace=True)
                logger.info(f"Data shape after update: {df.shape}")

                return df

            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Failed to scrape table data: {str(e)} with attempt {attempt}")
            driver.refresh()
            time.sleep(random.uniform(5, 7))
            continue

    logger.error("Max attempts reached but still failed to fetch the listing status ")
    return pd.DataFrame()