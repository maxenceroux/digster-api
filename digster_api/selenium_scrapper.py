import time

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

load_dotenv()


class SeleniumScrapper:
    def __init__(
        self, spotify_user: str, spotify_password: str, chromedriver: str
    ) -> None:
        self.spotify_user = spotify_user
        self.spotify_password = spotify_password
        self.chromedriver = chromedriver

    def get_token(self) -> str:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920x1080")
        if self.chromedriver == "local":
            driver = webdriver.Chrome(options=chrome_options)
        else:
            driver = webdriver.Remote(
                "http://chrome:4444/wd/hub",
                DesiredCapabilities.CHROME,
                options=chrome_options,
            )
        driver.get("https://developer.spotify.com/console/get-several-shows/")
        time.sleep(1)
        button = driver.find_element_by_id(
            "onetrust-accept-btn-handler"
        ).click()
        time.sleep(1)

        driver.find_elements_by_xpath("//*[contains(text(), 'Get Token')]")[
            0
        ].click()
        time.sleep(1)
        button = driver.find_elements_by_xpath(
            """//input[@id='scope-user-read-recently-played']
            /following-sibling::span"""
        )[0]
        ActionChains(driver).move_to_element(button).click(button).perform()
        button = driver.find_element_by_id("oauthRequestToken").click()
        time.sleep(1)
        button = driver.find_element_by_id("login-username")
        button.send_keys(self.spotify_user)
        button = driver.find_element_by_id("login-password")
        button.send_keys(self.spotify_password)
        button = driver.find_element_by_id("login-button").click()
        time.sleep(1)
        button = driver.find_element_by_id("oauth-input")
        token = button.get_attribute("value")
        driver.quit()
        return token
