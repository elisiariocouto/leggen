"""API routes for category rules: CRUD, authoring helpers and the engine."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response

from leggen.api.models.category_rules import (
    CategoryRule,
    CategoryRuleCreate,
    CategoryRuleUpdate,
    RuleChange,
    RuleErrors,
    RuleMatch,
    RulePreviewResponse,
    RuleReference,
    RuleRunReport,
    RuleScriptPreview,
    RuleScriptTest,
    RuleTestResult,
    SkippedRule,
)
from leggen.errors import NotFoundError
from leggen.repositories import CategoryRepository, CategoryRuleRepository
from leggen.services.rules import CategoryRuleEngine, RuleRuntime, reference

router = APIRouter()

# Column names differ from the API's snake_case; map the editable ones.
_FIELD_TO_COLUMN = {
    "name": "name",
    "description": "description",
    "category_id": "categoryId",
    "lua_script": "lua_script",
    "priority": "priority",
    "is_active": "is_active",
    "exclude_from_stats": "exclude_from_stats",
}

EXAMPLES: list[dict[str, Any]] = [
    {
        "title": "Merchant keyword",
        "lua_script": 'return contains(tx.merchant, "pingo doce")',
    },
    {
        "title": "Several merchants for one category",
        "lua_script": 'return contains_any(tx.merchant, {"lidl", "continente", "pingo doce", "mercadona"})',
    },
    {
        "title": "Salary: large credit late in the month",
        "lua_script": "return tx.is_income and tx.amount > 1000 and day_of_month(tx.date) >= 23",
    },
    {
        "title": "Transfer between own accounts, using the raw payload",
        "lua_script": 'local iban = tx.raw.creditor_account and tx.raw.creditor_account.iban\nreturn iban ~= nil and contains_any(iban, {"PT50000201231234567890154"})',
    },
    {
        "title": "Debugging with log()",
        "lua_script": "log(tx.merchant)\nlog(tx.amount)\nreturn false",
    },
]


def _to_model(rule: dict[str, Any], names: dict[int, str]) -> CategoryRule:
    return CategoryRule(
        id=rule["id"],
        name=rule["name"],
        description=rule["description"],
        category_id=rule["categoryId"],
        category_name=names.get(rule["categoryId"]),
        lua_script=rule["lua_script"],
        priority=rule["priority"],
        is_active=rule["is_active"],
        is_default=rule["is_default"],
        exclude_from_stats=rule["exclude_from_stats"],
        created_at=rule["created_at"],
        updated_at=rule["updated_at"],
    )


def _category_names(category_repo: CategoryRepository) -> dict[int, str]:
    return {c["id"]: c["name"] for c in category_repo.get_all_categories()}


def _require_category(category_repo: CategoryRepository, category_id: int) -> None:
    if category_repo.get_category_by_id(category_id) is None:
        raise NotFoundError(f"Category {category_id} not found.")


# --- Reference and authoring helpers (static paths first) ---


@router.get("/category-rules/reference", response_model=RuleReference)
async def get_rule_reference() -> RuleReference:
    """The rule-scripting reference: every `tx` field, every stdlib function,
    the sandbox rules, and example scripts.

    Fetch this before writing a rule. It is generated from the runtime's own
    definitions, so it is always current for this server.
    """
    return RuleReference(**reference(), examples=EXAMPLES)


@router.post("/category-rules/test", response_model=RuleTestResult)
async def test_rule_script(body: RuleScriptTest) -> RuleTestResult:
    """Run a script against one existing transaction and see the result and
    its log() output.

    Rejects a script that does not compile with 422; a runtime error inside
    the script comes back in `error` with a 200.
    """
    try:
        outcome = CategoryRuleEngine().test_script(
            body.lua_script, body.account_id, body.transaction_id
        )
    except LookupError:
        raise NotFoundError("Transaction not found.") from None
    return RuleTestResult(
        matched=outcome.matched, error=outcome.error, logs=outcome.logs
    )


@router.post("/category-rules/preview", response_model=RulePreviewResponse)
async def preview_rule_script(body: RuleScriptPreview) -> RulePreviewResponse:
    """List every transaction a script matches, without saving anything.

    Manually categorized transactions are included and flagged `manual`:
    the engine would leave them alone, but they show the rule's true reach.
    Use this to check a rule's precision before creating or activating it.
    """
    preview = CategoryRuleEngine().preview_script(body.lua_script)
    total = preview.matched
    total_pages = max((total + body.per_page - 1) // body.per_page, 1)
    start = (body.page - 1) * body.per_page
    page_matches = preview.matches[start : start + body.per_page]
    return RulePreviewResponse(
        data=[RuleMatch(**m.__dict__) for m in page_matches],
        total=total,
        page=body.page,
        per_page=body.per_page,
        total_pages=total_pages,
        has_next=body.page < total_pages,
        has_prev=body.page > 1,
        evaluated=preview.evaluated,
        errors=preview.errors,
        error_samples=preview.error_samples,
    )


@router.post("/category-rules/apply", response_model=RuleRunReport)
async def apply_rules(
    dry_run: bool = Query(
        default=False,
        description="Report what would change without writing anything.",
    ),
) -> RuleRunReport:
    """Run every active rule over all transactions without a manual category.

    Rules also run automatically over new transactions on every sync; this
    re-evaluates history, which is what a new or edited rule needs. Manual
    assignments are never changed. Rule-made assignments no active rule
    reproduces any more are cleared.
    """
    result = CategoryRuleEngine().run(dry_run=dry_run)
    return RuleRunReport(
        dry_run=result.dry_run,
        rules_evaluated=result.rules_evaluated,
        transactions_evaluated=result.transactions_evaluated,
        assigned=result.assigned,
        cleared=result.cleared,
        changes=[RuleChange(**c.__dict__) for c in result.changes],
        skipped_rules=[
            SkippedRule(rule_id=rule_id, error=error)
            for rule_id, error in result.skipped_rules.items()
        ],
        errors=[
            RuleErrors(
                rule_id=report.rule_id,
                rule_name=report.rule_name,
                count=report.count,
                samples=report.samples,
            )
            for report in result.errors.values()
        ],
    )


# --- CRUD ---


@router.get("/category-rules", response_model=list[CategoryRule])
async def list_rules(
    rule_repo: Annotated[CategoryRuleRepository, Depends()],
    category_repo: Annotated[CategoryRepository, Depends()],
) -> list[CategoryRule]:
    """All rules in evaluation order: ascending priority, then id."""
    names = _category_names(category_repo)
    return [_to_model(rule, names) for rule in rule_repo.get_all_rules()]


@router.post(
    "/category-rules",
    response_model=CategoryRule,
    status_code=201,
    responses={
        404: {"description": "Category not found"},
        409: {"description": "A rule with this name already exists"},
        422: {"description": "The script does not compile"},
    },
)
async def create_rule(
    body: CategoryRuleCreate,
    rule_repo: Annotated[CategoryRuleRepository, Depends()],
    category_repo: Annotated[CategoryRepository, Depends()],
) -> CategoryRule:
    """Create a rule. The script is compiled first and rejected with 422 if
    it has a syntax error. Creating a rule does not run it: call
    POST /category-rules/apply, or wait for the next sync to categorize new
    transactions."""
    _require_category(category_repo, body.category_id)
    RuleRuntime().compile(body.lua_script)
    rule = rule_repo.create_rule(
        name=body.name,
        category_id=body.category_id,
        lua_script=body.lua_script,
        description=body.description,
        priority=body.priority,
        is_active=body.is_active,
        exclude_from_stats=body.exclude_from_stats,
    )
    return _to_model(rule, _category_names(category_repo))


@router.get(
    "/category-rules/{rule_id}",
    response_model=CategoryRule,
    responses={404: {"description": "Rule not found"}},
)
async def get_rule(
    rule_id: int,
    rule_repo: Annotated[CategoryRuleRepository, Depends()],
    category_repo: Annotated[CategoryRepository, Depends()],
) -> CategoryRule:
    """One rule by id."""
    rule = rule_repo.get_rule_by_id(rule_id)
    if rule is None:
        raise NotFoundError("Rule not found.")
    return _to_model(rule, _category_names(category_repo))


@router.put(
    "/category-rules/{rule_id}",
    response_model=CategoryRule,
    responses={
        404: {"description": "Rule or category not found"},
        409: {"description": "A rule with this name already exists"},
        422: {"description": "The script does not compile"},
    },
)
async def update_rule(
    rule_id: int,
    body: CategoryRuleUpdate,
    rule_repo: Annotated[CategoryRuleRepository, Depends()],
    category_repo: Annotated[CategoryRepository, Depends()],
) -> CategoryRule:
    """Update the fields sent; the others keep their value. A changed script
    is compiled first. Editing does not re-run the engine."""
    if rule_repo.get_rule_by_id(rule_id) is None:
        raise NotFoundError("Rule not found.")
    fields = body.model_dump(exclude_unset=True)
    if "category_id" in fields:
        if fields["category_id"] is None:
            fields.pop("category_id")
        else:
            _require_category(category_repo, fields["category_id"])
    if fields.get("lua_script") is not None:
        RuleRuntime().compile(fields["lua_script"])
    # None for the required columns means "not sent"; only the nullable
    # ones (description, exclude_from_stats) may be cleared.
    for key in ("name", "lua_script", "priority", "is_active"):
        if key in fields and fields[key] is None:
            fields.pop(key)
    rule = rule_repo.update_rule(
        rule_id, **{_FIELD_TO_COLUMN[k]: v for k, v in fields.items()}
    )
    if rule is None:
        raise NotFoundError("Rule not found.")
    return _to_model(rule, _category_names(category_repo))


@router.delete(
    "/category-rules/{rule_id}",
    status_code=204,
    responses={404: {"description": "Rule not found"}},
)
async def delete_rule(
    rule_id: int,
    rule_repo: Annotated[CategoryRuleRepository, Depends()],
) -> Response:
    """Delete a rule. The categories it assigned are removed with it;
    manual assignments are untouched."""
    if not rule_repo.delete_rule(rule_id):
        raise NotFoundError("Rule not found.")
    return Response(status_code=204)
