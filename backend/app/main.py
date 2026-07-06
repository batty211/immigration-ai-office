from fastapi import FastAPI

app = FastAPI(title="Immigration AI Office Backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

