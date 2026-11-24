"""Small security helpers (no Streamlit import, so they are unit-testable)."""
import hmac


def verify_password(entered: str, expected: str | None) -> bool:
    """Constant-time password check. An unset/empty expected password never matches."""
    if not expected or not entered:
        return False
    return hmac.compare_digest(entered.encode("utf-8"), expected.encode("utf-8"))
