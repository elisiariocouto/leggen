"""Pydantic models for category endpoints."""

from typing import Literal

from pydantic import BaseModel


class Category(BaseModel):
    """Category model."""

    id: int
    name: str
    color: str = "#6b7280"
    icon: str | None = None
    is_default: bool = False
    exclude_from_stats: bool = False


class CategoryCreate(BaseModel):
    """Model for creating a category."""

    name: str
    color: str = "#6b7280"
    icon: str | None = None
    exclude_from_stats: bool = False


class CategoryUpdate(BaseModel):
    """Model for updating a category."""

    name: str | None = None
    color: str | None = None
    icon: str | None = None
    exclude_from_stats: bool | None = None


class CategoryAssignment(BaseModel):
    """Model for assigning a category to a transaction."""

    category_id: int


class BulkCategoryAssignment(BaseModel):
    """Model for bulk-assigning a category by transaction description."""

    category_id: int
    description: str


class BulkCategoryRemoval(BaseModel):
    """Model for bulk-removing categories by transaction description."""

    description: str


class CategorySuggestion(BaseModel):
    """Model for a category suggestion."""

    category: Category
    score: float
    confidence: Literal["high", "medium", "low"]
