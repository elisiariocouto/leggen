"""The category rule engine: evaluates rules over transactions and records
the assignments they make.

Rules run in priority order and the first one that matches a transaction
wins. The engine only ever considers transactions without a manual
category and only ever writes rows marked as rule-made, so a category the
user chose is never touched, and a pass can be repeated at any time: the
second run over unchanged inputs changes nothing.
"""

from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from leggen.errors import InvalidRuleScriptError
from leggen.repositories import CategoryRuleRepository, TransactionRepository
from leggen.services.rules.lua_runtime import CompiledRule, RuleOutcome, RuleRuntime

# Error messages kept per rule in a run report; the count is unbounded.
MAX_ERROR_SAMPLES = 5


@dataclass
class RuleChange:
    """One assignment the engine made, or would make in a dry run."""

    account_id: str
    transaction_id: str
    description: str
    amount: float | None
    currency: str | None
    date: str | None
    # "assign" writes a category, "clear" removes a rule-made one that no
    # active rule reproduces any more.
    action: str
    category_id: int | None
    rule_id: int | None
    exclude_from_stats: bool | None
    previous_category_id: int | None
    previous_rule_id: int | None


@dataclass
class RuleErrorReport:
    """Evaluation failures of one rule across a run."""

    rule_id: int
    rule_name: str
    count: int = 0
    samples: list[str] = field(default_factory=list)

    def record(self, message: str) -> None:
        self.count += 1
        if len(self.samples) < MAX_ERROR_SAMPLES and message not in self.samples:
            self.samples.append(message)


@dataclass
class RuleRunResult:
    """What a pass evaluated and what it changed."""

    dry_run: bool
    rules_evaluated: int
    transactions_evaluated: int
    assigned: int
    cleared: int
    changes: list[RuleChange]
    # Rules that did not compile, keyed by id, with the compile error.
    skipped_rules: dict[int, str]
    errors: dict[int, RuleErrorReport]


@dataclass
class ScriptMatch:
    """A transaction an inline script matched, for previews."""

    account_id: str
    transaction_id: str
    description: str
    amount: float | None
    currency: str | None
    date: str | None
    category_id: int | None
    category_name: str | None
    # True when a manual category means the engine would leave it alone.
    manual: bool
    logs: list[str]


@dataclass
class ScriptPreview:
    matches: list[ScriptMatch]
    evaluated: int
    matched: int
    errors: int
    error_samples: list[str]


def _snapshot(row: dict[str, Any]) -> dict[str, Any]:
    when = row.get("transactionDate")
    return {
        "account_id": row["accountId"],
        "transaction_id": row["transactionId"],
        "description": row.get("description") or "",
        "amount": row.get("transactionValue"),
        "currency": row.get("transactionCurrency"),
        "date": str(when)[:10] if when else None,
    }


class CategoryRuleEngine:
    """Runs the active rules over transactions and applies the outcome."""

    def __init__(
        self,
        rules: CategoryRuleRepository | None = None,
        transactions: TransactionRepository | None = None,
    ) -> None:
        self.rules = rules or CategoryRuleRepository()
        self.transactions = transactions or TransactionRepository()

    def _compile_active_rules(
        self, runtime: RuleRuntime
    ) -> tuple[list[tuple[dict[str, Any], CompiledRule]], dict[int, str]]:
        compiled: list[tuple[dict[str, Any], CompiledRule]] = []
        skipped: dict[int, str] = {}
        for rule in self.rules.get_all_rules(active_only=True):
            try:
                compiled.append((rule, runtime.compile(rule["lua_script"])))
            except InvalidRuleScriptError as exc:
                # A broken rule must not stop the others from running.
                logger.warning(
                    f"Category rule '{rule['name']}' does not compile: {exc.detail}"
                )
                skipped[rule["id"]] = exc.detail
        return compiled, skipped

    def run(
        self,
        keys: list[tuple[str, str]] | None = None,
        *,
        dry_run: bool = False,
    ) -> RuleRunResult:
        """Evaluate the active rules over the candidate transactions.

        `keys` limits the pass to those transactions (a sync passes the rows
        it just added); None means every transaction without a manual
        category. With `dry_run` nothing is written and the report says
        what would have been.
        """
        runtime = RuleRuntime()
        compiled, skipped = self._compile_active_rules(runtime)
        errors: dict[int, RuleErrorReport] = {}

        candidates = self.transactions.get_rule_candidates(keys)
        assignments: list[tuple[str, str, int, int, bool | None]] = []
        clears: list[tuple[str, str]] = []
        changes: list[RuleChange] = []

        for row in candidates:
            tx = runtime.build_tx(row)
            winner: dict[str, Any] | None = None
            for rule, function in compiled:
                outcome = runtime.evaluate(function, tx)
                if outcome.error is not None:
                    report = errors.setdefault(
                        rule["id"], RuleErrorReport(rule["id"], rule["name"])
                    )
                    report.record(outcome.error)
                    continue
                if outcome.matched:
                    winner = rule
                    break

            current_category = row.get("categoryId")
            current_rule = row.get("ruleId")
            current_flag = row.get("ruleExcludeFromStats")
            if current_flag is not None:
                current_flag = bool(current_flag)

            if winner is not None:
                desired = (
                    winner["categoryId"],
                    winner["id"],
                    winner["exclude_from_stats"],
                )
                if desired != (current_category, current_rule, current_flag):
                    assignments.append(
                        (row["accountId"], row["transactionId"], *desired)
                    )
                    changes.append(
                        RuleChange(
                            **_snapshot(row),
                            action="assign",
                            category_id=winner["categoryId"],
                            rule_id=winner["id"],
                            exclude_from_stats=winner["exclude_from_stats"],
                            previous_category_id=current_category,
                            previous_rule_id=current_rule,
                        )
                    )
            elif row.get("categorySource") == "rule":
                clears.append((row["accountId"], row["transactionId"]))
                changes.append(
                    RuleChange(
                        **_snapshot(row),
                        action="clear",
                        category_id=None,
                        rule_id=None,
                        exclude_from_stats=None,
                        previous_category_id=current_category,
                        previous_rule_id=current_rule,
                    )
                )

        if not dry_run:
            self.rules.apply_assignments(assignments)
            self.rules.clear_assignments(clears)
            logger.info(
                f"Category rules: {len(compiled)} rules over {len(candidates)} "
                f"transactions, {len(assignments)} assigned, {len(clears)} cleared"
            )

        return RuleRunResult(
            dry_run=dry_run,
            rules_evaluated=len(compiled),
            transactions_evaluated=len(candidates),
            assigned=len(assignments),
            cleared=len(clears),
            changes=changes,
            skipped_rules=skipped,
            errors=errors,
        )

    # -- authoring helpers --

    def test_script(
        self, script: str, account_id: str, transaction_id: str
    ) -> RuleOutcome:
        """Evaluate a script against one transaction. Raises
        InvalidRuleScriptError on a syntax error; the transaction must exist."""
        row = self.transactions.get_transaction_by_id(account_id, transaction_id)
        if row is None:
            raise LookupError("Transaction not found.")
        runtime = RuleRuntime()
        compiled = runtime.compile(script)
        return runtime.evaluate(compiled, runtime.build_tx(row))

    def preview_script(self, script: str) -> ScriptPreview:
        """Every transaction a script matches, including manually categorized
        ones, which are flagged: the engine would not change them, but the
        author needs to see the rule's full reach to judge it."""
        runtime = RuleRuntime()
        compiled = runtime.compile(script)
        matches: list[ScriptMatch] = []
        errors = 0
        samples: list[str] = []
        rows = self.transactions.get_rule_candidates(include_manual=True)
        for row in rows:
            outcome = runtime.evaluate(compiled, runtime.build_tx(row))
            if outcome.error is not None:
                errors += 1
                if len(samples) < MAX_ERROR_SAMPLES and outcome.error not in samples:
                    samples.append(outcome.error)
                continue
            if outcome.matched:
                matches.append(
                    ScriptMatch(
                        **_snapshot(row),
                        category_id=row.get("categoryId"),
                        category_name=row.get("categoryName"),
                        manual=row.get("categorySource") == "manual",
                        logs=outcome.logs,
                    )
                )
        return ScriptPreview(
            matches=matches,
            evaluated=len(rows),
            matched=len(matches),
            errors=errors,
            error_samples=samples,
        )
