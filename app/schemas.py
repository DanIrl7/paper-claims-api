from pydantic import BaseModel, Field, field_validator


class PaperIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    doi: str | None = Field(default=None, max_length=200)
    year: int = Field(ge=1900, le=2100)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class Paper(PaperIn):
    id: int


class ClaimIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    evidence: str = Field(min_length=1, max_length=2000)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("text", "evidence")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class Claim(ClaimIn):
    id: int
    paper_id: int
