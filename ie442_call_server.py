import httpx
import asyncio

async def call_api_endpoint():
    url = "https://www.google.com"
    api_url = "http://localhost:8000/fetch_url_response?url=" + url

    async with httpx.AsyncClient() as client:
        response = await client.get(api_url)

    if response.status_code == 200:
        data = response.json()
        print("Status Code:", data["status_code"])
        print("Response Content:")
        print(data["content"])
    else:
        print("Error:", response.status_code)

if __name__ == "__main__":
    asyncio.run(call_api_endpoint())