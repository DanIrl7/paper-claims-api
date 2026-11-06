# Paper Claims API

A small REST API for research papers and the claims made in them. Each claim has evidence and a confidence score (0 to 1).

Built with FastAPI and Pydantic, stored in SQLite, tested with pytest.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/papers` | Add a paper (`title`, `year`, optional `doi`) |
| GET | `/papers` | List papers, filter with `?year=`, paginate with `limit` and `offset` |
| GET | `/papers/{id}` | Get one paper |
| POST | `/papers/{id}/claims` | Add a claim (`text`, `evidence`, `confidence` from 0 to 1) |
| GET | `/papers/{id}/claims` | List a paper's claims |

Invalid input returns 422, and a missing paper returns 404.

## Run it

Use Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:create_app --factory --reload
```

Then open http://127.0.0.1:8000/docs for the interactive API docs. The database file defaults to `claims.db`. Set `CLAIMS_DB` to choose another path.

## Run the tests

```bash
python -m pytest -v
```

The tests use a separate temporary database for each test, so they never touch `claims.db`.
