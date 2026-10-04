from fastapi import FastAPI

from app.routers import supplier, product, shipping_route, listing, readonly

app = FastAPI(title="AI Amazon Commerce Manager")

app.include_router(supplier.router)
app.include_router(product.router)
app.include_router(shipping_route.router)
app.include_router(listing.router)
app.include_router(readonly.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}