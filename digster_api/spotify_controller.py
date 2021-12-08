from typing import Any, Dict

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()


class SpotifyController:
    def __init__(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self._base_url = "https://api.spotify.com"

    def get_unauth_token(self) -> str:
        url = "https://accounts.spotify.com/api/token"
        payload = "grant_type=client_credentials"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            response = requests.post(
                url,
                auth=HTTPBasicAuth(self.client_id, self.client_secret),
                headers=headers,
                data=payload,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        return response.json().get("access_token")

    def get_current_play(self, token: str) -> Dict[str, Any]:
        url = f"{self._base_url}/v1/me/player"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        current_play = {}
        current_play["timestamp"] = response.json().get("timestamp")
        current_play["song_id"] = response.json().get("item").get("id")
        return current_play

    def get_user_info(self, token: str) -> Dict[str, Any]:
        url = f"{self._base_url}/v1/me"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        current_user = {}
        current_user["id"] = int(response.json().get("id"))
        current_user["display_name"] = response.json().get("display_name")
        current_user["email"] = response.json().get("email")
        current_user["country"] = response.json().get("country")
        current_user["image_url"] = response.json().get("images")[0].get("url")
        return current_user

    # def get_user_recently_played(self, token, after):
    #     url = f"""https://api.spotify.com/v1/me/player/recently-played?
    #         &after={after}"""
    #     headers = {
    #         "Accept": "application/json",
    #         "Content-Type": "application/json",
    #         "Authorization": f"Bearer {token}",
    #     }
    #     response = requests.request("GET", url, headers=headers)
    #     if "items" not in response.json():
    #         return False
    #     songs = response.json()["items"]
    #     if len(songs) == 0:
    #         return False
    #     ts_li, spotify_li = [], []
    #     for song in songs:
    #         ts_li.append(song["played_at"])
    #         spotify_li.append(song["track"]["id"])
    #     songs_json = [
    #         {"ts": t, "spotify_id": sp} for t, sp in zip(ts_li, spotify_li)
    #     ]
    #     return songs_json
