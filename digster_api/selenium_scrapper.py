import time
from typing import Any, Dict, List

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

    def get_spotify_token(self) -> str:
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
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
        time.sleep(3)
        button = driver.find_element_by_id("login-username")
        button.send_keys("maxence.b.roux@gmail.com")
        button = driver.find_element_by_id("login-password")
        button.send_keys("}jdS[Uc[qwX{")
        button = driver.find_element_by_id("login-button").click()
        time.sleep(4)
        button = driver.find_element_by_id("oauth-input")
        token = button.get_attribute("value")
        driver.quit()
        return token

    def get_chartmetric_cookie(self, cm_email: str, cm_password: str) -> str:
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
        driver.get("https://app.chartmetric.com/login")
        driver.find_element_by_id("email").send_keys(cm_email)
        driver.find_element_by_id("password").send_keys(cm_password)
        driver.find_element_by_xpath("//button[@type='submit']").click()
        time.sleep(3)
        driver.get("https://api.chartmetric.com/user/auth")
        time.sleep(3)
        print(driver.get_cookie("connect.sid"))
        cookie = driver.get_cookie("connect.sid").get("value")
        driver.quit()
        return cookie

    def get_album_genres(self, albums: List[Dict]):
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
        url = f"https://www.discogs.com/"
        driver.get(url)
        time.sleep(1)
        results = []
        driver.find_element_by_id("onetrust-accept-btn-handler").click()
        for album in albums:
            print(album)
            query = (
                f'{album["album_name"].replace(" ", "+")}+{album["artist_name"].replace(" ", "+")}'
            )
            url = f"https://www.discogs.com/search/?q={query}&type=all"
            driver.get(url)

            search_results = driver.find_elements_by_xpath(
                '//div[@id="search_results"]/div'
            )
            if search_results:

                search_results[0].click()
                time.sleep(0.5)
                info = driver.find_elements_by_xpath(
                    '//table[@class="table_1fWaB"]/tbody/tr'
                )
                genres = ""
                styles = ""
                if info:
                    for item in info[0].find_elements_by_xpath("//tr"):
                        if "Genre: " in item.text:
                            genre_str = item.text
                            genres = genre_str.split("Genre: ")[1].split(", ")
                        if "Style: " in item.text:
                            style_str = item.text
                            styles = style_str.split("Style: ")[1].split(", ")
                    results.append(
                        {
                            "album_id": album["id"],
                            "genres": genres,
                            "styles": styles,
                        }
                    )
                print(results)
        driver.quit()
        return results
