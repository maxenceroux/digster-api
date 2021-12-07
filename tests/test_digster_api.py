import os

from digster_api import __version__
from digster_api.main import root
from digster_api.selenium_scrapper import SeleniumScrapper
from digster_api.spotify_controller import SpotifyController


def test_version():
    assert __version__ == "0.1.0"


def test_root():
    result = root()
    assert result.get("message") == "Hello World"


def test_spotify_client():
    spotify_client = SpotifyController(
        client_id="test", client_secret="secret_test"
    )
    assert spotify_client.client_id == "test"
    assert spotify_client._base_url == "https://api.spotify.com"


# TODO
# Mock API - MonkeyPatch
def test_spotify_get_unauth_token():
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )
    token = spotify_client.get_unauth_token()
    assert isinstance(token, str)
    assert len(token) == 83


def test_selenium_scrapper():
    scrapper = SeleniumScrapper(
        spotify_user=os.environ.get("SPOTIFY_USER"),
        spotify_password=os.environ.get("SPOTIFY_PWD"),
        chromedriver="local",
    )
    assert scrapper.chromedriver == "local"


def test_selenium_get_token():
    scrapper = SeleniumScrapper(
        spotify_user=os.environ.get("SPOTIFY_USER"),
        spotify_password=os.environ.get("SPOTIFY_PWD"),
        chromedriver="local",
    )
    token = scrapper.get_token()
    assert isinstance(token, str)
    assert len(token) == 278
