import os

from digster_api.selenium_scrapper import SeleniumScrapper
from digster_api.spotify_controller import SpotifyController

# from datetime import datetime


scrapper = SeleniumScrapper(
    str(os.environ.get("SPOTIFY_USER")),
    str(os.environ.get("SPOTIFY_PWD")),
    str(os.environ.get("CHROME_DRIVER")),
)
token = scrapper.get_token()

spotify_client_id = str(os.environ.get("SPOTIFY_CLIENT_ID"))
spotify_client_secret = str(os.environ.get("SPOTIFY_CLIENT_SECRET"))
spotify_client = SpotifyController(
    client_id=spotify_client_id, client_secret=spotify_client_secret
)
print(
    spotify_client.get_tracks_info(
        token=token,
        track_ids=["4bqCS9VUNFQPW8GJ5sllHX", "3xRiTUZdmkH3HyEXy2aG6G"],
    )
)
