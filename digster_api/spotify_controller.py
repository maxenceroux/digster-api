from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import base64

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

    def refresh_access_token(self, refresh_token):
        auth_url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic "
            + base64.b64encode(
                (self.client_id + ":" + self.client_secret).encode()
            ).decode(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        try:
            response = requests.post(auth_url, headers=headers, data=data)
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

    def save_album(
        self, tokens: Dict[str, Any], album_id: str
    ) -> Dict[str, Any]:
        url = f"{self._base_url}/v1/me/albums"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {tokens['access_token']}",
        }
        data = {"ids": [album_id]}

        try:
            response = requests.put(url, headers=headers, json=data)
            if response.status_code == 401:
                print("refreshing tokens...")
                tokens["access_token"] = self.refresh_access_token(
                    tokens["refresh_token"]
                )
                return self.save_album(tokens, album_id)
            response.raise_for_status()

            return {"status": "success", "message": "Album saved successfully"}
        except requests.exceptions.HTTPError as err:
            raise err

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
        current_user["id"] = response.json().get("id")
        current_user["display_name"] = response.json().get("display_name")
        current_user["email"] = response.json().get("email")
        current_user["country"] = response.json().get("country")
        current_user["image_url"] = (
            response.json().get("images")[-1].get("url")
            if response.json().get("images")
            else None
        )
        return current_user

    def get_recently_played(
        self,
        token: str,
        url: Optional[str] = None,
        after: Optional[int] = None,
        limit: Optional[int] = 50,
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
        recently_played_tracks.reverse()
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

    def get_albums_info(
        self, token: str, album_ids: List[str]
    ) -> Dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        params = {"ids": ",".join(album_ids)}
        url = f"{self._base_url}/v1/albums"
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        if not response.json().get("albums"):
            return {"message": "IDs corresponding to no albums"}
        results = {}
        albums = []
        for album in response.json().get("albums"):
            albums.append(
                {
                    "spotify_id": album.get("id"),
                    "artist_id": album.get("artists")[0].get("id"),
                    "genres": " - ".join(album.get("genres")),
                    "image_url": album.get("images")[0].get("url"),
                    "label": album.get("label"),
                    "name": album.get("name"),
                    "popularity": album.get("popularity"),
                    "release_date": album.get("release_date"),
                    "total_tracks": album.get("total_tracks"),
                }
            )
        results["albums"] = albums
        return results

    def get_artists_info(
        self, token: str, artist_ids: List[str]
    ) -> Dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        params = {"ids": ",".join(artist_ids)}
        url = f"{self._base_url}/v1/artists"
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        if not response.json().get("artists"):
            return {"message": "IDs corresponding to no artists"}
        results = {}
        artists = []
        for artist in response.json().get("artists"):
            artists.append(
                {
                    "spotify_id": artist.get("id"),
                    "genres": " - ".join(artist.get("genres")),
                    "image_url": (
                        artist.get("images")[0].get("url")
                        if artist.get("images")
                        else None
                    ),
                    "name": artist.get("name"),
                    "followers": artist.get("followers").get("total"),
                    "popularity": artist.get("popularity"),
                }
            )
        results["artists"] = artists
        return results

    def get_user_saved_albums_limit(
        self,
        tokens: Dict[str, Any],
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {tokens['access_token']}",
        }
        params = {"limit": limit, "offset": offset}
        url = f"{self._base_url}/v1/me/albums"
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 401:
                tokens["access_token"] = self.refresh_access_token(
                    tokens["refresh_token"]
                )
                return self.get_user_saved_albums_limit(tokens, limit, offset)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"Error get user_saved_album: {err}")
            raise SystemExit(err)
        results = {}
        albums = []
        if response.json().get("items"):
            for item in response.json().get("items"):
                single_album = {
                    "spotify_id": item.get("album").get("id"),
                    "type": item.get("album").get("album_type"),
                    "artist_spotify_id": item.get("album")
                    .get("artists")[0]
                    .get("id"),
                    "artist_name": item.get("album")
                    .get("artists")[0]
                    .get("name"),
                    "upc_id": item.get("album").get("external_ids").get("upc"),
                    "label": item.get("album").get("label"),
                    "name": item.get("album").get("name"),
                    "release_date": item.get("album").get("release_date"),
                    "image_url": item.get("album").get("images")[0].get("url"),
                    "genres": " - ".join(item.get("album").get("genres")),
                    "total_tracks": item.get("album").get("total_tracks"),
                    "popularity": item.get("album").get("popularity"),
                    "created_at": datetime.now(),
                    "added_at": item.get("added_at"),
                }

                albums.append(single_album)
        results["albums"] = albums
        results["total_albums"] = response.json().get("total")
        return results

    def get_user_saved_albums(
        self, token: str, user_spotify_id: str
    ) -> Dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        params = {"limit": 50, "offset": 0}
        url = f"{self._base_url}/v1/me/albums"
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        results = {}
        albums = []
        user_albums = []
        if response.json().get("next"):
            while response.json().get("next"):
                response = requests.get(url, headers=headers)
                if response.json().get("items"):
                    for item in response.json().get("items"):
                        single_album = {
                            "spotify_id": item.get("album").get("id"),
                            "type": item.get("album").get("album_type"),
                            "artist_spotify_id": item.get("album")
                            .get("artists")[0]
                            .get("id"),
                            "artist_name": item.get("album")
                            .get("artists")[0]
                            .get("name"),
                            "upc_id": item.get("album")
                            .get("external_ids")
                            .get("upc"),
                            "label": item.get("album").get("label"),
                            "name": item.get("album").get("name"),
                            "release_date": item.get("album").get(
                                "release_date"
                            ),
                            "image_url": item.get("album")
                            .get("images")[0]
                            .get("url"),
                            "genres": " - ".join(
                                item.get("album").get("genres")
                            ),
                            "total_tracks": item.get("album").get(
                                "total_tracks"
                            ),
                            "popularity": item.get("album").get("popularity"),
                            "created_at": datetime.now(),
                        }
                        single_user_album = {
                            "user_spotify_id": user_spotify_id,
                            "album_spotify_id": item.get("album").get("id"),
                            "added_at": item.get("added_at"),
                            "created_at": datetime.now(),
                        }
                        albums.append(single_album)
                        user_albums.append(single_user_album)
                    url = response.json().get("next")
        else:
            for item in response.json().get("items"):
                single_album = {
                    "spotify_id": item.get("album").get("id"),
                    "type": item.get("album").get("album_type"),
                    "artist_spotify_id": item.get("album")
                    .get("artists")[0]
                    .get("id"),
                    "artist_name": item.get("album")
                    .get("artists")[0]
                    .get("name"),
                    "upc_id": item.get("album").get("external_ids").get("upc"),
                    "label": item.get("album").get("label"),
                    "name": item.get("album").get("name"),
                    "release_date": item.get("album").get("release_date"),
                    "image_url": item.get("album").get("images")[0].get("url"),
                    "genres": " - ".join(item.get("album").get("genres")),
                    "total_tracks": item.get("album").get("total_tracks"),
                    "popularity": item.get("album").get("popularity"),
                    "created_at": datetime.now(),
                }
                single_user_album = {
                    "user_spotify_id": user_spotify_id,
                    "album_spotify_id": item.get("album").get("id"),
                    "added_at": item.get("added_at"),
                    "created_at": datetime.now(),
                }
                albums.append(single_album)
                user_albums.append(single_user_album)
        results["albums"] = albums
        results["user_albums"] = user_albums
        return results
