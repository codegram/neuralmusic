from pathlib import Path

__all__ = ["test_eq", "path"]


def test_eq(a, b):
    assert a == b, f"Expected {a}, got {b}"


def path(p: str) -> str:
    if Path(p).exists():
        return p
    elif Path(f"nbs/{p}").exists():
        return f"nbs/{p}"
    else:
        raise f"Could not find {p} in nbs"
