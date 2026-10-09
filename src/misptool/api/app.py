from fastapi import FastAPI

from src.misptool.api.routes import router


app = FastAPI(title="MISP Tool API")

app.include_router(router)