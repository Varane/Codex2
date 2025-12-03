from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import requests, vehicles

app = FastAPI(title="Sonver Auto Parts")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehicles.router)
app.include_router(requests.router)


@app.get("/")
def read_root():
    return {"status": "ok"}
