"""SQL utility helpers for safe query building."""


def escape_like(value: str) -> str:
    """Escape SQL LIKE wildcards (%, _) in user input to prevent injection.

    Usage:
        User.email.ilike(f"%{escape_like(search)}%")
    """
    return (
        value
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
