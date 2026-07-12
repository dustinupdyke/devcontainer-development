"""Pydantic request and response models for the URL shortener API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ShortenRequest(BaseModel):
    """Payload for creating a short link."""

    url: HttpUrl = Field(
        ...,
        description="The absolute http(s) URL to shorten.",
        examples=["https://www.example.com/some/very/long/path?ref=newsletter"],
    )


class ShortenResponse(BaseModel):
    """Details of a newly created (or reused) short link."""

    code: str = Field(
        ...,
        description="The short code identifying the link.",
        examples=["3"],
    )
    short_url: str = Field(
        ...,
        description="The fully qualified short URL that redirects to the target.",
        examples=["http://localhost:8000/3"],
    )
    target_url: str = Field(
        ...,
        description="The original URL the short link redirects to.",
        examples=["https://www.example.com/some/very/long/path?ref=newsletter"],
    )


class StatsResponse(BaseModel):
    """Usage statistics for a short link."""

    code: str = Field(..., description="The short code.", examples=["3"])
    target_url: str = Field(
        ...,
        description="The original URL the short link redirects to.",
        examples=["https://www.example.com/"],
    )
    hits: int = Field(
        ...,
        description="Number of times the short link has been resolved.",
        examples=[42],
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp when the link was created.",
    )


class HealthResponse(BaseModel):
    """Liveness response."""

    status: str = Field(
        ...,
        description="Always 'ok' when the service is healthy.",
        examples=["ok"],
    )
    links: int = Field(
        ...,
        description="Number of short links currently stored.",
        examples=[7],
    )
