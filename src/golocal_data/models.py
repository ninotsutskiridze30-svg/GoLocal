"""Validated canonical values for future collectors and loaders."""
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .normalization import (CATEGORIES, normalize_currency, normalize_datetime,
    normalize_price, normalize_text, normalize_url)

PositiveId = Annotated[int, Field(strict=True, gt=0)]


class NormalizedEvent(BaseModel):
    """Strict canonical contract. Call normalization helpers before constructing.

    Text remains untrusted data; consumers must escape output and must never treat
    descriptions as instructions. No network, clock, database, or API calls occur.
    """
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    title: str
    description: str = ""
    category: str = "other"
    city_id: PositiveId
    venue_name: str
    start_time: datetime
    end_time: datetime | None = None
    price_min: Decimal | None = None
    price_max: Decimal | None = None
    currency: str | None = None
    source_id: PositiveId
    source_name: str
    source_url: str
    fetched_at: datetime
    external_id: str | None = None
    image_url: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)
    status: Literal["active", "expired", "cancelled"] = "active"

    @field_validator("title", "venue_name", "source_name", "external_id")
    @classmethod
    def text_fields(cls, value):
        return normalize_text(value) if value is not None else None

    @field_validator("description")
    @classmethod
    def description_text(cls, value):
        return normalize_text(value, required=False)

    @field_validator("source_url", "image_url")
    @classmethod
    def url_fields(cls, value):
        return normalize_url(value) if value is not None else None

    @field_validator("start_time", "end_time", "fetched_at")
    @classmethod
    def utc_fields(cls, value):
        return normalize_datetime(value) if value is not None else None

    @field_validator("price_min", "price_max")
    @classmethod
    def prices(cls, value):
        return normalize_price(value)

    @field_validator("currency")
    @classmethod
    def currency_code(cls, value):
        return normalize_currency(value)

    @field_validator("category")
    @classmethod
    def known_category(cls, value):
        if value not in CATEGORIES:
            raise ValueError("Category must be normalized first")
        return value

    @model_validator(mode="after")
    def consistent_fields(self):
        if self.end_time is not None and self.end_time < self.start_time:
            raise ValueError("end_time precedes start_time")
        if self.price_min is not None and self.price_max is not None and self.price_max < self.price_min:
            raise ValueError("price_max is below price_min")
        if (self.price_min is not None or self.price_max is not None) and self.currency is None:
            raise ValueError("Known price requires currency")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Coordinates must be supplied together")
        return self


def event_has_finished(event: NormalizedEvent, *, now: datetime) -> bool | None:
    """True when a known end is reached; None when no end is known.

    Does not change status or assume that a start time is an end time.
    """
    current = normalize_datetime(now)
    return event.end_time <= current if event.end_time is not None else None
