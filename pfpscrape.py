import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import random
from faker import Faker
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging
from requests.adapters import HTTPAdapter

# Constants
BASE_URL = "https://www.google.com/search?q={}&tbm=isch"
FOLDER_NAME = "data\\avatars"
NUM_THREADS = 500

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProfilePictureScraper:
    def __init__(self, prompt, folder_name=FOLDER_NAME, num_threads=NUM_THREADS):
        self.prompt = prompt
        self.folder_name = folder_name
        self.saved_image_urls = set()
        self.number = random.randint(1, 999) # random number to prevent overwriting files
        self.num_threads = num_threads
        self.session = requests.Session()  # use a session object
        self.session.mount('http://', HTTPAdapter(pool_maxsize=self.num_threads))
        self.session.mount('https://', HTTPAdapter(pool_maxsize=self.num_threads))
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

    def get_image_elements(self):
        encoded_prompt = quote_plus(self.prompt) + f"&{random.randint(1, 999)}_{int(time.time())}"
        url = BASE_URL.format(encoded_prompt)
        try:
            response = self.session.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get images: {e}")
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.find_all("img")

    def save_image(self, image_url, count):
        try:
            image_response = self.session.get(image_url)
            image_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to save image: {e}")
            return
        image_path = os.path.join(self.folder_name, f"profile_picture_{self.number}_{count}.jpg")
        with open(image_path, "wb") as image_file:
            image_file.write(image_response.content)
        self.saved_image_urls.add(image_url)

    def save_profile_pictures(self):
        count = 0
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []
            for image_element in self.get_image_elements():
                image_url = image_element.get("src")
                if image_url and image_url.startswith("http") and image_url not in self.saved_image_urls:
                    futures.append(executor.submit(self.save_image, image_url, count))
                    count += 1
            for future in as_completed(futures):
                future.result()  # to raise exception if any occurred during execution
        logger.info(f"{count} profile pictures saved to the '{self.folder_name}' folder. In the data folder, there are now {len(os.listdir(self.folder_name))} images.")

if __name__ == "__main__":
    fake = Faker()
    while True:
        prompt = random.choice([fake.word(), fake.sentence(), fake.paragraph()])
        logger.info(f"Generated prompt: {prompt}")
        scraper = ProfilePictureScraper(prompt, num_threads=NUM_THREADS)
        scraper.save_profile_pictures()