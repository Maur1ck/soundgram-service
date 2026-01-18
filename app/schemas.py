from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class PlaylistRequest(BaseModel):
    url: HttpUrl


class TrackInfo(BaseModel):
    title: str
    authors: List[str]
    cover_url: Optional[str]
    iframe_html: str


class PlaylistResponse(BaseModel):
    title: str
    owner: str
    tracks: List[TrackInfo]
