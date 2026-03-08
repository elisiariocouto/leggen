"""Tests for the keyword extraction utility."""

from leggen.services.categorizer import extract_keywords


class TestExtractKeywords:
    """Test keyword extraction from transaction text."""

    def test_basic_extraction(self):
        """Test basic keyword extraction from simple text."""
        result = extract_keywords("TESCO GROCERY STORE")
        assert "tesco" in result
        assert "grocery" in result
        assert "store" in result

    def test_lowercasing(self):
        """Test that keywords are lowercased."""
        result = extract_keywords("STARBUCKS Coffee")
        assert "starbucks" in result
        assert "coffee" in result

    def test_short_tokens_removed(self):
        """Test that tokens shorter than 3 characters are removed."""
        result = extract_keywords("BP Gas UK")
        assert "gas" in result
        assert "bp" not in result
        assert "uk" not in result

    def test_stop_words_removed(self):
        """Test that common stop words are filtered out."""
        result = extract_keywords("payment for the coffee")
        assert "coffee" in result
        assert "payment" not in result
        assert "the" not in result
        assert "for" not in result

    def test_punctuation_handling(self):
        """Test that punctuation is stripped."""
        result = extract_keywords("MCDONALD'S - LONDON")
        assert "mcdonald" in result
        assert "london" in result

    def test_empty_string(self):
        """Test empty string returns empty list."""
        assert extract_keywords("") == []

    def test_none_input(self):
        """Test None input returns empty list."""
        assert extract_keywords(None) == []

    def test_numbers_preserved(self):
        """Test that numeric tokens are preserved if long enough."""
        result = extract_keywords("REF 12345 PAYMENT")
        assert "12345" in result

    def test_mixed_alphanumeric(self):
        """Test mixed alphanumeric tokens."""
        result = extract_keywords("AMAZON PRIME 2024")
        assert "amazon" in result
        assert "prime" in result
        assert "2024" in result

    def test_transaction_stop_words(self):
        """Test that transaction-specific stop words are removed."""
        result = extract_keywords("DEBIT CARD PURCHASE LIDL")
        assert "lidl" in result
        assert "debit" not in result
        assert "card" not in result
        assert "purchase" not in result
