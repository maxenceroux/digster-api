from datetime import datetime
from typing import Any, Dict, List, Optional

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
        current_play["listened_at"] = response.json().get("timestamp")
        current_play["track_id"] = response.json().get("item").get("id")
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

    def get_recently_played(
        self,
        token: str,
        url: Optional[str] = None,
        after: Optional[int] = None,
        limit: Optional[int] = 10,
    ) -> Dict[str, Any]:
        if not url:
            if after:
                url = (
                    f"""{self._base_url}/v1/me/player/recently-played"""
                    f"""?limit={limit}&after={after}"""
                )
            else:
                url = (
                    f"""{self._base_url}/v1/me/player/recently-played"""
                    f"""?limit={limit}"""
                )
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
        if not response.json().get("items"):
            return {"message": f"no tracks played after {after}"}
        recently_played_tracks = []
        results = {}
        results["next_url"] = response.json().get("next")
        for track in response.json().get("items"):
            recently_played_tracks.append(
                {
                    "listened_at": datetime.fromisoformat(
                        track.get("played_at")[:-1]
                    ),
                    "track_id": track.get("track").get("id"),
                }
            )
        results["recently_played"] = recently_played_tracks
        return results

    def get_tracks_info(
        self, token: str, track_ids: List[str]
    ) -> Dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        params = {"ids": ",".join(track_ids)}
        url = f"{self._base_url}/v1/tracks"
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        if not response.json().get("tracks"):
            return {"message": "IDs corresponding to no tracks"}
        results = {}
        tracks_info = []
        for track in response.json().get("tracks"):
            tracks_info.append(
                {
                    "spotify_id": track.get("id"),
                    "name": track.get("name"),
                    "duration_ms": track.get("duration_ms"),
                    "popularity": track.get("popularity"),
                    "album_id": track.get("album").get("id"),
                }
            )
        results["tracks_info"] = tracks_info
        return results

    def get_tracks_attributes(
        self, token: str, track_ids: List[str]
    ) -> Dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        params = {"ids": ",".join(track_ids)}
        url = f"{self._base_url}/v1/audio-features"
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        if not response.json().get("audio_features"):
            return {"message": "IDs corresponding to no tracks"}
        results = {}
        tracks_audio_features = []
        for track in response.json().get("audio_features"):
            tracks_audio_features.append(
                {
                    "spotify_id": track.get("id"),
                    "danceability": track.get("danceability"),
                    "energy": track.get("energy"),
                    "key": track.get("key"),
                    "loudness": track.get("loudness"),
                    "mode": track.get("mode"),
                    "speechiness": track.get("speechiness"),
                    "acousticness": track.get("acousticness"),
                    "instrumentalness": track.get("instrumentalness"),
                    "liveness": track.get("liveness"),
                    "valence": track.get("valence"),
                    "tempo": track.get("tempo"),
                }
            )
        results["audio_features"] = tracks_audio_features
        return results
