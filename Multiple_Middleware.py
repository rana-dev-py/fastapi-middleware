
## special note 
"""
When a request is received, each middleware processes the request in a specific order until it reaches the endpoint.
Once the endpoint handler (like your /secure-data route) is called and processed, the response flows back through the middlewares in reverse order.

Each middleware function calls await call_next(request), which hands over control to the next middleware or the endpoint.
When the final middleware in the stack calls await call_next(request), the request reaches the endpoint.
The endpoint processes the request only once and produces a response.
This response is then sent back up the middleware chain in reverse order (from the last middleware back to the first).
"""
import time
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
# from fastapi.security.api_key import APIKeyHeader #FastAPI provides the APIKeyHeader class to define API key authentication. This will tell Swagger to prompt for the X-Auth-Token header.

# Define a request model for data structure
class RequestData(BaseModel):
    name: str
    value: int
app = FastAPI()
# Define the API key header
# api_key_header = APIKeyHeader(name="X-Auth-Token", auto_error=False)

# Middleware 1: Measure processing time
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    print("in time middleware")
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Middleware 2: Check for an authentication header
@app.middleware("http")
async def check_authentication(request: Request, call_next):
    if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    auth_token = request.headers.get("X-Auth-Token")
    if auth_token != "my_secure_token":
        return JSONResponse(content="Unauthorized " , status_code=401)
    response = await call_next(request)
    return response

# Middleware 3: Log request method and URL
@app.middleware("http")
async def log_request_data(request: Request, call_next):
    print("in logs middleware")
    method = request.method
    url = str(request.url)
    print(f"Received request: {method} {url}")
    response = await call_next(request)
    return response

# Sample endpoint
@app.post("/test")
async def read_root():
    return {"message": "Welcome to FastAPI with multiple middlewares!"}

# Another endpoint to test middleware behavior

@app.post("/secure-data")
async def secure_data(request: Request, request_data: RequestData):
    try:
        # Main logic of the endpoint
        return {"data": "This is secure data only accessible with a valid auth token", "received_data": request_data.dict() , "X-Auth-Token": request.headers.get("X-Auth-Token")}
    except Exception as e:
        # Log the error for debugging (optional)
        print(f"An error occurred in /secure-data endpoint: {str(e)}")

        # Return a structured error response
        return JSONResponse(
            status_code=500,
            content={"error": "An error occurred while processing your request.", "details": str(e)}
        )
