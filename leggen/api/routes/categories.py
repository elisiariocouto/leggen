"""API routes for transaction categorization."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from leggen.api.models.categories import (
    Category,
    CategoryAssignment,
    CategoryCreate,
    CategorySuggestion,
    CategoryUpdate,
)
from leggen.repositories.category_repository import CategoryRepository
from leggen.repositories.transaction_repository import TransactionRepository

router = APIRouter()


# --- Category CRUD ---


@router.get("/categories", response_model=list[Category])
async def get_categories(
    category_repo: Annotated[CategoryRepository, Depends()],
) -> list[Category]:
    """Get all categories."""
    try:
        categories = category_repo.get_all_categories()
        return [Category(**cat) for cat in categories]
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get categories: {e}"
        ) from e


@router.post("/categories", response_model=Category, status_code=201)
async def create_category(
    body: CategoryCreate,
    category_repo: Annotated[CategoryRepository, Depends()],
) -> Category:
    """Create a new custom category."""
    try:
        cat = category_repo.create_category(
            name=body.name, color=body.color, icon=body.icon
        )
        return Category(**cat)
    except Exception as e:
        logger.error(f"Failed to create category: {e}")
        if "UNIQUE constraint" in str(e):
            raise HTTPException(
                status_code=409, detail=f"Category '{body.name}' already exists."
            ) from e
        raise HTTPException(
            status_code=500, detail=f"Failed to create category: {e}"
        ) from e


@router.put("/categories/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    body: CategoryUpdate,
    category_repo: Annotated[CategoryRepository, Depends()],
) -> Category:
    """Update a category."""
    try:
        cat = category_repo.update_category(
            category_id=category_id,
            name=body.name,
            color=body.color,
            icon=body.icon,
        )
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found.")
        return Category(**cat)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update category: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update category: {e}"
        ) from e


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    category_repo: Annotated[CategoryRepository, Depends()],
) -> None:
    """Delete a custom category."""
    try:
        deleted = category_repo.delete_category(category_id)
        if not deleted:
            raise HTTPException(
                status_code=400,
                detail="Category not found or is a default category.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete category: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete category: {e}"
        ) from e


# --- Transaction category assignment ---


@router.put("/transactions/{account_id}/{transaction_id}/category")
async def assign_transaction_category(
    account_id: str,
    transaction_id: str,
    body: CategoryAssignment,
    category_repo: Annotated[CategoryRepository, Depends()],
    transaction_repo: Annotated[TransactionRepository, Depends()],
) -> dict[str, str]:
    """Assign a category to a transaction."""
    try:
        # Verify category exists
        cat = category_repo.get_category_by_id(body.category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found.")

        # Get transaction text fields for keyword learning
        transactions = transaction_repo.get_transactions(
            account_id=account_id, limit=1, offset=0
        )
        description = ""
        creditor_name = ""
        debtor_name = ""
        for txn in transactions:
            if txn["transactionId"] == transaction_id:
                description = txn.get("description", "")
                raw = txn.get("rawTransaction", {})
                creditor_name = raw.get("creditorName", "")
                debtor_name = raw.get("debtorName", "")
                break

        category_repo.assign_category(
            account_id=account_id,
            transaction_id=transaction_id,
            category_id=body.category_id,
            description=description,
            creditor_name=creditor_name,
            debtor_name=debtor_name,
        )
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign category: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to assign category: {e}"
        ) from e


@router.delete("/transactions/{account_id}/{transaction_id}/category")
async def remove_transaction_category(
    account_id: str,
    transaction_id: str,
    category_repo: Annotated[CategoryRepository, Depends()],
    transaction_repo: Annotated[TransactionRepository, Depends()],
) -> dict[str, str]:
    """Remove category from a transaction."""
    try:
        # Get transaction text fields for keyword unlearning
        transactions = transaction_repo.get_transactions(
            account_id=account_id, limit=1, offset=0
        )
        description = ""
        creditor_name = ""
        debtor_name = ""
        for txn in transactions:
            if txn["transactionId"] == transaction_id:
                description = txn.get("description", "")
                raw = txn.get("rawTransaction", {})
                creditor_name = raw.get("creditorName", "")
                debtor_name = raw.get("debtorName", "")
                break

        removed = category_repo.remove_category(
            account_id=account_id,
            transaction_id=transaction_id,
            description=description,
            creditor_name=creditor_name,
            debtor_name=debtor_name,
        )
        if not removed:
            raise HTTPException(status_code=404, detail="No category assignment found.")
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove category: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to remove category: {e}"
        ) from e


@router.get(
    "/transactions/{account_id}/{transaction_id}/suggest-category",
    response_model=list[CategorySuggestion],
)
async def suggest_transaction_category(
    account_id: str,
    transaction_id: str,
    category_repo: Annotated[CategoryRepository, Depends()],
    transaction_repo: Annotated[TransactionRepository, Depends()],
) -> list[CategorySuggestion]:
    """Get category suggestions for a transaction."""
    try:
        # Get transaction text fields
        transactions = transaction_repo.get_transactions(
            account_id=account_id, limit=1, offset=0
        )
        description = ""
        creditor_name = ""
        debtor_name = ""
        for txn in transactions:
            if txn["transactionId"] == transaction_id:
                description = txn.get("description", "")
                raw = txn.get("rawTransaction", {})
                creditor_name = raw.get("creditorName", "")
                debtor_name = raw.get("debtorName", "")
                break

        suggestions = category_repo.suggest_category(
            description=description,
            creditor_name=creditor_name,
            debtor_name=debtor_name,
        )
        return [
            CategorySuggestion(
                category=Category(**s["category"]),
                score=s["score"],
                confidence=s["confidence"],
            )
            for s in suggestions
        ]
    except Exception as e:
        logger.error(f"Failed to get category suggestions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get category suggestions: {e}"
        ) from e
