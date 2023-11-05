from fastapi import FastAPI
import httpx
from bs4 import BeautifulSoup

app = FastAPI()

@app.get("/fetch_url_response")
async def fetch_url_response(url: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return {"status_code": response.status_code, "content": soup.prettify()}
    except httpx.HTTPError as e:
        return {"error": f"HTTP Error: {str(e)}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

