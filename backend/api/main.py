from fastapi import FastAPI

app = FastAPI(
    title="Nazar API",
    description="Performance monitoring platform API",
    version="0.1.0"
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
