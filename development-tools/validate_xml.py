import sys
import os
from pathlib import Path

try:
    from lxml import etree  # type: ignore
    _PARSER = "lxml"
except Exception:
    import xml.etree.ElementTree as etree  # fallback
    _PARSER = "stdlib"


def validate_xml(file_path: str) -> bool:
    try:
        # lxml and stdlib expose parse with similar signature
        etree.parse(file_path)
        print(f"OK [{_PARSER}]: {file_path}")
        return True
    except Exception as e:  # broad to cover both libs
        print(f"ERROR: {file_path}: {e}")
        return False


def main(argv: list[str]) -> int:
    # If a path is provided, validate just that; otherwise, scan common XML folders
    if len(argv) >= 2:
        return 0 if validate_xml(argv[1]) else 1

    root = Path(__file__).resolve().parents[1]
    xml_dirs = [
        root / "records_management" / "views",
        root / "records_management" / "security",
        root / "records_management" / "report",
        root / "records_management_fsm" / "views",
        root / "addons",
    ]

    any_errors = False
    for base in xml_dirs:
        if not base.exists():
            continue
        for path in base.rglob("*.xml"):
            ok = validate_xml(str(path))
            any_errors = any_errors or (not ok)

    return 1 if any_errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
