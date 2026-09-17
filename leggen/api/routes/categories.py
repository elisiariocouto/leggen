"""API routes for transaction categorization."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from leggen.api.models.categories import (
    BulkCategoryAssignment,
    BulkCategoryRemoval,
    Category,
    CategoryAssignment,
    CategoryCreate,
    CategoryUpdate,
)
from leggen.repositories.category_repository import CategoryRepository

router = APIRouter()


# --- Category CRUD ---


@router.get("/categories", response_model=list[Category])
async def get_categories(
    category_repo: Annotated[CategoryRepository, Depends()],
) -> list[Category]:
    """Get all categories."""
    categories = category_repo.get_all_categories()
    return [Category(**cat) for cat in categories]


@router.post("/categories", response_model=Category, status_code=201)
async def create_category(
    body: CategoryCreate,
    category_repo: Annotated[CategoryRepository, Depends()],
) -> Category:
    """Create a new custom category.

    A duplicate name raises CategoryExistsError from the repository, which the
    exception handlers render as a 409.
    """
    cat = category_repo.create_category(
        name=body.name,
        color=body.color,
        icon=body.icon,
        exclude_from_stats=body.exclude_from_stats,
    )
    return Category(**cat)


@router.put("/categories/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    body: CategoryUpdate,
    category_repo: Annotated[CategoryRepository, Depends()],
) -> Category:
    """Update a category."""
    cat = category_repo.update_category(
        category_id=category_id,
        name=body.name,
        color=body.color,
        icon=body.icon,
        exclude_from_stats=body.exclude_from_stats,
    )
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    return Category(**cat)


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    category_repo: Annotated[CategoryRepository, Depends()],
) -> None:
    """Delete a custom category."""
    deleted = category_repo.delete_category(category_id)
    if not deleted:
        raise HTTPException(
            status_code=400,
            detail="Category not found or is a default category.",
        )


# --- Transaction category assignment ---


@router.put("/transactions/bulk-categorize")
async def bulk_categorize_transactions(
    body: BulkCategoryAssignment,
    category_repo: Annotated[CategoryRepository, Depends()],
) -> dict[str, Any]:
    """Assign a category to all transactions matching a description."""
    cat = category_repo.get_category_by_id(body.category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")

    updated_count = category_repo.bulk_assign_by_description(
        category_id=body.category_id,
        description=body.description,
    )
    return {"status": "ok", "updated_count": updated_count}


@router.delete("/transactions/bulk-categorize")
async def bulk_remove_transaction_categories(
    body: BulkCategoryRemoval,
    category_repo: Annotated[CategoryRepository, Depends()],
) -> dict[str, Any]:
    """Remove category from all transactions matching a description."""
    removed_count = category_repo.bulk_remove_by_description(
        description=body.description,
    )
    return {"status": "ok", "removed_count": removed_count}


@router.put("/transactions/{account_id}/{transaction_id}/category")
async def assign_transaction_category(
    account_id: str,
    transaction_id: str,
    body: CategoryAssignment,
    category_repo: Annotated[CategoryRepository, Depends()],
) -> dict[str, str]:
    """Assign a category to a transaction by hand. A manual category is
    never changed by the rule engine."""
    cat = category_repo.get_category_by_id(body.category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    category_repo.assign_category(account_id, transaction_id, body.category_id)
    return {"status": "ok"}


@router.delete("/transactions/{account_id}/{transaction_id}/category")
async def remove_transaction_category(
    account_id: str,
    transaction_id: str,
    category_repo: Annotated[CategoryRepository, Depends()],
) -> dict[str, str]:
    """Remove a transaction's category."""
    if not category_repo.remove_category(account_id, transaction_id):
        raise HTTPException(status_code=404, detail="No category assignment found.")
    return {"status": "ok"}
