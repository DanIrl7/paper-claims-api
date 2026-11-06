import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c
    app.state.store.close()


def new_paper(client, title="A study of sleep", year=2021, doi=None):
    body = {"title": title, "year": year}
    if doi is not None:
        body["doi"] = doi
    response = client.post("/papers", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_paper_returns_saved_fields(client):
    paper = new_paper(client, doi="10.1000/xyz123")
    assert paper["id"] > 0
    assert paper["title"] == "A study of sleep"
    assert paper["year"] == 2021
    assert paper["doi"] == "10.1000/xyz123"


def test_title_is_trimmed_and_blank_title_is_rejected(client):
    assert new_paper(client, title="   Padded title   ")["title"] == "Padded title"
    response = client.post("/papers", json={"title": "   ", "year": 2020})
    assert response.status_code == 422


@pytest.mark.parametrize("year", [1899, 2101, "not a year"])
def test_invalid_year_is_rejected(client, year):
    response = client.post("/papers", json={"title": "x", "year": year})
    assert response.status_code == 422


def test_missing_paper_returns_404(client):
    response = client.get("/papers/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "paper not found"


def test_list_papers_filters_by_year_and_paginates(client):
    new_paper(client, title="One", year=2020)
    new_paper(client, title="Two", year=2021)
    new_paper(client, title="Three", year=2021)

    only_2021 = client.get("/papers", params={"year": 2021}).json()
    assert [p["title"] for p in only_2021] == ["Two", "Three"]

    page = client.get("/papers", params={"limit": 1, "offset": 1}).json()
    assert [p["title"] for p in page] == ["Two"]


def test_limit_above_100_is_rejected(client):
    assert client.get("/papers", params={"limit": 101}).status_code == 422


def test_add_and_list_claims(client):
    paper = new_paper(client)
    claim_body = {"text": "Short sleep raises stress.", "evidence": "Table 2, n=340", "confidence": 0.8}

    created = client.post(f"/papers/{paper['id']}/claims", json=claim_body)
    assert created.status_code == 201
    claim = created.json()
    assert claim["paper_id"] == paper["id"]
    assert claim["confidence"] == 0.8

    listed = client.get(f"/papers/{paper['id']}/claims").json()
    assert [c["text"] for c in listed] == ["Short sleep raises stress."]


def test_claim_on_missing_paper_returns_404(client):
    response = client.post(
        "/papers/9999/claims", json={"text": "x", "evidence": "y", "confidence": 0.5}
    )
    assert response.status_code == 404


def test_list_claims_for_missing_paper_returns_404(client):
    assert client.get("/papers/9999/claims").status_code == 404


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_confidence_must_be_between_0_and_1(client, confidence):
    paper = new_paper(client)
    response = client.post(
        f"/papers/{paper['id']}/claims",
        json={"text": "x", "evidence": "y", "confidence": confidence},
    )
    assert response.status_code == 422


def test_data_persists_across_app_instances(tmp_path):
    db = str(tmp_path / "persist.db")
    first = create_app(db)
    with TestClient(first) as c:
        c.post("/papers", json={"title": "Kept", "year": 2022})
    first.state.store.close()

    second = create_app(db)
    with TestClient(second) as c:
        assert [p["title"] for p in c.get("/papers").json()] == ["Kept"]
    second.state.store.close()
