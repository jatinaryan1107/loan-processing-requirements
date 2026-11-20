"""Validated request bodies for the public API."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(Model):
    role: Literal["ba", "compliance", "pm", "developer"]


class ProjectInput(Model):
    name: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=4000)
    jurisdiction: str = Field(default="Not specified", min_length=2, max_length=100)


class SourceInput(Model):
    text: str = Field(min_length=12, max_length=100000)
    source_name: str = Field(min_length=2, max_length=200)
    stakeholder: str = Field(default="Business Analyst", min_length=2, max_length=100)

    @field_validator("text")
    @classmethod
    def clean(cls, value):
        if "\x00" in value:
            raise ValueError("NUL characters are not supported")
        return value


class AnalyseInput(Model):
    use_llm: bool = False


class RequirementEdit(Model):
    statement: str | None = Field(default=None, min_length=12, max_length=5000)
    priority: Literal["Must", "Should", "Could"] | None = None
    acceptance_criteria: list[str] | None = Field(default=None, min_length=1, max_length=10)
    justification: str | None = Field(default=None, min_length=3, max_length=2000)

    @field_validator("acceptance_criteria")
    @classmethod
    def criteria(cls, value):
        if value is not None and any(not x.strip() or len(x) > 3000 for x in value):
            raise ValueError("Criteria must contain 1–3000 characters")
        return value


class Review(Model):
    decision: Literal["approved", "rejected"]
    note: str = Field(min_length=3, max_length=2000)


class MappingReview(Review):
    interpretation: str | None = Field(default=None, min_length=3, max_length=3000)


class Answer(Model):
    answer: str = Field(min_length=3, max_length=10000)


class ExcludeSource(Model):
    note: str = Field(min_length=3, max_length=2000)


class Factors(Model):
    stability: int = Field(ge=1, le=5, strict=True)
    complexity: int = Field(ge=1, le=5, strict=True)
    regulatory: int = Field(ge=1, le=5, strict=True)
    security: int = Field(ge=1, le=5, strict=True)
    stakeholders: int = Field(ge=1, le=5, strict=True)
    change: int = Field(ge=1, le=5, strict=True)
    legacy: int = Field(ge=1, le=5, strict=True)
    testing: int = Field(ge=1, le=5, strict=True)
    cadence: int = Field(ge=1, le=5, strict=True)


class SdlcInput(Model):
    factors: Factors


class SdlcDecision(Review):
    model: str = Field(min_length=2, max_length=80)
