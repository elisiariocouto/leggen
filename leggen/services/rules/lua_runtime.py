"""Sandboxed Lua runtime for category rules.

A rule is the body of a Lua function that receives one transaction as the
table `tx` and returns `true` when the rule applies. Scripts run inside a
runtime that has had every way out of the sandbox removed, with a hard cap on
instructions per evaluation and on memory, so a rule written by a user — or
by an agent working the API — can misbehave without taking the server with it.

The stdlib injected into the runtime and the shape of `tx` are described by
`STDLIB_REFERENCE`, `TX_REFERENCE` and `NOTES`, which double as the reference
served to rule authors: the documentation is generated from the same data
the runtime is built from, so the two cannot drift.
"""

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import lupa
from lupa import LuaRuntime

from leggen.errors import InvalidRuleScriptError
from leggen.services.data_processors import counterparty_name, merchant_identity

# Lua VM instructions one evaluation may execute before it is aborted. Ample
# for any sensible rule — a typical one needs well under a hundred — and
# small enough that a runaway loop is cut off in about a millisecond.
MAX_INSTRUCTIONS = 100_000

# Memory the Lua state may allocate. Bounds `string.rep`-style blowups.
MAX_MEMORY_BYTES = 32 * 1024 * 1024

# Nesting depth beyond which `tx.raw` is truncated. Provider payloads are a
# few levels deep; this guards against a pathological one recursing forever.
MAX_RAW_DEPTH = 10

# `log()` lines kept per evaluation, so a log() inside a loop stays bounded.
MAX_LOG_LINES = 100

# ─── Reference metadata (the single source for the docs) ─────────────────────

STDLIB_REFERENCE: list[dict[str, Any]] = [
    {
        "title": "Text",
        "functions": [
            {
                "signature": "contains(text, substring)",
                "description": "True if text contains substring (case-insensitive).",
            },
            {
                "signature": "contains_any(text, {a, b, ...})",
                "description": "True if text contains any of the substrings.",
            },
            {
                "signature": "starts_with(text, prefix)",
                "description": "True if text starts with prefix (case-insensitive).",
            },
            {
                "signature": "ends_with(text, suffix)",
                "description": "True if text ends with suffix (case-insensitive).",
            },
            {
                "signature": "exact(text, value)",
                "description": "True if text equals value after trimming and lowercasing.",
            },
            {
                "signature": "matches(text, pattern)",
                "description": "True if the Python-syntax regex matches anywhere in text (case-insensitive).",
            },
            {
                "signature": "normalize(text)",
                "description": "Lowercase, strip accents and collapse whitespace.",
            },
            {
                "signature": "words(text)",
                "description": "Lua array of the lowercased alphanumeric words in text.",
            },
        ],
    },
    {
        "title": "Amount",
        "functions": [
            {
                "signature": "magnitude(a)",
                "description": "Absolute value; nil stays nil.",
            },
            {
                "signature": "amount_eq(a, b)",
                "description": "True if the two amounts have the same magnitude.",
            },
            {
                "signature": "amount_close(a, b, tolerance, tolerance_percent?)",
                "description": "True if the magnitudes differ by at most tolerance, or by at most tolerance_percent of the larger.",
            },
            {
                "signature": "amount_between(a, low, high)",
                "description": "True if low <= a <= high. Signed: expenses are negative.",
            },
        ],
    },
    {
        "title": "Date",
        "functions": [
            {
                "signature": "days_apart(d1, d2)",
                "description": "Whole days between two ISO dates, or nil.",
            },
            {
                "signature": "same_month(d1, d2)",
                "description": "True if both dates fall in the same year and month.",
            },
            {
                "signature": "day_of_month(d)",
                "description": "1–31, or nil.",
            },
            {
                "signature": "weekday(d)",
                "description": "1 (Monday) to 7 (Sunday), or nil.",
            },
            {
                "signature": "month(d)",
                "description": "1–12, or nil.",
            },
            {
                "signature": "year(d)",
                "description": "Four-digit year, or nil.",
            },
        ],
    },
    {
        "title": "Utility",
        "functions": [
            {
                "signature": "coalesce(a, b, ...)",
                "description": "First argument that is not nil.",
            },
            {
                "signature": "is_nil(x)",
                "description": "True if x is nil.",
            },
            {
                "signature": "log(message)",
                "description": "Records a line in the test output. print() does the same.",
            },
        ],
    },
]

TX_REFERENCE: list[dict[str, Any]] = [
    {
        "title": "tx (transaction)",
        "fields": [
            {
                "name": "tx.description",
                "type": "string",
                "description": "Description as the bank sent it.",
            },
            {
                "name": "tx.merchant",
                "type": "string",
                "description": "Best guess at who the transaction was with: the "
                "structured counterparty name where the bank gives one, otherwise "
                "the description with card references, dates and scheme prefixes "
                "stripped. The field to match merchants on.",
            },
            {
                "name": "tx.creditor",
                "type": "string or nil",
                "description": "Structured creditor name, if the bank provides it.",
            },
            {
                "name": "tx.debtor",
                "type": "string or nil",
                "description": "Structured debtor name, if the bank provides it.",
            },
            {
                "name": "tx.amount",
                "type": "number",
                "description": "Signed amount: negative for expenses, positive for income.",
            },
            {
                "name": "tx.is_expense",
                "type": "boolean",
                "description": "True when amount < 0.",
            },
            {
                "name": "tx.is_income",
                "type": "boolean",
                "description": "True when amount > 0.",
            },
            {
                "name": "tx.currency",
                "type": "string",
                "description": "Three-letter currency code.",
            },
            {
                "name": "tx.date",
                "type": "string",
                "description": "ISO date, YYYY-MM-DD.",
            },
            {
                "name": "tx.status",
                "type": "string",
                "description": '"booked" or "pending".',
            },
            {
                "name": "tx.account_id",
                "type": "string",
                "description": "Leggen account ID the transaction belongs to.",
            },
            {
                "name": "tx.iban",
                "type": "string or nil",
                "description": "IBAN of that account.",
            },
            {
                "name": "tx.institution_id",
                "type": "string or nil",
                "description": "Bank identifier of that account.",
            },
            {
                "name": "tx.category",
                "type": "string or nil",
                "description": "Name of the category currently assigned, if any.",
            },
            {
                "name": "tx.raw",
                "type": "table",
                "description": "The full transaction exactly as the bank returned it, "
                "as nested Lua tables. Provider-shaped and unstable: keys are "
                "EnableBanking's snake_case and vary by bank, so a rule that "
                "reads it may break when the bank changes its feed. The fields "
                "above are the stable contract; this is the escape hatch for "
                "anything they do not carry.",
            },
        ],
    },
]

NOTES: list[str] = [
    "The script is the body of `function(tx) ... end`. Return true to apply the rule; anything else does not match.",
    "Every field can be nil and every stdlib function tolerates nil, returning false, nil or an empty value as appropriate.",
    "Text comparisons are case-insensitive. matches() takes Python regex syntax, not Lua patterns.",
    "tx.amount is signed: compare against negative numbers for expenses, or use magnitude().",
    "tx.raw lists are Lua arrays: 1-based, and iterable with ipairs() and #.",
    "The runtime is sandboxed: os, io, require, load, dofile, debug, package, coroutine and python are unavailable. string, table and math are.",
    f"An evaluation is aborted after {MAX_INSTRUCTIONS:,} Lua instructions, so a rule cannot loop forever.",
]


def reference() -> dict[str, Any]:
    """The rule-authoring reference, built from the runtime's own metadata."""
    return {
        "stdlib": STDLIB_REFERENCE,
        "fields": TX_REFERENCE,
        "notes": NOTES,
        "max_instructions": MAX_INSTRUCTIONS,
    }


# ─── Coercion helpers ────────────────────────────────────────────────────────


def _to_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _to_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


_WORD = re.compile(r"[a-zA-Z0-9À-ɏ]+")


def _lua_list(value: Any) -> list[Any]:
    """Materialize a Lua array (or a Python sequence) as a list."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    if lupa.lua_type(value) == "table":
        return list(value.values())
    return [value]


# ─── The stdlib ──────────────────────────────────────────────────────────────


def _contains(text: Any, substring: Any) -> bool:
    t, s = _to_str(text), _to_str(substring)
    if t is None or s is None:
        return False
    return s.lower() in t.lower()


def _contains_any(text: Any, substrings: Any) -> bool:
    return any(_contains(text, s) for s in _lua_list(substrings))


def _starts_with(text: Any, prefix: Any) -> bool:
    t, p = _to_str(text), _to_str(prefix)
    if t is None or p is None:
        return False
    return t.lower().startswith(p.lower())


def _ends_with(text: Any, suffix: Any) -> bool:
    t, s = _to_str(text), _to_str(suffix)
    if t is None or s is None:
        return False
    return t.lower().endswith(s.lower())


def _exact(text: Any, value: Any) -> bool:
    t, v = _to_str(text), _to_str(value)
    if t is None or v is None:
        return False
    return t.strip().lower() == v.strip().lower()


def _matches(text: Any, pattern: Any) -> bool:
    t, p = _to_str(text), _to_str(pattern)
    if t is None or p is None:
        return False
    try:
        return re.search(p, t, re.IGNORECASE) is not None
    except re.error:
        return False


def _normalize(text: Any) -> str:
    t = _to_str(text)
    if t is None:
        return ""
    return re.sub(r"\s+", " ", _strip_accents(t.lower())).strip()


def _magnitude(amount: Any) -> float | None:
    a = _to_float(amount)
    return abs(a) if a is not None else None


def _amount_eq(a: Any, b: Any) -> bool:
    fa, fb = _to_float(a), _to_float(b)
    if fa is None or fb is None:
        return False
    return abs(fa) == abs(fb)


def _amount_close(
    a: Any, b: Any, tolerance: Any = 0, tolerance_percent: Any = None
) -> bool:
    fa, fb = _to_float(a), _to_float(b)
    if fa is None or fb is None:
        return False
    diff = abs(abs(fa) - abs(fb))
    if diff <= (_to_float(tolerance) or 0.0):
        return True
    percent = _to_float(tolerance_percent)
    if percent is not None:
        larger = max(abs(fa), abs(fb))
        return larger > 0 and diff <= percent / 100.0 * larger
    return False


def _amount_between(a: Any, low: Any, high: Any) -> bool:
    fa, lo, hi = _to_float(a), _to_float(low), _to_float(high)
    if fa is None or lo is None or hi is None:
        return False
    return lo <= fa <= hi


def _days_apart(d1: Any, d2: Any) -> int | None:
    a, b = _to_date(d1), _to_date(d2)
    if a is None or b is None:
        return None
    return abs((a - b).days)


def _same_month(d1: Any, d2: Any) -> bool:
    a, b = _to_date(d1), _to_date(d2)
    if a is None or b is None:
        return False
    return (a.year, a.month) == (b.year, b.month)


def _day_of_month(d: Any) -> int | None:
    parsed = _to_date(d)
    return parsed.day if parsed else None


def _weekday(d: Any) -> int | None:
    parsed = _to_date(d)
    return parsed.isoweekday() if parsed else None


def _month(d: Any) -> int | None:
    parsed = _to_date(d)
    return parsed.month if parsed else None


def _year(d: Any) -> int | None:
    parsed = _to_date(d)
    return parsed.year if parsed else None


def _coalesce(*args: Any) -> Any:
    for value in args:
        if value is not None:
            return value
    return None


def _is_nil(value: Any) -> bool:
    return value is None


# ─── Sandbox ─────────────────────────────────────────────────────────────────

# Built before `debug` is removed: the closure keeps its own reference to
# debug.sethook, so it can arm the instruction cap for every evaluation while
# the rule itself has no way to reach or disarm it. Re-arming per call is
# what makes the cap per evaluation — a count hook is cumulative otherwise,
# and a bulk pass over a few thousand transactions would trip it on a
# perfectly good rule.
_MAKE_CALL_RULE = """
function(limit)
    local sethook = debug.sethook
    local function on_limit()
        error("instruction limit exceeded", 2)
    end
    return function(fn, tx)
        sethook(on_limit, "", limit)
        local ok, result = pcall(fn, tx)
        sethook()
        return ok, result
    end
end
"""

# Everything that could read the filesystem, load code, reach the host
# process or tamper with the runtime. `python` is lupa's bridge to the
# interpreter and the most dangerous of the lot.
_SANDBOX = """
os = nil
io = nil
require = nil
load = nil
loadstring = nil
loadfile = nil
dofile = nil
debug = nil
package = nil
coroutine = nil
collectgarbage = nil
rawget = nil
rawset = nil
rawequal = nil
rawlen = nil
getmetatable = nil
setmetatable = nil
python = nil
"""


def _deny_attribute(obj: Any, attr_name: Any, is_setting: bool) -> None:
    """Lua may call the stdlib functions but never look inside them."""
    raise AttributeError(f"attribute access is not allowed: {attr_name}")


_LUA_LOCATION = re.compile(r'\[string "<python>"\]:(\d+):\s*')


def _clean_error(message: str) -> str:
    """Rewrite Lua's chunk locations to line numbers within the script.

    The script is wrapped in a one-line function header, so Lua's line N is
    the author's line N-1.
    """

    def relocate(match: re.Match[str]) -> str:
        line = max(int(match.group(1)) - 1, 1)
        return f"line {line}: "

    return _LUA_LOCATION.sub(relocate, message).strip()


# ─── Runtime ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CompiledRule:
    """A rule script compiled into the runtime that will evaluate it."""

    script: str
    function: Any


@dataclass
class RuleOutcome:
    """What happened when a rule was evaluated against one transaction."""

    matched: bool
    error: str | None = None
    logs: list[str] = field(default_factory=list)


class RuleRuntime:
    """One sandboxed Lua state: compile rules against it, then evaluate them.

    Compiled rules belong to the runtime that compiled them. A caller that
    evaluates many rules over many transactions builds one runtime, compiles
    every rule once, and builds each `tx` table once per transaction.
    """

    def __init__(self) -> None:
        self._logs: list[str] = []
        self._lua = LuaRuntime(
            unpack_returned_tuples=True,
            register_eval=False,
            register_builtins=False,
            attribute_filter=_deny_attribute,
            max_memory=MAX_MEMORY_BYTES,
        )
        self._call_rule = self._lua.eval(_MAKE_CALL_RULE)(MAX_INSTRUCTIONS)
        self._lua.execute(_SANDBOX)
        self._install_stdlib()

    def _install_stdlib(self) -> None:
        lua = self._lua
        globals_ = lua.globals()

        def words(text: Any) -> Any:
            t = _to_str(text)
            return lua.table(*_WORD.findall(t.lower())) if t else lua.table()

        def log(message: Any) -> None:
            if len(self._logs) < MAX_LOG_LINES:
                self._logs.append("nil" if message is None else str(message))

        stdlib: dict[str, Any] = {
            "contains": _contains,
            "contains_any": _contains_any,
            "starts_with": _starts_with,
            "ends_with": _ends_with,
            "exact": _exact,
            "matches": _matches,
            "normalize": _normalize,
            "words": words,
            "magnitude": _magnitude,
            "amount_eq": _amount_eq,
            "amount_close": _amount_close,
            "amount_between": _amount_between,
            "days_apart": _days_apart,
            "same_month": _same_month,
            "day_of_month": _day_of_month,
            "weekday": _weekday,
            "month": _month,
            "year": _year,
            "coalesce": _coalesce,
            "is_nil": _is_nil,
            "log": log,
            "print": log,
        }
        for name, function in stdlib.items():
            globals_[name] = function

    # -- compiling --

    def compile(self, script: str) -> CompiledRule:
        """Compile a rule body. Raises InvalidRuleScriptError on a syntax error."""
        try:
            function = self._lua.eval(f"function(tx)\n{script}\nend")
        except lupa.LuaSyntaxError as exc:
            raise InvalidRuleScriptError(_clean_error(str(exc))) from exc
        except lupa.LuaError as exc:
            raise InvalidRuleScriptError(_clean_error(str(exc))) from exc
        return CompiledRule(script=script, function=function)

    # -- the tx table --

    def _to_lua(self, value: Any, depth: int = 0) -> Any:
        """Convert a JSON-shaped Python value into nested Lua tables.

        Handing the Python dict across as-is would break every Lua idiom on
        it: `#` fails, ipairs raises, `[1]` returns the second element and a
        missing key raises KeyError instead of yielding nil.
        """
        if depth >= MAX_RAW_DEPTH:
            return None
        if isinstance(value, dict):
            table = self._lua.table()
            for key, item in value.items():
                table[str(key)] = self._to_lua(item, depth + 1)
            return table
        if isinstance(value, (list, tuple)):
            return self._lua.table(*(self._to_lua(item, depth + 1) for item in value))
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    def build_tx(self, row: dict[str, Any]) -> Any:
        """Build the `tx` table from a transaction row as the repository returns it."""
        raw = row.get("rawTransaction") or {}
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except ValueError:
                raw = {}
        if not isinstance(raw, dict):
            raw = {}

        description = str(row.get("description") or "")
        amount = _to_float(row.get("transactionValue"))
        is_expense = amount is not None and amount < 0
        _, merchant = merchant_identity(raw, description, is_expense)
        when = row.get("transactionDate")
        iso = when.isoformat() if isinstance(when, datetime) else _to_str(when)

        tx = self._lua.table()
        tx["account_id"] = row.get("accountId")
        tx["transaction_id"] = row.get("transactionId")
        tx["description"] = description
        tx["merchant"] = merchant
        tx["creditor"] = counterparty_name(raw, "creditor") or None
        tx["debtor"] = counterparty_name(raw, "debtor") or None
        tx["amount"] = amount
        tx["is_expense"] = is_expense
        tx["is_income"] = amount is not None and amount > 0
        tx["currency"] = row.get("transactionCurrency")
        tx["date"] = iso[:10] if iso else None
        tx["status"] = row.get("transactionStatus")
        tx["iban"] = row.get("iban")
        tx["institution_id"] = row.get("institutionId")
        tx["category"] = row.get("categoryName")
        tx["raw"] = self._to_lua(raw)
        return tx

    # -- evaluating --

    def evaluate(self, rule: CompiledRule, tx: Any) -> RuleOutcome:
        """Run a compiled rule against a `tx` table.

        Never raises for anything the script does: runtime errors, the
        instruction cap and memory exhaustion all come back in `error`.
        """
        self._logs = []
        try:
            ok, result = self._call_rule(rule.function, tx)
        except lupa.LuaError as exc:
            # Memory exhaustion surfaces here rather than through pcall.
            return RuleOutcome(False, _clean_error(str(exc)), self._logs)
        logs, self._logs = self._logs, []
        if not ok:
            return RuleOutcome(False, _clean_error(str(result)), logs)
        return RuleOutcome(result is True, None, logs)


def validate_script(script: str) -> str | None:
    """Return the compile error for a script, or None when it is valid."""
    try:
        RuleRuntime().compile(script)
    except InvalidRuleScriptError as exc:
        return exc.detail
    return None
