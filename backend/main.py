from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import modules, runs, sources


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="compass_purple", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(modules.router, prefix="/modules", tags=["modules"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(sources.router, prefix="/sources", tags=["sources"])


@app.get("/health")
def health():
    return {"status": "ok"}
