from datetime import date

import pytest

from app.core.transaction_parser import parse_transaction_input

TODAY = date(2026, 4, 1)

EXPENSE_SLUGS: set[str] = {
    "fuel",
    "groceries",
    "food",
    "shopping",
    "entertainment",
    "utilities",
    "health",
    "travel",
    "education",
    "personal-care",
    "housing",
    "insurance",
    "subscriptions",
    "electronics",
    "gifts",
    "taxes",
    "other-expense",
}

INCOME_SLUGS: set[str] = {
    "salary",
    "freelance",
    "business",
    "investment-returns",
    "rental",
    "interest",
    "dividends",
    "gift-received",
    "refund",
    "other-income",
}


# ── Acceptance-criteria cases ──────────────────────────────────────────────────


def test_simple_expense_amount_first():
    """'500 fuel' → expense, 500, category=fuel, merchant=fuel"""
    result = parse_transaction_input("500 fuel", EXPENSE_SLUGS, INCOME_SLUGS, TODAY)
    assert result.transaction_type == "expense"
    assert result.amount == 500.0
    assert result.category_slug == "fuel"
    assert result.merchant == "fuel"
    assert result.transacted_on == TODAY


def test_income_category_first():
    """'salary 50000' → income, 50000, category=salary"""
    result = parse_transaction_input("salary 50000", EXPENSE_SLUGS, INCOME_SLUGS, TODAY)
    assert result.transaction_type == "income"
    assert result.amount == 50000.0
    assert result.category_slug == "salary"


def test_expense_with_merchant_and_category():
    """'1200 amazon shopping' → expense, 1200, merchant=amazon, category=shopping"""
    result = parse_transaction_input(
        "1200 amazon shopping", EXPENSE_SLUGS, INCOME_SLUGS, TODAY
    )
    assert result.transaction_type == "expense"
    assert result.amount == 1200.0
    assert result.category_slug == "shopping"
    assert result.merchant == "amazon"
    assert result.description == "amazon"


def test_no_category_match():
    """'random stuff 99' → expense, 99, description='random stuff', category=None"""
    result = parse_transaction_input(
        "random stuff 99", EXPENSE_SLUGS, INCOME_SLUGS, TODAY
    )
    assert result.transaction_type == "expense"
    assert result.amount == 99.0
    assert result.description == "random stuff"
    assert result.category_slug is None
    assert result.merchant is None


def test_amount_only():
    """'500' → expense, 500, description='', category=None"""
    result = parse_transaction_input("500", EXPENSE_SLUGS, INCOME_SLUGS, TODAY)
    assert result.transaction_type == "expense"
    assert result.amount == 500.0
    assert result.description == ""
    assert result.category_slug is None
    assert result.merchant is None


def test_income_with_extra_text():
    """'income 5000 freelance' → income, 5000, category=freelance"""
    result = parse_transaction_input(
        "income 5000 freelance", EXPENSE_SLUGS, INCOME_SLUGS, TODAY
    )
    assert result.transaction_type == "income"
    assert result.amount == 5000.0
    assert result.category_slug == "freelance"


def test_missing_amount_raises():
    """No numeric token → ValueError"""
    with pytest.raises(ValueError, match="No numeric amount found"):
        parse_transaction_input("fuel random stuff", EXPENSE_SLUGS, INCOME_SLUGS)


# ── Additional edge cases ──────────────────────────────────────────────────────


def test_float_amount():
    result = parse_transaction_input("1200.50 food", EXPENSE_SLUGS, INCOME_SLUGS, TODAY)
    assert result.amount == 1200.50
    assert result.category_slug == "food"


def test_amount_at_end():
    result = parse_transaction_input(
        "groceries 850 bigbasket", EXPENSE_SLUGS, INCOME_SLUGS, TODAY
    )
    assert result.transaction_type == "expense"
    assert result.amount == 850.0
    assert result.category_slug == "groceries"
    assert result.merchant == "bigbasket"
    assert result.description == "bigbasket"


def test_unknown_category_tokens_become_description():
    """Two unknown tokens → description, no merchant."""
    result = parse_transaction_input(
        "99 random stuff", EXPENSE_SLUGS, INCOME_SLUGS, TODAY
    )
    assert result.category_slug is None
    assert result.description == "random stuff"
    assert result.merchant is None


def test_income_merchant_is_none():
    """Income transactions should not populate merchant."""
    result = parse_transaction_input(
        "50000 salary bonus", EXPENSE_SLUGS, INCOME_SLUGS, TODAY
    )
    assert result.transaction_type == "income"
    assert result.category_slug == "salary"
    assert result.merchant is None


def test_default_today_used_when_not_provided():
    """When today is not supplied, transacted_on is date.today()."""
    from datetime import date as _date

    result = parse_transaction_input("100 food", EXPENSE_SLUGS, INCOME_SLUGS)
    assert result.transacted_on == _date.today()


def test_income_slug_takes_priority_over_expense():
    """If a token matches income, it should not be treated as expense."""
    mixed_expense = EXPENSE_SLUGS | {"salary"}  # salary also in expense (hypothetical)
    result = parse_transaction_input(
        "salary 30000", mixed_expense, INCOME_SLUGS, TODAY
    )
    assert result.transaction_type == "income"
    assert result.category_slug == "salary"


def test_category_slug_lowercased():
    """Token matching is case-insensitive."""
    result = parse_transaction_input("500 FUEL", EXPENSE_SLUGS, INCOME_SLUGS, TODAY)
    assert result.category_slug == "fuel"
    assert result.transaction_type == "expense"


def test_integer_like_float_amount():
    """'500.0' is a valid amount."""
    result = parse_transaction_input(
        "500.0 groceries", EXPENSE_SLUGS, INCOME_SLUGS, TODAY
    )
    assert result.amount == 500.0
