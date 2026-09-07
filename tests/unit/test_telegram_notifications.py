"""Tests for the Telegram MarkdownV2 escaping helper."""

import pytest

from leggen.notifications.telegram import (
    _MARKDOWN_V2_SPECIAL_CHARS,
    escape_markdown,
)

# The full MarkdownV2 special-character set, per Telegram's spec:
# https://core.telegram.org/bots/api#markdownv2-style
SPEC_SPECIAL_CHARS = "_*[]()~`>#+-=|{}.!\\"


@pytest.mark.unit
class TestEscapeMarkdown:
    def test_covers_the_full_markdownv2_special_character_set(self):
        assert set(_MARKDOWN_V2_SPECIAL_CHARS) == set(SPEC_SPECIAL_CHARS)

    def test_backslash_is_escaped_first(self):
        assert _MARKDOWN_V2_SPECIAL_CHARS[0] == "\\"

    @pytest.mark.parametrize("char", list(SPEC_SPECIAL_CHARS))
    def test_every_special_character_is_escaped_once(self, char):
        assert escape_markdown(char) == f"\\{char}"

    def test_plain_text_is_untouched(self):
        assert escape_markdown("Coffee Shop 42") == "Coffee Shop 42"

    def test_escapes_a_lone_backslash(self):
        assert escape_markdown("C:\\path") == "C:\\\\path"

    def test_escapes_backslash_mixed_with_other_specials(self):
        # Input:  a\b_c
        # Output: a\\b\_c  (backslash doubled, underscore escaped once)
        assert escape_markdown("a\\b_c") == "a\\\\b\\_c"

    def test_no_double_escaping_of_added_escapes(self):
        # Every escape in the output must be a backslash followed by a special
        # character, and the number of escapes must equal the number of
        # specials in the input — no escape gets escaped again.
        text = "Payment -12.50 EUR (ref: #42) \\ 100% {done}!"
        escaped = escape_markdown(text)

        expected_specials = sum(text.count(c) for c in SPEC_SPECIAL_CHARS)
        assert escaped.count("\\") == expected_specials + text.count("\\")

        # Unescaping restores the original exactly.
        unescaped = []
        i = 0
        while i < len(escaped):
            if escaped[i] == "\\":
                assert i + 1 < len(escaped), "trailing escape character"
                assert escaped[i + 1] in SPEC_SPECIAL_CHARS
                unescaped.append(escaped[i + 1])
                i += 2
            else:
                unescaped.append(escaped[i])
                i += 1
        assert "".join(unescaped) == text

    def test_already_escaped_input_is_escaped_again_not_mangled(self):
        # An input that already looks escaped is literal text: both characters
        # get escaped, which round-trips back to the original.
        assert escape_markdown("\\.") == "\\\\\\."

    def test_accepts_non_string_input(self):
        assert escape_markdown(-10.5) == "\\-10\\.5"
