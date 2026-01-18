from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import httpx

from app.schemas import PlaylistRequest
from app.services import YandexMusicService


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(timeout=15.0) as client:
        app.state.http_client = client
        yield


app = FastAPI(title="Soundgram Playlists Service", lifespan=lifespan)


@app.post("/playlist")
async def get_playlist_info(data: PlaylistRequest, request: Request):
    return await YandexMusicService(request.app.state.http_client).get_playlist(data.url)
