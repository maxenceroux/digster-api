from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import discogs_client

load_dotenv()


class DiscogsController:
    def __init__(self, user_token: str) -> None:
        self.user_token = user_token
        self.client = discogs_client.Client(
            "my_user_agent/1.0", user_token=user_token
        )

    def get_album_genres(self, albums: List[Dict]):
        results = []
        for album in albums:
            print(album)
            try:
                query = f'{album["album_name"].replace(" ", "+")}+{album["artist_name"].replace(" ", "+")}'
                search = self.client.search(query, type="release")
                styles = search[0].styles
                genres = search[0].genres
                if styles is None:
                    styles = ""
                if genres is None:
                    genres = ""
                results.append(
                    {
                        "album_id": album["id"],
                        "genres": genres,
                        "styles": styles,
                    }
                )
            except:
                pass
        print(results)
        return results

    def get_album_genre(self, album_name: str, artist_name: str):
        try:
            query = f'{album_name.replace(" ", "+")}+{artist_name.replace(" ", "+")}'
            search = self.client.search(query, type="release")
            styles = search[0].styles
            genres = search[0].genres
            if styles is None:
                styles = ""
            if genres is None:
                genres = ""
            return {"genres": genres, "styles": styles}
        except:
            return {"genres": None, "styles": None}
