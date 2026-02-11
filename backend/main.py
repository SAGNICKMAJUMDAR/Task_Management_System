from fastapi import FastAPI
from contextlib import asynccontextmanager
from setup import init_db, create_super_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await create_super_admin()
    yield


app = FastAPI(lifespan=lifespan)
