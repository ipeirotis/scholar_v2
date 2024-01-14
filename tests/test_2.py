import unittest
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class RandomSearchTests(unittest.TestCase):
    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = Service(executable_path="./webdriver/chromedriver")
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def test_random_search(self):
        self.driver.get("https://scholar.ipeirotis.org/")
        search_terms = ["Panos Ipeirotis", "Adam Heller", "Juliana Freire", "Claudio T. Silva"]
        search_query = random.choice(search_terms)

        search_box = self.driver.find_element(By.NAME, "author_name")
        search_box.clear()
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)


    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()

