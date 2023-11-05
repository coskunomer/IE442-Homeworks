# API Endpoint for Web Scraping

This Python script demonstrates how to make an asynchronous HTTP request to an API endpoint and retrieve its response using the HTTPX library. The code sends a GET request to a specified API endpoint that fetches the content of a given URL.

## Prerequisites

Before running the code, make sure you have the following prerequisites installed:

- Python 3.x
- HTTPX library (can be installed using `pip install httpx`)

## Running the Code

1. Start the API server using Uvicorn. Open your terminal and run the following command:

   ```shell
   uvicorn ie442_server:app --reload
   
This will start the server on http://localhost:8000.

You can now use one of the following methods to call the API endpoint:

## Make a request to server

### Method 1: Using curl

Open your terminal and run the following cURL command:

```shell
   curl "http://localhost:8000/fetch_url_response?url=https://www.google.com"
```

### Method 2: Using the Provided Python Script:

Run the Python script ie442_call_server.py from your terminal:

```shell
   python ie442_call_server.py
```
Make sure that ie442_call_server.py is in the current working directory.
