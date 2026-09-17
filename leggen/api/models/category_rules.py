"""Pydantic models for the category rule endpoints."""

from typing import Any

from pydantic import BaseModel, Field

_SCRIPT_DESCRIPTION = (
    "Body of a Lua function receiving the transaction as `tx`; return true "
    "to apply the rule. See GET /category-rules/reference for the fields and "
    "functions available."
)


class CategoryRule(BaseModel):
    """A rule that assigns a category to the transactions its script matches."""

    id: int
    name: str
    description: str | None = None
    category_id: int
    category_name: str | None = None
    lua_script: str = Field(description=_SCRIPT_DESCRIPTION)
    priority: int = Field(
        description="Evaluation order, ascending; the first matching rule wins."
    )
    is_active: bool
    is_default: bool = Field(
        description="Shipped with leggen. Editable, but a future version may "
        "replace it."
    )
    exclude_from_stats: bool | None = Field(
        description="Statistics flag set on the transactions this rule "
        "categorizes: true excludes them, false includes them, null leaves "
        "the category's default in force."
    )
    created_at: str | None = None
    updated_at: str | None = None


class CategoryRuleCreate(BaseModel):
    """Request body for creating a rule."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    category_id: int
    lua_script: str = Field(min_length=1, description=_SCRIPT_DESCRIPTION)
    priority: int = Field(default=100, ge=0)
    is_active: bool = True
    exclude_from_stats: bool | None = None


class CategoryRuleUpdate(BaseModel):
    """Request body for updating a rule. Only the fields sent are changed;
    send `description` or `exclude_from_stats` as null to clear them."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    category_id: int | None = None
    lua_script: str | None = Field(default=None, min_length=1)
    priority: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    exclude_from_stats: bool | None = None


class RuleScriptTest(BaseModel):
    """Evaluate a script against one existing transaction."""

    lua_script: str = Field(min_length=1, description=_SCRIPT_DESCRIPTION)
    account_id: str
    transaction_id: str


class RuleTestResult(BaseModel):
    """Outcome of evaluating a script against one transaction."""

    matched: bool
    error: str | None = Field(
        default=None,
        description="Runtime error raised by the script, if any. A script "
        "that does not compile is rejected with 422 instead.",
    )
    logs: list[str] = Field(
        default_factory=list, description="Lines the script passed to log()."
    )


class RuleScriptPreview(BaseModel):
    """Find every transaction a script matches."""

    lua_script: str = Field(min_length=1, description=_SCRIPT_DESCRIPTION)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=500)


class RuleMatch(BaseModel):
    """A transaction a script matched."""

    account_id: str
    transaction_id: str
    description: str
    amount: float | None
    currency: str | None
    date: str | None
    category_id: int | None = None
    category_name: str | None = None
    manual: bool = Field(
        description="The transaction has a manually chosen category, which "
        "the engine never overrides; the rule matches it but would not "
        "change it."
    )
    logs: list[str] = Field(default_factory=list)


class RulePreviewResponse(BaseModel):
    """The transactions a script matches, paginated, with run statistics."""

    data: list[RuleMatch]
    total: int = Field(description="Transactions matched.")
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
    evaluated: int = Field(description="Transactions the script was run against.")
    errors: int = Field(description="Evaluations that raised a runtime error.")
    error_samples: list[str] = Field(default_factory=list)


class RuleChange(BaseModel):
    """One assignment a run made, or would make."""

    account_id: str
    transaction_id: str
    description: str
    amount: float | None
    currency: str | None
    date: str | None
    action: str = Field(description='"assign" or "clear".')
    category_id: int | None
    rule_id: int | None
    exclude_from_stats: bool | None
    previous_category_id: int | None
    previous_rule_id: int | None


class SkippedRule(BaseModel):
    rule_id: int
    error: str


class RuleErrors(BaseModel):
    rule_id: int
    rule_name: str
    count: int
    samples: list[str]


class RuleRunReport(BaseModel):
    """Report of a rule engine pass."""

    dry_run: bool
    rules_evaluated: int
    transactions_evaluated: int
    assigned: int
    cleared: int
    changes: list[RuleChange]
    skipped_rules: list[SkippedRule] = Field(
        description="Active rules that did not compile and were left out."
    )
    errors: list[RuleErrors] = Field(
        description="Rules that raised runtime errors on some transactions."
    )


class RuleFunction(BaseModel):
    signature: str
    description: str


class RuleFunctionGroup(BaseModel):
    title: str
    functions: list[RuleFunction]


class RuleField(BaseModel):
    name: str
    type: str
    description: str


class RuleFieldGroup(BaseModel):
    title: str
    fields: list[RuleField]


class RuleReference(BaseModel):
    """Everything a script can use: the `tx` fields and the stdlib."""

    stdlib: list[RuleFunctionGroup]
    fields: list[RuleFieldGroup]
    notes: list[str]
    max_instructions: int
    examples: list[dict[str, Any]] = Field(
        description="Small, complete scripts showing common shapes of rule."
    )
