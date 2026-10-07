"""Request and response models.

Money rule: amounts are stored and transported as integers in the smallest
currency unit. No float ever touches an amount. A float amount is a defect,
not a style preference.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ScholarshipIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    amount_minor: int = Field(ge=0, description="Smallest currency unit, integer")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    gpa_minimum: float = Field(ge=0.0, le=4.0)
    country: str = Field(min_length=2, max_length=2)
    deadline_utc: datetime

    @field_validator("amount_minor", mode="before")
    @classmethod
    def reject_float_amounts(cls, v: object) -> object:
        if isinstance(v, float) and not float(v).is_integer():
            raise ValueError(
                "amount_minor must be an integer in the smallest currency unit; "
                f"got the float {v!r}. Money is never a float here."
            )
        return v


class Scholarship(BaseModel):
    id: int
    name: str
    amount_minor: int
    currency: str
    gpa_minimum: float
    country: str
    deadline_utc: datetime


class Page(BaseModel):
    items: list[Scholarship]
    page: int
    size: int
    total: int
    pages: int


class ApplicationIn(BaseModel):
    scholarship_id: int
    applicant_id: str = Field(min_length=1, max_length=64)
    applicant_name: str = Field(min_length=1, max_length=200)
    gpa: float | None = Field(default=None, ge=0.0, le=4.0)
    country: str = Field(min_length=2, max_length=2)


class Application(BaseModel):
    id: int
    scholarship_id: int
    applicant_id: str
    applicant_name: str
    gpa: float | None
    country: str


class Eligibility(BaseModel):
    scholarship_id: int
    eligible: bool
    reasons: list[str]
