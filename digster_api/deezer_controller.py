import requests
from datetime import datetime


class DeezerController:
    def __init__(self) -> None:
        self._base_url = "https://api.deezer.com"
        pass

    def get_album_info(self, album_id: int):
        url = f"{self._base_url}/album/{album_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        data = response.json()
        return {
            "deezer_id": data["id"],
            "deezer_artist_id": data["artist"]["id"],
            "artist_name": data["artist"]["name"],
            "upc_id": data["upc"],
            "label": data["label"],
            "name": data["title"],
            "release_date": data["release_date"],
            "image_url": data["cover_big"],
            "total_tracks": data["nb_tracks"],
        }

    def get_user_saved_albums(
        self, user_id: int, offset: int = 0, limit: int = 25
    ):
        url = f"{self._base_url}/user/{user_id}/albums?index={offset}"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        results = {}
        albums = []
        if response.json().get("data"):
            for item in response.json().get("data"):
                try:
                    album = self.get_album_info(item["id"])
                except:
                    continue
                album["created_at"] = datetime.now()
                album["added_at"] = datetime.fromtimestamp(item["time_add"])
                albums.append(album)
        results["albums"] = albums
        results["total_albums"] = response.json().get("total")
        return results
