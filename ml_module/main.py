from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static") 