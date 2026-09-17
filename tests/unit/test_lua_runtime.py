"""Tests for the sandboxed Lua runtime that evaluates category rules."""

import pytest

from leggen.errors import InvalidRuleScriptError
from leggen.services.rules import (
    MAX_INSTRUCTIONS,
    RuleRuntime,
    reference,
    validate_script,
)


def _row(**overrides):
    row = {
        "accountId": "acc-1",
        "transactionId": "tx-1",
        "description": "COMPRA 3007 PINGO DOCE LISBOA",
        "transactionValue": -12.5,
        "transactionCurrency": "EUR",
        "transactionDate": "2026-09-05T10:00:00",
        "transactionStatus": "booked",
        "iban": "PT50000201231234567890154",
        "institutionId": "BPI_BBPIPTPL",
        "categoryName": None,
        "rawTransaction": {
            "creditor": {"name": "Pingo Doce"},
            "remittance_information": ["COMPRA 3007 PINGO DOCE LISBOA", "extra"],
            "bank_transaction_code": {"code": "PMNT"},
            "transaction_amount": {"amount": "12.50", "currency": "EUR"},
        },
    }
    row.update(overrides)
    return row


@pytest.fixture
def runtime():
    return RuleRuntime()


def run(runtime: RuleRuntime, script: str, row: dict | None = None):
    return runtime.evaluate(runtime.compile(script), runtime.build_tx(row or _row()))


@pytest.mark.unit
class TestEvaluation:
    def test_true_matches(self, runtime):
        assert run(runtime, 'return contains(tx.description, "pingo")').matched

    def test_false_does_not_match(self, runtime):
        assert not run(runtime, "return false").matched

    @pytest.mark.parametrize("script", ["return 1", 'return "yes"', "return nil", ""])
    def test_only_boolean_true_matches(self, runtime, script):
        """Lua truthiness is not enough: a rule states its verdict explicitly."""
        outcome = run(runtime, script)
        assert not outcome.matched
        assert outcome.error is None

    def test_runtime_error_is_reported_not_raised(self, runtime):
        outcome = run(runtime, "return tx.raw.missing.deeper")

        assert not outcome.matched
        assert outcome.error is not None
        assert "attempt to index a nil value" in outcome.error
        assert outcome.error.startswith("line 1:")

    def test_error_lines_are_relative_to_the_script(self, runtime):
        outcome = run(runtime, "local a = 1\nlocal b = 2\nreturn tx.raw.x.y")

        assert outcome.error is not None
        assert outcome.error.startswith("line 3:")

    def test_log_and_print_are_captured(self, runtime):
        outcome = run(runtime, 'log("one") print(tx.amount) log(nil) return true')

        assert outcome.logs == ["one", "-12.5", "nil"]

    def test_logs_do_not_leak_between_evaluations(self, runtime):
        run(runtime, 'log("first") return true')

        assert run(runtime, "return true").logs == []

    def test_logs_are_bounded(self, runtime):
        outcome = run(runtime, "for i = 1, 1000 do log(i) end return true")

        assert len(outcome.logs) == 100


@pytest.mark.unit
class TestCompilation:
    def test_syntax_error_is_a_domain_error(self, runtime):
        with pytest.raises(InvalidRuleScriptError) as excinfo:
            runtime.compile("if then")

        assert excinfo.value.status_code == 422
        assert "line 1" in excinfo.value.detail

    def test_validate_script(self):
        assert validate_script("return true") is None
        assert validate_script("return (") is not None


@pytest.mark.unit
class TestSandbox:
    @pytest.mark.parametrize(
        "name",
        [
            "os",
            "io",
            "require",
            "load",
            "loadstring",
            "loadfile",
            "dofile",
            "debug",
            "package",
            "coroutine",
            "collectgarbage",
            "getmetatable",
            "setmetatable",
            "rawget",
            "rawset",
            # lupa's bridge back into the interpreter: python.eval and
            # python.builtins would be a full escape.
            "python",
        ],
    )
    def test_dangerous_globals_are_gone(self, runtime, name):
        assert run(runtime, f"return {name} == nil").matched

    def test_safe_libraries_remain(self, runtime):
        assert run(
            runtime,
            'return string.upper("a") == "A" and math.floor(1.5) == 1 '
            "and #table.pack(1, 2) == 2",
        ).matched

    def test_stdlib_functions_cannot_be_introspected(self, runtime):
        outcome = run(runtime, "return contains.__globals__")

        assert not outcome.matched
        assert "not allowed" in (outcome.error or "")

    def test_infinite_loop_is_cut_off(self, runtime):
        outcome = run(runtime, "while true do end")

        assert not outcome.matched
        assert outcome.error == "line 1: instruction limit exceeded"

    def test_cap_is_per_evaluation(self, runtime):
        """A count hook is cumulative unless re-armed; many cheap
        evaluations must never add up to a spurious abort."""
        rule = runtime.compile("return tx.amount < 0")
        tx = runtime.build_tx(_row())

        for _ in range(MAX_INSTRUCTIONS):
            assert runtime.evaluate(rule, tx).matched

    def test_memory_bomb_is_contained(self, runtime):
        outcome = run(
            runtime, 'local s = "x" for i = 1, 40 do s = s .. s end return #s > 0'
        )

        assert not outcome.matched
        assert "memory" in (outcome.error or "")
        # The runtime survives to evaluate the next rule.
        assert run(runtime, "return true").matched


@pytest.mark.unit
class TestTxTable:
    def test_stable_fields(self, runtime):
        script = """
        log(tx.account_id) log(tx.transaction_id) log(tx.description)
        log(tx.amount) log(tx.currency) log(tx.date) log(tx.status)
        log(tx.iban) log(tx.institution_id)
        return tx.is_expense and not tx.is_income
        """
        outcome = run(runtime, script)

        assert outcome.matched
        assert outcome.logs == [
            "acc-1",
            "tx-1",
            "COMPRA 3007 PINGO DOCE LISBOA",
            "-12.5",
            "EUR",
            "2026-09-05",
            "booked",
            "PT50000201231234567890154",
            "BPI_BBPIPTPL",
        ]

    def test_merchant_prefers_the_structured_counterparty(self, runtime):
        assert run(runtime, 'return tx.merchant == "Pingo Doce"').matched

    def test_merchant_falls_back_to_the_cleaned_description(self, runtime):
        row = _row(rawTransaction={})
        # Card reference "3007" is stripped, the merchant text kept.
        assert run(
            runtime, 'return tx.merchant == "COMPRA PINGO DOCE LISBOA"', row
        ).matched

    def test_creditor_and_debtor(self, runtime):
        assert run(
            runtime, 'return tx.creditor == "Pingo Doce" and tx.debtor == nil'
        ).matched

    def test_income_flags(self, runtime):
        row = _row(transactionValue=2500.0)
        assert run(runtime, "return tx.is_income and not tx.is_expense", row).matched

    def test_category_name(self, runtime):
        assert run(runtime, "return tx.category == nil").matched
        assert run(
            runtime, 'return tx.category == "Groceries"', _row(categoryName="Groceries")
        ).matched

    def test_raw_is_nested_lua_tables(self, runtime):
        script = """
        return tx.raw.bank_transaction_code.code == "PMNT"
           and tx.raw.creditor.name == "Pingo Doce"
           and tx.raw.transaction_amount.amount == "12.50"
        """
        assert run(runtime, script).matched

    def test_raw_lists_are_lua_arrays(self, runtime):
        """1-based, sized with #, iterable with ipairs — a Python list handed
        across untouched would fail all three."""
        script = """
        local items = tx.raw.remittance_information
        local n = 0
        for _, _ in ipairs(items) do n = n + 1 end
        return #items == 2 and items[1] == "COMPRA 3007 PINGO DOCE LISBOA" and n == 2
        """
        assert run(runtime, script).matched

    def test_missing_raw_keys_are_nil(self, runtime):
        """The whole point of raw access is probing fields that may not be
        there; a missing key must read as nil, not raise."""
        assert run(
            runtime, "return tx.raw.nope == nil and tx.raw.creditor.nope == nil"
        ).matched

    def test_raw_accepts_json_text(self, runtime):
        row = _row(rawTransaction='{"creditor": {"name": "From JSON"}}')
        assert run(runtime, 'return tx.raw.creditor.name == "From JSON"', row).matched

    def test_raw_depth_is_capped(self, runtime):
        deep: dict = {"v": 1}
        for _ in range(20):
            deep = {"n": deep}
        row = _row(rawTransaction=deep)
        # Does not recurse forever; nine levels in is still a table and the
        # tenth reads as nil.
        nine = "tx.raw" + ".n" * 9
        assert run(runtime, f"return {nine} ~= nil and {nine}.n == nil", row).matched

    def test_datetime_dates_are_accepted(self, runtime):
        from datetime import datetime

        row = _row(transactionDate=datetime(2026, 1, 2, 3, 4))
        assert run(runtime, 'return tx.date == "2026-01-02"', row).matched


@pytest.mark.unit
class TestStdlib:
    @pytest.mark.parametrize(
        "script",
        [
            'return contains("Pingo Doce", "doce")',
            'return not contains("Pingo Doce", "lidl")',
            'return not contains(nil, "x") and not contains("x", nil)',
            'return contains_any("Pingo Doce", {"lidl", "pingo"})',
            'return not contains_any("Pingo Doce", {"lidl"}) and not contains_any(nil, {"a"})',
            'return starts_with("Pingo Doce", "PINGO") and not starts_with(nil, "x")',
            'return ends_with("Pingo Doce", "doce") and not ends_with("x", nil)',
            'return exact("  Pingo Doce ", "pingo doce") and not exact(nil, "a")',
            'return matches("INV-2025-42", "^inv-\\\\d{4}") and not matches("x", "[")',
            'return normalize("  Sã Jôao  Lda ") == "sa joao lda" and normalize(nil) == ""',
            'local w = words("Pingo-Doce 42") return #w == 3 and w[1] == "pingo" and w[3] == "42"',
            "return #words(nil) == 0",
            "return magnitude(-12.5) == 12.5 and magnitude(nil) == nil",
            "return amount_eq(-10, 10) and not amount_eq(nil, 10)",
            "return amount_close(-10, 10.4, 0.5) and not amount_close(-10, 11, 0.5)",
            "return amount_close(100, 104, 0, 5) and not amount_close(100, 106, 0, 5)",
            "return amount_between(-12.5, -20, 0) and not amount_between(-12.5, 0, 20)",
            "return not amount_between(nil, 0, 1)",
            'return days_apart("2026-01-01", "2026-01-11") == 10 and days_apart(nil, "2026-01-01") == nil',
            'return same_month("2026-01-01", "2026-01-31") and not same_month("2026-01-31", "2026-02-01")',
            'return day_of_month("2026-09-05") == 5 and day_of_month(nil) == nil',
            'return weekday("2026-09-07") == 1 and weekday("2026-09-13") == 7',
            'return month("2026-09-05") == 9 and year("2026-09-05") == 2026',
            'return month("garbage") == nil',
            'return coalesce(nil, nil, "x") == "x" and coalesce(nil) == nil',
            "return is_nil(nil) and not is_nil(false)",
        ],
    )
    def test_function(self, runtime, script):
        outcome = run(runtime, script)
        assert outcome.error is None, outcome.error
        assert outcome.matched


@pytest.mark.unit
class TestAccountIbans:
    def test_is_own_iban_ignores_spaces_and_case(self):
        runtime = RuleRuntime(account_ibans=["PT50 0002 0123 1234 5678 9015 4"])

        assert run(runtime, 'return is_own_iban("pt50000201231234567890154")').matched
        assert run(runtime, 'return not is_own_iban("DE89370400440532013000")').matched
        assert run(runtime, "return not is_own_iban(nil)").matched
        assert run(
            runtime,
            'return #ACCOUNT_IBANS == 1 and ACCOUNT_IBANS[1] == "PT50000201231234567890154"',
        ).matched

    def test_defaults_to_no_accounts(self, runtime):
        assert run(
            runtime, "return #ACCOUNT_IBANS == 0 and not is_own_iban('X')"
        ).matched


@pytest.mark.unit
class TestReference:
    def test_documents_every_injected_function(self, runtime):
        documented = {
            fn["signature"].split("(")[0]
            for section in reference()["stdlib"]
            for fn in section["functions"]
        }
        # print is an alias of log and deliberately shares its entry.
        injected = {
            name
            for name in [
                "contains",
                "contains_any",
                "starts_with",
                "ends_with",
                "exact",
                "matches",
                "normalize",
                "words",
                "magnitude",
                "amount_eq",
                "amount_close",
                "amount_between",
                "days_apart",
                "same_month",
                "day_of_month",
                "weekday",
                "month",
                "year",
                "coalesce",
                "is_nil",
                "log",
                "is_own_iban",
            ]
            # Python callables reach Lua as userdata, not "function".
            if run(runtime, f"return {name} ~= nil").matched
        }
        assert documented == injected

    def test_documents_every_tx_field(self, runtime):
        documented = {
            f["name"].removeprefix("tx.")
            for section in reference()["fields"]
            for f in section["fields"]
        }
        # A nil field is absent from pairs(), so give every field a value.
        row = _row(
            categoryName="Groceries",
            rawTransaction={
                "creditor": {"name": "Shop"},
                "debtor": {"name": "Me"},
            },
        )
        outcome = run(
            runtime,
            "for k, _ in pairs(tx) do log(k) end return true",
            row,
        )
        # transaction_id is an identifier, not something to write a rule on.
        assert set(outcome.logs) - {"transaction_id"} == documented
