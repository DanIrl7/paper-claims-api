import os

from fastapi import FastAPI, HTTPException, Query

from app.schemas import Claim, ClaimIn, Paper, PaperIn
from app.store import Store


def create_app(db_path: str | None = None) -> FastAPI:
    """Build the app. Use the factory form so tests can give each app its own database file.

    Run it with: uvicorn app.main:create_app --factory
    """
    store = Store(db_path or os.environ.get("CLAIMS_DB", "claims.db"))
    app = FastAPI(title="Paper Claims API", version="1.0.0")
    app.state.store = store

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/papers", response_model=Paper, status_code=201)
    def create_paper(body: PaperIn) -> dict:
        return store.create_paper(body)

    @app.get("/papers", response_model=list[Paper])
    def list_papers(
        year: int | None = Query(default=None, ge=1900, le=2100),
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> list[dict]:
        return store.list_papers(year, limit, offset)

    @app.get("/papers/{paper_id}", response_model=Paper)
    def get_paper(paper_id: int) -> dict:
        paper = store.get_paper(paper_id)
        if paper is None:
            raise HTTPException(status_code=404, detail="paper not found")
        return paper

    @app.post("/papers/{paper_id}/claims", response_model=Claim, status_code=201)
    def add_claim(paper_id: int, body: ClaimIn) -> dict:
        claim = store.add_claim(paper_id, body)
        if claim is None:
            raise HTTPException(status_code=404, detail="paper not found")
        return claim

    @app.get("/papers/{paper_id}/claims", response_model=list[Claim])
    def list_claims(paper_id: int) -> list[dict]:
        claims = store.list_claims(paper_id)
        if claims is None:
            raise HTTPException(status_code=404, detail="paper not found")
        return claims

    return app
