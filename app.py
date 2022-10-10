import logging

import docker
import uvicorn
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse


async def error_to_json(request: Request, exc: HTTPException):
    return JSONResponse(
        {"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers
    )


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["http://girder", "http://localhost:8001"],
    )
]
exception_handlers = {404: error_to_json, 400: error_to_json}
app = Starlette(
    debug=False, middleware=middleware, exception_handlers=exception_handlers
)
docker_client = docker.from_env(version="1.28")


@app.route("/")
async def get_log(request):
    if not request.query_params.get("name"):
        raise HTTPException(
            status_code=400,
            detail="Missing 'name' parameter",
        )

    try:
        tail = request.query_params.get("tail") or 200
        if tail != "all":
            tail = int(tail)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Parameter 'tail' has to be int or string 'all'"
        )

    service_name = request.query_params.get("name")
    try:
        service = docker_client.services.get(service_name)
    except docker.errors.NotFound:
        raise HTTPException(
            status_code=404,
            detail=f"Service {service_name} doesn't exist",
        )

    logs = service.logs(stdout=True, stderr=True, tail=tail)
    return StreamingResponse(logs, media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
