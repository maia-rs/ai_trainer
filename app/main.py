import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import agente_router, dashboard_router, whatsapp_router

app = FastAPI(title="AITrainer API", version="1.0.0")
app.include_router(dashboard_router)
app.include_router(agente_router)
app.include_router(whatsapp_router)

# Arquivos estáticos da aplicação (logo, css, etc.)
_STATIC_PATH = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=_STATIC_PATH), name="static")

# Serve os GIFs e imagens do dataset de exercícios
_EXERCISES_DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "exercises-dataset"
)
app.mount(
    "/exercises",
    StaticFiles(directory=_EXERCISES_DATASET_PATH),
    name="exercises",
)


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}