from fastapi import FastAPI

from app.routers import supplier

app = FastAPI(title="AI Amazon Commerce Manager")

app.include_router(supplier.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}