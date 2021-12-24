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


def test_selenium_get_spotify_token():
    scrapper = SeleniumScrapper(
        spotify_user=os.environ.get("SPOTIFY_USER"),
        spotify_password=os.environ.get("SPOTIFY_PWD"),
        chromedriver="local",
    )
    token = scrapper.get_spotify_token()
    assert isinstance(token, str)
    assert len(token) == 278


def test_spotify_get_current_play_success(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )

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
    assert spotify_client.get_current_play(token="test-token") == {
        "timestamp": 1638969938899,
        "track_id": "4bqCS9VUNFQPW8GJ5sllHX",
    }


def test_spotify_get_current_play_failure(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}

        def raise_for_status(self):
            raise requests.exceptions.HTTPError()

    def mock_get(url, headers):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    with pytest.raises(SystemExit) as excinfo:
        spotify_client.get_current_play(token="test-token")
    assert "HTTPError" in str(excinfo)


def test_spotify_get_user_info_success(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}

        def json(self):
            return {
                "country": "FR",
                "display_name": "Raxence Moux",
                "email": "maxence.b.roux@gmail.com",
                "explicit_content": {
                    "filter_enabled": False,
                    "filter_locked": False,
                },
                "external_urls": {
                    "spotify": "https://open.spotify.com/user/1138415959"
                },
                "followers": {"href": None, "total": 49},
                "href": "https://api.spotify.com/v1/users/1138415959",
                "id": "1138415959",
                "images": [
                    {
                        "height": None,
                        "url": "https://test_url",
                        "width": None,
                    }
                ],
                "product": "premium",
                "type": "user",
                "uri": "spotify:user:1138415959",
            }

        def raise_for_status(self):
            pass

    def mock_get(url, headers):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    assert spotify_client.get_user_info(token="test-token") == {
        "id": 1138415959,
        "display_name": "Raxence Moux",
        "email": "maxence.b.roux@gmail.com",
        "country": "FR",
        "image_url": "https://test_url",
    }


def test_spotify_get_user_info_failure(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}

        def raise_for_status(self):
            raise requests.exceptions.HTTPError()

    def mock_get(url, headers):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    with pytest.raises(SystemExit) as excinfo:
        spotify_client.get_user_info(token="test-token")
    assert "HTTPError" in str(excinfo)


def test_spotify_get_recently_played_success(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}

        def json(self):
            return {
                "items": [
                    {
                        "track": {
                            "album": {
                                "album_type": "album",
                                "available_markets": ["AD"],
                                "external_urls": {
                                    "spotify": (
                                        "https://open.spotify.co8E9Uzj1Tycdlf2"
                                    )
                                },
                                "href": (
                                    "https://api.spotify.com/vE9Uzj1Tycdlf2"
                                ),
                                "id": "3ZZMK1Hd8E9Uzj1Tycdlf2",
                                "name": "Afrique Victime",
                                "release_date": "2021-05-21",
                                "release_date_precision": "day",
                                "total_tracks": 9,
                                "type": "album",
                                "uri": "spotify:album:3ZZMK1Hd8E9Uzj1Tycdlf2",
                            },
                            "artists": [
                                {
                                    "external_urls": {
                                        "spotify": "htrtiO3pzd94"
                                    },
                                    "href": "https://api./arQ3E5KO3pzd94",
                                    "id": "48dgx7iGqLQ3E5KO3pzd94",
                                    "name": "Mdou Moctar",
                                    "type": "artist",
                                    "uri": (
                                        "spotify:artist:48dgx7iGqLQ3E5KO3pzd94"
                                    ),
                                }
                            ],
                            "available_markets": [
                                "AD",
                            ],
                            "disc_number": 1,
                            "duration_ms": 445816,
                            "explicit": False,
                            "external_ids": {"isrc": "USMTD2000459"},
                            "external_urls": {
                                "spotify": "httpscom1RhL5PGWaiYXwVmqOpj0Nm"
                            },
                            "href": "https://api.spotiOpj0Nm",
                            "id": "1RhL5PGWaiYXwVmqOpj0Nm",
                            "is_local": False,
                            "name": "Afrique Victime",
                            "popularity": 43,
                            "track_number": 8,
                            "type": "track",
                            "uri": "spotify:track:1RhL5PGWaiYXwVmqOpj0Nm",
                        },
                        "played_at": "2021-12-09T08:05:15.499Z",
                        "context": {
                            "external_urls": {
                                "spotify": (
                                    "https://openum/3ZZMK1Hd8E9Uzj1Tycdlf2"
                                )
                            },
                            "href": "https://api.sf2",
                            "type": "album",
                            "uri": "spotify:album:3ZZMK1Hd8E9Uzj1Tycdlf2",
                        },
                    }
                ],
                "next": "https://mock/recently-played?imit=1",
                "cursors": {
                    "after": "1639037115499",
                    "before": "1639037115499",
                },
                "limit": 1,
                "href": "https://api.spotify.y-played?limit=1",
            }

        def raise_for_status(self):
            pass

    def mock_get(url, headers):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    assert spotify_client.get_recently_played(
        token="test-token", after=1639037115000, limit=1
    ) == {
        "next_url": "https://mock/recently-played?imit=1",
        "recently_played": [
            {"timestamp": 1639033515499, "track_id": "1RhL5PGWaiYXwVmqOpj0Nm"}
        ],
    }


def test_spotify_get_recently_played_failure(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}

        def raise_for_status(self):
            raise requests.exceptions.HTTPError()

    def mock_get(url, headers):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    with pytest.raises(SystemExit) as excinfo:
        spotify_client.get_recently_played(
            token="test-token", after=1639037115000, limit=1
        )
    assert "HTTPError" in str(excinfo)


def test_spotify_get_recently_played_no_items(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}

        def raise_for_status(self):
            pass

        def json(self):
            return {
                "items": [],
                "next": (
                    "https://mock/recently-played?before=1639037115499&limit=1"
                ),
                "cursors": {
                    "after": "1639037115499",
                    "before": "1639037115499",
                },
                "limit": 1,
            }

    def mock_get(url, headers):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    tracks = spotify_client.get_recently_played(
        token="test-token", after=1639037115000, limit=1
    )
    assert tracks == {"message": "no tracks played after 1639037115000"}


def test_spotify_get_tracks_info_success(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}
            self.params = {"bla": 123}

        def json(self):
            return {
                "tracks": [
                    {
                        "album": {
                            "album_type": "album",
                            "artists": [
                                {
                                    "external_urls": {
                                        "spotify": (
                                            "https://open.spoPjM6Kg59Tf3Q"
                                        )
                                    },
                                    "id": "2dhK4evl9ePjM6Kg59Tf3Q",
                                    "name": "Raoul Vignal",
                                    "type": "artist",
                                    "uri": (
                                        "spotify:artist:2dhK4evl9ePjM6Kg59Tf3Q"
                                    ),
                                }
                            ],
                            "external_urls": {
                                "spotify": "/album/13waVJVFIJu4msqrxnge75"
                            },
                            "href": "/v1/albums/13waVJVFIJu4msqrxnge75",
                            "id": "13waVJVFIJu4msqrxnge75",
                            "images": [
                                {"height": 640, "width": 640},
                                {"height": 300, "width": 300},
                                {"height": 64, "width": 64},
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
                                    "spotify": "https:evl9ePjM6Kg59Tf3Q"
                                },
                                "href": "https://api.spotify",
                                "id": "2dhK4evl9ePjM6Kg59Tf3Q",
                                "name": "Raoul Vignal",
                                "type": "artist",
                                "uri": "spotify:artist:2dhK4evl9ePjM6Kg59Tf3Q",
                            }
                        ],
                        "disc_number": 1,
                        "duration_ms": 161301,
                        "explicit": False,
                        "external_ids": {"isrc": "FR59Y2111811"},
                        "external_urls": {
                            "spotify": "https://open.spotiQPW8GJ5sllHX"
                        },
                        "href": "https://api.spotify.com/v1/trUNFQPW8GJ5sllHX",
                        "id": "4bqCS9VUNFQPW8GJ5sllHX",
                        "is_local": False,
                        "name": "Moonlit Visit",
                        "popularity": 16,
                        "track_number": 11,
                        "type": "track",
                        "uri": "spotify:track:4bqCS9VUNFQPW8GJ5sllHX",
                    },
                    {
                        "album": {
                            "album_type": "album",
                            "artists": [
                                {
                                    "external_urls": {
                                        "spotify": "https://opeYpD2nt"
                                    },
                                    "href": "https://ap4k01UHAnX9skbKaqYpD2nt",
                                    "id": "4k01UHAnX9skbKaqYpD2nt",
                                    "name": "Yennu Ariendra",
                                    "type": "artist",
                                    "uri": (
                                        "spotify:artist:4k01UHAnX9skbKaqYpD2nt"
                                    ),
                                }
                            ],
                            "external_urls": {
                                "spotify": "https://open.spotify.cYe2ZyV8zWI0"
                            },
                            "href": "https://api.spotiftKZYe2ZyV8zWI0",
                            "id": "4ZXVA2sStKZYe2ZyV8zWI0",
                            "images": [
                                {"height": 640, "width": 640},
                                {"height": 300, "width": 300},
                                {"height": 64, "width": 64},
                            ],
                            "name": "Far Away Songs",
                            "release_date": "2018-09-24",
                            "release_date_precision": "day",
                            "total_tracks": 9,
                            "type": "album",
                            "uri": "spotify:album:4ZXVA2sStKZYe2ZyV8zWI0",
                        },
                        "artists": [
                            {
                                "external_urls": {
                                    "spotify": "httpy.com/artistskbKaqYpD2nt"
                                },
                                "href": "https://api.sHAnX9skbKaqYpD2nt",
                                "id": "4k01UHAnX9skbKaqYpD2nt",
                                "name": "Yennu Ariendra",
                                "type": "artist",
                                "uri": "spotify:artist:4k01UHAnX9skbKaqYpD2nt",
                            }
                        ],
                        "disc_number": 1,
                        "duration_ms": 402000,
                        "explicit": False,
                        "external_ids": {"isrc": "QM2PV1835184"},
                        "external_urls": {
                            "spotify": "https://rack/3xRiTUZdmkH3HyEXy2aG6G"
                        },
                        "href": "https://api.spotify.com/v1/tEXy2aG6G",
                        "id": "3xRiTUZdmkH3HyEXy2aG6G",
                        "is_local": False,
                        "name": "Departure. Cross the Sea",
                        "popularity": 2,
                        "track_number": 1,
                        "type": "track",
                        "uri": "spotify:track:3xRiTUZdmkH3HyEXy2aG6G",
                    },
                ]
            }

        def raise_for_status(self):
            pass

    def mock_get(url, headers, params):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    assert spotify_client.get_tracks_info(
        token="test-token",
        track_ids=["4bqCS9VUNFQPW8GJ5sllHX", "3xRiTUZdmkH3HyEXy2aG6G"],
    ) == {
        "tracks_info": [
            {
                "id": "4bqCS9VUNFQPW8GJ5sllHX",
                "name": "Moonlit Visit",
                "duration_ms": 161301,
                "popularity": 16,
                "album_id": "13waVJVFIJu4msqrxnge75",
            },
            {
                "id": "3xRiTUZdmkH3HyEXy2aG6G",
                "name": "Departure. Cross the Sea",
                "duration_ms": 402000,
                "popularity": 2,
                "album_id": "4ZXVA2sStKZYe2ZyV8zWI0",
            },
        ]
    }


def test_spotify_get_tracks_info_failure(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}
            self.params = {"bla": 123}

        def raise_for_status(self):
            raise requests.exceptions.HTTPError()

    def mock_get(url, headers, params):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    with pytest.raises(SystemExit) as excinfo:
        spotify_client.get_tracks_info(
            token="test-token",
            track_ids=["4bqCS9VUNFQPW8GJ5sllHX", "3xRiTUZdmkH3HyEXy2aG6G"],
        )
    assert "HTTPError" in str(excinfo)


def test_spotify_get_tracks_info_no_items(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}
            self.params = {"bla": 123}

        def raise_for_status(self):
            pass

        def json(self):
            return {
                "audio_features": [],
                "next": (
                    "https://mock/recently-played?before=1639037115499&limit=1"
                ),
                "cursors": {
                    "after": "1639037115499",
                    "before": "1639037115499",
                },
                "limit": 1,
            }

    def mock_get(url, headers, params):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    tracks_info = spotify_client.get_tracks_info(
        token="test-token",
        track_ids=["4bqCS9VUNFsllHX", "3xRiTUZdmkH3y2aG6G"],
    )
    assert tracks_info == {"message": "IDs corresponding to no tracks"}


def test_spotify_get_tracks_attributes_success(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}
            self.params = {"bla": 123}

        def json(self):
            return {
                "audio_features": [
                    {
                        "danceability": 0.606,
                        "energy": 0.295,
                        "key": 4,
                        "loudness": -13.721,
                        "mode": 0,
                        "speechiness": 0.0345,
                        "acousticness": 0.867,
                        "instrumentalness": 0.0826,
                        "liveness": 0.111,
                        "valence": 0.23,
                        "tempo": 132.104,
                        "type": "audio_features",
                        "id": "4bqCS9VUNFQPW8GJ5sllHX",
                        "uri": "spotify:track:4bqCS9VUNFQPW8GJ5sllHX",
                        "duration_ms": 161301,
                        "time_signature": 4,
                    },
                    {
                        "danceability": 0.631,
                        "energy": 0.446,
                        "key": 11,
                        "loudness": -10.702,
                        "mode": 0,
                        "speechiness": 0.0245,
                        "acousticness": 0.794,
                        "instrumentalness": 0.741,
                        "liveness": 0.109,
                        "valence": 0.353,
                        "tempo": 140.016,
                        "type": "audio_features",
                        "id": "3xRiTUZdmkH3HyEXy2aG6G",
                        "uri": "spotify:track:3xRiTUZdmkH3HyEXy2aG6G",
                        "duration_ms": 402000,
                        "time_signature": 4,
                    },
                ]
            }

        def raise_for_status(self):
            pass

    def mock_get(url, headers, params):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    assert spotify_client.get_tracks_attributes(
        token="test-token",
        track_ids=["4bqCS9VUNFQPW8GJ5sllHX", "3xRiTUZdmkH3HyEXy2aG6G"],
    ) == {
        "audio_features": [
            {
                "id": "4bqCS9VUNFQPW8GJ5sllHX",
                "danceability": 0.606,
                "energy": 0.295,
                "key": 4,
                "loudness": -13.721,
                "mode": 0,
                "speechiness": 0.0345,
                "acousticness": 0.867,
                "instrumentalness": 0.0826,
                "liveness": 0.111,
                "valence": 0.23,
                "tempo": 132.104,
            },
            {
                "id": "3xRiTUZdmkH3HyEXy2aG6G",
                "danceability": 0.631,
                "energy": 0.446,
                "key": 11,
                "loudness": -10.702,
                "mode": 0,
                "speechiness": 0.0245,
                "acousticness": 0.794,
                "instrumentalness": 0.741,
                "liveness": 0.109,
                "valence": 0.353,
                "tempo": 140.016,
            },
        ]
    }


def test_spotify_get_tracks_attributes_failure(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}
            self.params = {"bla": 123}

        def raise_for_status(self):
            raise requests.exceptions.HTTPError()

    def mock_get(url, headers, params):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    with pytest.raises(SystemExit) as excinfo:
        spotify_client.get_tracks_attributes(
            token="test-token",
            track_ids=["4bqCS9VUNFQPW8GJ5sllHX", "3xRiTUZdmkH3HyEXy2aG6G"],
        )
    assert "HTTPError" in str(excinfo)


def test_spotify_get_tracks_attributes_no_items(
    monkeypatch,
):
    spotify_client = SpotifyController(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    )

    class MockResponse(object):
        def __init__(self):
            self.status_code = 200
            self.url = "http://httpbin.org/get"
            self.headers = {"blaa": "1234"}
            self.params = {"bla": 123}

        def raise_for_status(self):
            pass

        def json(self):
            return {
                "audio_features": [],
                "next": (
                    "https://mock/recently-played?before=1639037115499&limit=1"
                ),
                "cursors": {
                    "after": "1639037115499",
                    "before": "1639037115499",
                },
                "limit": 1,
            }

    def mock_get(url, headers, params):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    tracks_info = spotify_client.get_tracks_attributes(
        token="test-token",
        track_ids=["4bqCS9VUNX", "3xRiTUZdmkH"],
    )
    assert tracks_info == {"message": "IDs corresponding to no tracks"}
