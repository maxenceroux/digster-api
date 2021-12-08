import os

import pytest
import requests

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
        client_id="test",
        client_secret="secret_test",
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


def test_spotify_get_unauth_token_failure():
    spotify_client = SpotifyController(
        client_id="wrong_token",
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )
    with pytest.raises(SystemExit) as excinfo:
        spotify_client.get_unauth_token()
    assert (
        "400 Client Error: Bad Request for url:"
        " https://accounts.spotify.com/api/token"
        in str(excinfo)
    )


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


def test_spotify_get_current_play_success(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )
    scrapper = SeleniumScrapper(
        spotify_user=os.environ.get("SPOTIFY_USER"),
        spotify_password=os.environ.get("SPOTIFY_PWD"),
        chromedriver="local",
    )
    token = scrapper.get_token()

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}

        def json(self):
            return {
                "device": {
                    "id": "48e02f76332948c9802c01bc5793e18edb3dc5dd",
                    "is_active": True,
                    "is_private_session": False,
                    "is_restricted": False,
                    "name": "macfrmro02",
                    "type": "Computer",
                    "volume_percent": 100,
                },
                "shuffle_state": False,
                "repeat_state": "off",
                "timestamp": 1638969938899,
                "context": {
                    "external_urls": {
                        "spotify": "https://open.spotiJu4msqrxnge75"
                    },
                    "href": "https://api.spotify.com/vJu4msqrxnge75",
                    "type": "album",
                    "uri": "spotify:album:13waVJVFIJu4msqrxnge75",
                },
                "progress_ms": 101283,
                "item": {
                    "album": {
                        "album_type": "album",
                        "artists": [
                            {
                                "external_urls": {
                                    "spotify": "https://open.rtist/2dhK4evl"
                                },
                                "href": "https://api.spohK4evl9ePjM6Kg59Tf3Q",
                                "id": "2dhK4evl9ePjM6Kg59Tf3Q",
                                "name": "Raoul Vignal",
                                "type": "artist",
                                "uri": "spotify:artist:2dhK4evl9ePjM6Kg59Tf3Q",
                            }
                        ],
                        "available_markets": [
                            "AD",
                            "AE",
                        ],
                        "external_urls": {
                            "spotify": "https://open.sp13waVJVFIJu4msqrxnge75"
                        },
                        "href": "https://api.spotify.comrxnge75",
                        "id": "13waVJVFIJu4msqrxnge75",
                        "images": [
                            {
                                "height": 640,
                                "url": "https://i.scdn.co/i9c9b4ed92",
                                "width": 640,
                            },
                            {
                                "height": 300,
                                "url": "https://i.6d00001e020a9ed92",
                                "width": 300,
                            },
                            {
                                "height": 64,
                                "url": "https://i.scdn.co/image/7529c9b4ed92",
                                "width": 64,
                            },
                        ],
                        "name": "Years in Marble",
                        "release_date": "2021-05-28",
                        "release_date_precision": "day",
                        "total_tracks": 11,
                        "type": "album",
                        "uri": "spotify:album:13waVJVFIJu4msqrxnge75",
                    },
                    "artists": [
                        {
                            "external_urls": {
                                "spotify": "https://open.sartiTf3Q"
                            },
                            "href": "https://api.spotify.cg59Tf3Q",
                            "id": "2dhK4evl9ePjM6Kg59Tf3Q",
                            "name": "Raoul Vignal",
                            "type": "artist",
                            "uri": "spotify:artist:2dhK4evl9ePjM6Kg59Tf3Q",
                        }
                    ],
                    "available_markets": ["AD"],
                    "disc_number": 1,
                    "duration_ms": 161301,
                    "explicit": False,
                    "external_ids": {"isrc": "FR59Y2111811"},
                    "external_urls": {
                        "spotify": "https://open.spotify.com/track/4bqCSsllHX"
                    },
                    "href": "https://api.spotify.com/v1/tracks/",
                    "id": "4bqCS9VUNFQPW8GJ5sllHX",
                    "is_local": False,
                    "name": "Moonlit Visit",
                    "popularity": 16,
                    "preview_url": "https://p.scdn.co/mp3-preview/?cid=",
                    "track_number": 11,
                    "type": "track",
                    "uri": "spotify:track:4bqCS9VUNFQPW8GJ5sllHX",
                },
                "currently_playing_type": "track",
                "actions": {"disallows": {"resuming": True}},
                "is_playing": True,
            }

        def raise_for_status(self):
            pass

    def mock_get(url, headers):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    assert spotify_client.get_current_play(token=token) == {
        "timestamp": 1638969938899,
        "song_id": "4bqCS9VUNFQPW8GJ5sllHX",
    }


def test_spotify_get_current_play_failure(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )
    scrapper = SeleniumScrapper(
        spotify_user=os.environ.get("SPOTIFY_USER"),
        spotify_password=os.environ.get("SPOTIFY_PWD"),
        chromedriver="local",
    )
    token = scrapper.get_token()

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}

        def raise_for_status(self):
            raise SystemExit()

    def mock_get(url, headers):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    with pytest.raises(SystemExit) as excinfo:
        spotify_client.get_current_play(token=token)
    assert "<ExceptionInfo" in str(excinfo)
