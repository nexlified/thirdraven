from dataclasses import dataclass
from datetime import date


@dataclass
class ParsedTransaction:
    transaction_type: str  # "expense" | "income"
    amount: float
    description: str
    category_slug: str | None
    merchant: str | None
    transacted_on: date


def parse_transaction_input(
    text: str,
    known_expense_slugs: set[str],
    known_income_slugs: set[str],
    today: date | None = None,
) -> ParsedTransaction:
    """Parse a natural-language transaction shorthand into a ParsedTransaction.

    Algorithm:
    1. Tokenize on whitespace.
    2. Find the first numeric token as the amount.
    3. Check remaining tokens against income slugs, then expense slugs, to
       determine transaction type and category.
    4. Join leftover tokens as description; if exactly one is left it also
       becomes the merchant.  When the category token was the only non-amount
       token it doubles as the merchant (expense only).

    Raises ValueError if no numeric token is found.
    """
    if today is None:
        today = date.today()

    tokens = text.strip().split()

    # ── 1. Find amount token (first numeric token) ─────────────────────────────
    amount: float | None = None
    amount_idx: int | None = None
    for i, token in enumerate(tokens):
        try:
            amount = float(token)
            amount_idx = i
            break
        except ValueError:
            continue

    if amount is None or amount_idx is None:
        raise ValueError("No numeric amount found in input")

    rest_tokens = [t for i, t in enumerate(tokens) if i != amount_idx]

    # ── 2. Detect category / transaction type ──────────────────────────────────
    transaction_type = "expense"
    category_slug: str | None = None
    category_idx: int | None = None

    for i, token in enumerate(rest_tokens):
        if token.lower() in known_income_slugs:
            transaction_type = "income"
            category_slug = token.lower()
            category_idx = i
            break

    if category_slug is None:
        for i, token in enumerate(rest_tokens):
            if token.lower() in known_expense_slugs:
                transaction_type = "expense"
                category_slug = token.lower()
                category_idx = i
                break

    if category_idx is not None:
        rest_tokens = [t for i, t in enumerate(rest_tokens) if i != category_idx]

    # ── 3. Build description and merchant ──────────────────────────────────────
    description = " ".join(rest_tokens)

    merchant: str | None = None
    if transaction_type == "expense":
        if not rest_tokens and category_slug is not None:
            # The category was the only non-amount token; treat it as merchant too.
            merchant = category_slug
        elif len(rest_tokens) == 1:
            merchant = rest_tokens[0]

    return ParsedTransaction(
        transaction_type=transaction_type,
        amount=amount,
        description=description,
        category_slug=category_slug,
        merchant=merchant,
        transacted_on=today,
    )
