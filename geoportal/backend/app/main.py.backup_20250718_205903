from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.database import engine, Base
from .api.endpoints import spatial, geometries
from .api.endpoints.statistics import router as statistics_router
from .api.endpoints.geometries import router as geometries_router
import logging

# Crear todas las tablas
Base.metadata.create_all(bind=engine)

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Geoportal API",
    description="API para el Geoportal PHI",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(spatial.router, prefix="/api", tags=["spatial"])
app.include_router(geometries_router, prefix="/api")
app.include_router(statistics_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Geoportal API is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Logging de rutas disponibles
@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando aplicación FastAPI")
    logger.info("Rutas registradas:")
    for route in app.routes:
        logger.info(f"{route.methods} {route.path}") 