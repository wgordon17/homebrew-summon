"""Swap specific sdist resources to pure-Python wheels in a Homebrew formula.

Some PyPI packages ship broken sdists (e.g. missing README.md). This script
replaces those specific resource blocks with their py3-none-any wheel.

Usage: python3 prefer_wheels.py <formula-file> <package> [<package> ...]
"""

import json
import re
import sys
import urllib.request


def swap_to_wheel(content: str, pkg: str) -> str:
    """Replace a single resource block's sdist with its pure-Python wheel."""
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{pkg}/json") as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"WARNING: could not fetch PyPI metadata for {pkg}: {e}", file=sys.stderr)
        return content

    wheel = next(
        (
            u
            for u in data.get("urls", [])
            if u["packagetype"] == "bdist_wheel"
            and re.search(r"py3[^-]*-none-any\.whl$", u["filename"])
        ),
        None,
    )
    if not wheel:
        print(f"WARNING: no pure-Python wheel found for {pkg}", file=sys.stderr)
        return content

    whl_url = wheel["url"]
    whl_sha = wheel["digests"]["sha256"]

    block_re = re.compile(
        rf'(resource "{re.escape(pkg)}" do\s*\n)'
        rf'(\s*url )"[^"]*"(.*?\n)'
        rf'(\s*sha256 )"[^"]*"',
        re.DOTALL,
    )
    new_content = block_re.sub(
        rf'\g<1>\g<2>"{whl_url}"\g<3>\g<4>"{whl_sha}"',
        content,
    )
    if new_content != content:
        print(f"Switched {pkg} to wheel")
    else:
        print(f"WARNING: {pkg} not found in formula", file=sys.stderr)

    return new_content


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <formula-file> <package> [<package> ...]", file=sys.stderr)
        sys.exit(1)

    formula = sys.argv[1]
    packages = sys.argv[2:]

    with open(formula) as f:
        content = f.read()

    for pkg in packages:
        content = swap_to_wheel(content, pkg)

    with open(formula, "w") as f:
        f.write(content)


if __name__ == "__main__":
    main()
