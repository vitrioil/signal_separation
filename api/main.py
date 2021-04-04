from fastapi import FastAPI
from starlette.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from api.routers import augment, signal
from api.db import connect_to_mongo, close_mongo_connection


# app = FastAPI(dependencies=[Depends(get_query_token)])
api = FastAPI()
origins = [
    "http://localhost:3000",
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


api.add_event_handler("startup", connect_to_mongo)
api.add_event_handler("shutdown", close_mongo_connection)

api.include_router(augment)
api.include_router(signal)


@api.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


@api.get("/sample/{file_name}")
async def main(file_name: str):
    response = FileResponse(f"static/{file_name}")
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(api)
