import pytest
import respx
from httpx import Response

MOCK_API_RESPONSE = {
    "result": {
        "title": "API Test Playlist",
        "owner": {"name": "API Tester"},
        "tracks": []
    }
}

@pytest.mark.asyncio
async def test_api_get_playlist_success(client):
    url_to_fetch = "https://music.yandex.ru/users/api_user/playlists/100"
    
    async with respx.mock:
        respx.route(host="music.yandex.ru").mock(
            return_value=Response(200, json=MOCK_API_RESPONSE)
        )
        
        response = await client.post("/playlist", json={"url": url_to_fetch})
        
        if response.status_code != 200:
             print(f"Failed with status {response.status_code}: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "API Test Playlist"

@pytest.mark.asyncio
async def test_api_get_playlist_invalid_url(client):
    response = await client.post("/playlist", json={"url": "not_a_url"})
    assert response.status_code == 422 

    response = await client.post("/playlist", json={"url": "https://google.com"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Неверный формат ссылки"

@pytest.mark.asyncio
async def test_api_service_unavailable(client):
    url_to_fetch = "https://music.yandex.ru/users/fail/playlists/500"
    
    async with respx.mock:
        respx.route(host="music.yandex.ru").mock(
            side_effect=Exception("Network Error")
        )
        
        response = await client.post("/playlist", json={"url": url_to_fetch})
        
        assert response.status_code == 503
        assert response.json()["detail"] == "Ошибка соединения с источником"
