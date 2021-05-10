from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import augment, signal, auth
from api.db import connect_to_mongo, close_mongo_connection


tags_metadata = [
    {
        "name": "signal",
        "description": (
            "Signal can be an audio file. "
            "On posting, background process will "
            "initiate signal separation. "
            "Depending upon the signal type different "
            "separator can be used."
        ),
    }
]

api = FastAPI(openapi_tags=tags_metadata, title="Signal Separation API")
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
api.include_router(auth)
api.include_router(signal)


@api.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(api)
