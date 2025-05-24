import time
import subprocess
import random
import nanoid
import requests
import httpx
import json
import os
import signal
import sys
import traceback
import logging
import subprocess
import whisper
import re
import firebase_admin
from firebase_admin import credentials, firestore
from selenium import webdriver
from tqdm import tqdm
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


""" SETUP LOGGING """
logging.basicConfig(level = logging.DEBUG if os.environ["LOG_LEVEL"] == "debug" else logging.INFO)
logging.info("Logging basic config completed.")


""" GET THE WORK DIR """
WORK_DIR = os.environ["WORK_DIR"]


vpn_connection_attempted = False
def connect_to_vpn():
    global vpn_connection_attempted
    logging.info("Connecting to VeePN...")
    time_start = time.time()
    
    # Determine the extension ID of VeePN
    loaded_extensions = get_loaded_extensions()
    logging.info(f"Loaded extensions are: {loaded_extensions}")
    
    window_handles = driver.window_handles
    logging.info(f"Checking VeePN welcome page open: {len(window_handles)}")
    if len(window_handles) > 1:
        logging.info("VeePN welcome page has been opened attempting to close.")
        driver.switch_to.window(window_handles[-1])
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        logging.info("VeePN welcome page has been closed. Proceeding...")

    veepn_id = None
    for loaded_extension in loaded_extensions:
        if "VeePN" in loaded_extension["name"]:
            veepn_id = loaded_extension["id"]
    if veepn_id == None:
        logging.info("VPN extension not properly loaded.")
        raise Exception()
    driver.get(f"chrome-extension://{veepn_id}/src/popup/popup.html")
    
    # Attempt to connect to a random VPN.
    if vpn_connection_attempted == False:
        switch_to_window(0)
        continue_button = WebDriverWait(driver, MAX_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "intro-steps__btn"))
        )
        continue_button.click()
        time.sleep(1)
        continue_button.click()

    # Attempt to change the location for rotation purposes.
    vpn_connection_attempted = True
    location_select_button = WebDriverWait(driver, MAX_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "connect-region__location"))
    )
    location_select_button.click()
    locations_list = WebDriverWait(driver, MAX_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "locations-view__category-item"))
    )
    location_elements = locations_list.find_elements(By.CLASS_NAME, "locations-view__country-item")
    location_elements = location_elements[:len(location_elements)-1]
    random_location = random.choice(location_elements)
    random_location.click()
    connect_button = WebDriverWait(driver, MAX_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "connect-button"))
    )
    connect_button.click()
    logging.info(f"VeePN connected! ({round(time.time()-time_start, 2)}s)")
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "connect-button--connected"))
    )
    current_tabs = driver.window_handles
    if len(current_tabs) > 1:
        switch_to_window(0)



def get_loaded_extensions():
    # Enable developer mode to see extension IDs
    driver.get("chrome://extensions")
    driver.execute_script("""
        const devToggle = document.querySelector('extensions-manager')
            ?.shadowRoot.querySelector('extensions-toolbar')
            ?.shadowRoot.querySelector('#devMode')
        if (devToggle.checked == false) devToggle.click()
    """)
    # Get extension details (requires JavaScript due to shadow DOM)
    return driver.execute_script("""
        let manager = document.querySelector('extensions-manager')
                        ?.shadowRoot;
        let list = manager.querySelector('extensions-item-list')
                        ?.shadowRoot || document.createElement("div");
        let items = list.querySelectorAll('extensions-item');

        return Array.from(items).map(item => {
            const shadow = item.shadowRoot;
            return {
                id: item.getAttribute('id'),
                name: shadow.querySelector('#name').textContent.trim(),
            };
        });
    """)


def switch_to_window(index):
    windows = driver.window_handles
    if index < len(windows):
        driver.switch_to.window(windows[index])
    else:
        logging.warning(f"No tab at index {index}")


def close_window(index):
    windows = driver.window_handles
    if index < len(windows):
        switch_to_window(1)
        driver.close()
    else:
        logging.warning(f"No tab at index {index}")


# Retreives a fresh key from the demo site to make API calls.
def get_new_token():
    global GOOGLE_TTS_ENDPOINT
    global driver
    logging.info("Refreshing token...")
    time_start = time.time()

    switch_to_window(0)
    waiter = WebDriverWait(driver, MAX_ELEMENT_TIMEOUT)

    driver.get("https://www.gstatic.com/cloud-site-ux/text_to_speech/text_to_speech.min.html")
    driver.execute_script("""
        (function(open) {
        XMLHttpRequest.prototype.open = function(method, url) {
            if (url.includes("https://cxl-services.appspot.com/proxy?url=https://texttospeech.googleapis.com/v1beta1/text:synthesize"))
                window.synthesize_url = url;
        };
        })(XMLHttpRequest.prototype.open);
    """)
    shadow_host = waiter.until(
        EC.presence_of_element_located((By.TAG_NAME, "ts-app"))
    )
    shadow_root = driver.execute_script("""
        return arguments[0].shadowRoot;
    """, shadow_host)
    start_button_element = shadow_root.find_element(By.CSS_SELECTOR, "ts-button#button")
    start_button_element.click()
    # Attempt to open the captcha challenge.
    open_captcha_challenge()
    # For simplicity use audio captchas.
    enable_audio_captcha()
    solution_text = get_captcha_solution()
    # Attempt to submit the captcha solution
    solution_text_box = WebDriverWait(driver, MAX_ELEMENT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, "audio-response"))
    )
    solution_text_box.send_keys(solution_text)
    # Submit the solution to attempt it.
    submit_button = WebDriverWait(driver, MAX_ELEMENT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, "recaptcha-verify-button"))
    )
    submit_button.click()
    
    # Check if another captcha solve is required.
    error_message_shown = True
    while error_message_shown == True:
        try:
            WebDriverWait(driver, MAX_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "rc-audiochallenge-error-message"))
            )
            new_solution = get_captcha_solution()
            solution_text_box.send_keys(new_solution)
            submit_button.click()
        except:
            error_message_shown = False
            
    driver.switch_to.default_content()
    GOOGLE_TTS_ENDPOINT =  driver.execute_script(
            """
                return window.synthesize_url;
            """)
    time_end = time.time()
    logging.info(f"Token has been refreshed ({round(time_end-time_start, 2)}s).")


def open_captcha_challenge():
    recaptcha_iframe = WebDriverWait(driver, MAX_ELEMENT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='recaptcha']"))
    )
    driver.switch_to.frame(recaptcha_iframe)
    recaptcha_anchor = WebDriverWait(driver, MAX_ELEMENT_TIMEOUT).until(
        EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
    )
    recaptcha_anchor.click()
    driver.switch_to.default_content()


def enable_audio_captcha():
    challenge_frame = WebDriverWait(driver, MAX_ELEMENT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[title*="challenge"]'))
    )
    driver.switch_to.frame(challenge_frame)
    # Attempt to open the audio captcha instead of the photo one.
    audio_captcha_button = WebDriverWait(driver, MAX_ELEMENT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, "recaptcha-audio-button"))
    )
    audio_captcha_button.click()


def get_captcha_solution():
    audio_link_button = WebDriverWait(driver, MAX_ELEMENT_TIMEOUT).until(
        EC.presence_of_element_located((By.CLASS_NAME, "rc-audiochallenge-tdownload-link"))
    )
    audio_url = audio_link_button.get_attribute("href")
    audio_file_path = download_file(audio_url)
    solution_text = whisper_model.transcribe(audio_file_path)
    # Delete the audio file to clean up.
    os.remove(audio_file_path)
    return solution_text["text"]


def reset_token_refresh_flags():
    global vpn_connection_attempted
    vpn_connection_attempted = False


def send_keys(element, text: str):
    for char in text:
        element.send_keys(char)
        time.sleep(random.random() * 0.7)


def get_chrome_version():
    try:
        # MacOS/Linux alternative
        result = subprocess.run(['google-chrome', '--version'],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        version = re.search(r'\d+', result.stdout)
        if version:
            return int(version.group(0))
    except:
        pass
    return None  # Couldn't determine version


def download_file(url, download_path=os.path.join(WORK_DIR, "recaptcha-audios")):
    # Create directory if it doesn't exist
    os.makedirs(download_path, exist_ok=True)
    # Generate filename
    filename = f"{nanoid.generate(size=5)}.mp3"
    output_path = os.path.join(download_path, filename)
    # Make the request (without streaming)
    response = requests.get(url)  # Removed stream=True
    response.raise_for_status()  # Raise error for bad status codes
    # Get total size from headers (may not be available without streaming)
    total_size = int(response.headers.get('content-length', len(response.content)))
    # Write file with progress bar
    with open(output_path, 'wb') as f, tqdm(
        desc=filename,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024
    ) as bar:
        # Write all content at once (no streaming)
        f.write(response.content)
        bar.update(len(response.content))
    return output_path


def start_process():
    global driver

    """ SET CHROME EXTENSIONS """
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--load-extension=/home/seluser/token-manager/extensions/veepn")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-accelerated-2d-canvas")
    logging.info("Chrome arguments updated via chrome options.")

    """ CONNECT TO THE REMOTE CHROME WEB DRIVER """
    driver = webdriver.Remote(
                    command_executor='http://localhost:4444/wd/hub',
                    options = chrome_options)
    logging.info(f"Web driver has been connected: {driver}")                
    logging.info("Web driver set up completed.")

    """ INITIALISE VPN CONNECTION """
    connect_to_vpn()
    
    """ REFRESH TOKEN AND UPDATE RECORDS """
    get_new_token()
    get_new_token()
    if len(GOOGLE_TTS_ENDPOINT) > 600:
        logging.info(f"New refreshed token: {GOOGLE_TTS_ENDPOINT[-10:]}")
        creds = database.collection("credentials")
        tts_cred = creds.document("google-tts")
        tts_cred.set(dict(endpoint = GOOGLE_TTS_ENDPOINT))

        
def end_process():
    global driver
    global database
    if driver:
        driver.quit()
    if database:
        database.close()
        
        
def test_audio_synthesis(token: str) -> requests.Response:
    try:
        payload = {
            "audioConfig": {
                "audioEncoding": "MP3",
                "effectsProfileId": [
                    "large-home-entertainment-class-device"
                ],
                "pitch": 0,
                "speakingRate": 1
            },
            "input": {
                "text": "This is a test."
            },
            "voice": {
                "languageCode": "en-US",
                "name": "en-US-Chirp3-HD-Gacrux"
            }
        }
        headers = {
            "Accept": "*/*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Content-Type": "text/plain;charset=UTF-8",
            "DNT": "1",
            "Origin": "https://www.gstatic.com",
            "Referer": "https://www.gstatic.com/",
            "Sec-CH-UA": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Linux"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }
        response = httpx.post(f"https://cxl-services.appspot.com/proxy?url=https://texttospeech.googleapis.com/v1beta1/text:synthesize&token={token}", headers=headers, content=json.dumps(payload))
        if response.is_error == False:
            return True
        logging.info(response.text)
        return False
    except:
        logging.info(traceback.format_exc())
        return False


""" SETUP SCRIPT EXIT EVENTS """
def on_sigterm(_, __):
    logging.info("Received termination signal")
    end_process()
    sys.exit(0)
signal.signal(signal.SIGTERM, on_sigterm)
signal.signal(signal.SIGINT, on_sigterm)

try:
    """ INITIALISE FIRABASE DATABASE """
    service_account = credentials.Certificate(os.path.join(WORK_DIR, "service-account.json"))
    firebase_admin.initialize_app(service_account)
    database = firestore.client()
    logging.info("Database has been connected.")

    """ SELENIUM SETUP PARAMETER """
    driver = None
    MAX_ELEMENT_TIMEOUT = 120
    TOKEN_REFRESH_TIMEOUT = 3600 # 1 hour timeout refresh rate

    """ GOOGLE TTS ENDPOINT AND LAST SAVED TOKEN """
    # GOOGLE_TOKEN = database.collection("credentials").document("google-tts").get().to_dict()["url"]
    # is_token_active = test_audio_synthesis(GOOGLE_TOKEN)
    # logging.info(f"Last saved token has been loaded: {GOOGLE_TOKEN[-10:]}")
    # if is_token_active:
    #     logging.info("Token is still active and valid, quitting...")
    #     sys.exit(0)

    """ OPENAI-WHISPER SETUP """
    whisper_model_variant = "tiny"
    whisper_model = whisper.load_model(whisper_model_variant)
    logging.info(f"Whisper model {whisper_model_variant} has been loaded.")

    """ START TOKEN REFRESH PROCESS """
    start_process()
except Exception as e:
    logging.info(traceback.format_exc())
    end_process()
except KeyboardInterrupt:
    logging.info("Script ended voluntarily by user.")
    end_process()
finally:
    logging.info("Clean up completed.")
    end_process()
    sys.exit(0)
