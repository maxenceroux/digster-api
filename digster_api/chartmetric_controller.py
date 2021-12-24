from typing import Any, Dict

import requests


class ChartmetricController:
    def __init__(self) -> None:
        self._base_url = "https://api.chartmetric.com"

    def find_artist_cm_id(self, cookie: str, spotify_id: str):
        url = f"{self._base_url}/search/suggestion"
        params: Dict[str, Any] = {
            "limit": 10,
            "offset": 0,
            "type": "artists",
            "q": f"spotify:artist:{spotify_id}",
        }
        cookies = {"connect.sid": cookie}
        try:
            response = requests.get(url, params=params, cookies=cookies)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        return (
            str(response.json().get("obj").get("artists")[0].get("id"))
            if response.json().get("obj")
            else None
        )

    def get_artist_spotify_playlist(
        self,
        cookie: str,
        cm_id: str,
        from_days_ago: int = 365,
        to_days_ago: int = 0,
        offset: int = 0,
        limit: int = 200,
    ):
        url = f"{self._base_url}/playlist/spotify/by/artist/current"
        params: Dict[str, Any] = {
            "fromDaysAgo": from_days_ago,
            "toDaysAgo": to_days_ago,
            "offset": offset,
            "limit": limit,
            "sortBy": "added_at",
            "ids[]": cm_id,
            "sortDirection": "descending",
        }
        cookies = {"connect.sid": cookie}
        try:
            response = requests.get(url, params=params, cookies=cookies)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        print(response.json())
