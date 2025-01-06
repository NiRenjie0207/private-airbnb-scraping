import logging
import sys
import os
import time
import random
from contextlib import contextmanager
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException,
    StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

def setup_chrome_for_airbnb():
    original_dir = Path(r"C:\Users\devadmin\AppData\Local\Google\Chrome\User Data")
    automation_dir = Path(r"C:\automation\chrome_user_data2")

    try:
        automation_dir.mkdir(parents=True, exist_ok=True)

        if automation_dir.exists():
            shutil.rmtree(automation_dir)
            automation_dir.mkdir(parents=True, exist_ok=True)

        root_files = ['Local State']
        for file in root_files:
            src = original_dir / file
            dst = automation_dir / file
            if src.exists():
                shutil.copy2(src, dst)

        profile_src = original_dir / 'Profile 4'
        profile_dst = automation_dir / 'Profile 4'

        if profile_src.exists():
            shutil.copytree(profile_src, profile_dst)

        return str(automation_dir)
    except Exception as e:
        print(f"Error when setting account: {e}")
        return None

def setup_proxy_extension(proxy_host: str, proxy_port: str, proxy_user: str, proxy_pass: str) -> str:
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 3,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "storage",
            "unlimitedStorage",
            "webRequest",
            "webRequestAuthProvider"
        ],
        "host_permissions": ["<all_urls>"],
        "background": {
            "service_worker": "background.js"
        }
    }
    """

    background_js = """
    const config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "https",
                host: "%s",
                port: parseInt("%s")
            },
            bypassList: ["localhost", "127.0.0.1"]
        }
    };

    chrome.proxy.settings.set({value: config, scope: 'regular'}, function() {});

    chrome.webRequest.onAuthRequired.addListener(
        function(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        },
        {urls: ["<all_urls>"]},
        ["blocking"]
    );
    """ % (proxy_host, proxy_port, proxy_user, proxy_pass)

    plugin_dir = 'proxy_auth_plugin'
    if not os.path.exists(plugin_dir):
        os.makedirs(plugin_dir)

    with open(f"{plugin_dir}/manifest.json", 'w') as f:
        f.write(manifest_json)

    with open(f"{plugin_dir}/background.js", 'w') as f:
        f.write(background_js)

    return os.path.abspath(plugin_dir)

def initialize_driver(user_data_dir) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # options.add_argument('--headless=new')
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--log-level=3")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-application-cache")
    options.add_argument("--disable-notifications")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-popup-blocking")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument("--profile-directory=Profile 4")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    ]
    options.add_argument(f'user-agent={random.choice(user_agents)}')

    proxy_host = os.environ.get('PROXY_HOST', "usa.rotating.proxyrack.net")
    proxy_port = os.environ.get('PROXY_PORT', "10060")
    proxy_user = os.environ.get('PROXY_USER', "novavacation")
    proxy_pass = os.environ.get('PROXY_PASS', "VIW1OTR-H19QIPG-DXG0GII-BCPZEKL-YZZAD0W-AL1FS6N-OMQGRBR")

    if proxy_host and proxy_port:
        if proxy_user and proxy_pass:
            logger.info("Using Proxy with authentication")
            plugin_path = setup_proxy_extension(proxy_host, proxy_port, proxy_user, proxy_pass)
            options.add_argument(f'--load-extension={plugin_path}')
        else:
            options.add_argument(f'--proxy-server={proxy_host}:{proxy_port}')

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = {
                    runtime: {},
                };
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """
        })

        driver.execute_script("""
            window.navigator.chrome = {
                runtime: {}
            };
            window.navigator.permissions = {
                query: () => Promise.resolve({ state: 'granted' })
            };
        """)
        time.sleep(random.uniform(2, 5))

        return driver

    except Exception as e:
        logger.info(f"Failed to initialize Chrome driver: {e}")
        raise

@contextmanager
def get_driver():
    driver = None
    try:
        # user_data_dir = "C:/automation/chrome_user_data"
        user_data_dir = setup_chrome_for_airbnb()
        logger.info(f"Using user data directory: {user_data_dir}")
        driver = initialize_driver(user_data_dir)
        yield driver
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.info(f"Error closing driver: {e}")

def click_submit_button(wait: WebDriverWait):
    try:
        submit_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='signup-login-submit-btn']"))
        )
        submit_button.click()
    except TimeoutException:
        logger.info("Submit button not found or not clickable")
        raise

def accept_cookies(driver, wait):
    try:
        ok_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept all']"))
        )
        ok_button.click()
        logger.info("Accepted cookies")
        return True
    except TimeoutException:
        logger.info("No cookies consent popup or failed to close it")
        return False

def random_mouse_move_click(driver, element):
    actions = ActionChains(driver)
    actions.move_to_element(element)

    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-10, 10)
    actions.move_by_offset(offset_x, offset_y)
    actions.click()
    actions.perform()
    logger.debug(f"Clicked element at offset ({offset_x}, {offset_y}).")

def random_mouse_move_click_show_more(driver, element):
    actions = ActionChains(driver)
    actions.move_to_element(element)

    offset_x = random.randint(-2, 2)
    offset_y = random.randint(-2, 2)
    actions.move_by_offset(offset_x, offset_y)
    actions.click()
    actions.perform()
    logger.debug(f"Clicked element at offset ({offset_x}, {offset_y}).")

def random_typing(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.25))
    logger.debug(f"Typed text: {text}")

def scroll_page(driver):
    scroll_height = random.randint(50, 100)
    driver.execute_script(f"window.scrollBy(0, {scroll_height});")
    logger.debug(f"Scrolled down by {scroll_height} pixels.")
    time.sleep(random.uniform(0.5, 1.5))

def check_security_verification(driver: webdriver.Chrome, wait_time: int = 20) -> bool:
    wait = WebDriverWait(driver, wait_time)
    try:
        modal = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='arkose-modal-header-id']")))
        logger.info("Security verification modal detected. Waiting for 3 minutes for manual resolution.")
        time.sleep(180)
        return True
    except:
        logger.info("No security verification modal detected.")
        return False

def login_airbnb(driver: webdriver.Chrome, username: str, password: str, wait_time: int = 120) -> bool:
    wait = WebDriverWait(driver, wait_time)
    actions = ActionChains(driver)

    try:
        time.sleep(random.uniform(12, 15))

        logger.info("Checking if the account has been logged in ")

        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 't8twbde')]")))
            logger.info("Already logged in.")
            return True
        except:
            logger.info("No profile is detected.")

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        accept_cookies(driver, wait)
        scroll_page(driver)

        log_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Continue with email']"))
        )
        random_mouse_move_click(driver, log_button)
        time.sleep(random.uniform(1, 3))
        scroll_page(driver)

        email_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@inputmode='email']"))
        )
        actions.move_to_element(email_input).click().perform()
        random_typing(email_input, username)
        time.sleep(random.uniform(1, 3))

        click_submit_button(wait)

        logger.info("Entered username.")

        time.sleep(random.uniform(3, 6))

        password_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='user[password]']"))
        )
        actions.move_to_element(password_input).click().perform()
        random_typing(password_input, password)
        time.sleep(random.uniform(1, 3))

        click_submit_button(wait)

        logger.info("Entered password and submitted.")

        scroll_page(driver)

        wait.until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 't8twbde')]"))
        )

        logger.info("Login successful")
        return True

    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return False


def click_until_button_disappears(driver: webdriver.Chrome, xpath: str, delay: float = 2):
    tried = False

    while True:
        try:
            button = driver.find_element(By.XPATH, xpath)

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            logger.debug("Scrolled to the bottom of the page.")
            time.sleep(random.uniform(1.5, 2))
            # random_mouse_move_click_show_more(driver, button)
            button.click()
            logger.debug("Clicked the load more button.")
            time.sleep(delay)

        except (NoSuchElementException, StaleElementReferenceException):
            if not tried:
                tried = True
                logger.debug("Failed to find the button. Trying again...")
                time.sleep(delay)
                continue
            else:
                logger.info("All content loaded successfully (button no longer present).")
                return True

        except ElementClickInterceptedException:
            logger.warning("Click intercepted, retrying after delay.")
            time.sleep(delay)

        except Exception as e:
            logger.error(f"Unexpected error while clicking button: {str(e)}")
            return False