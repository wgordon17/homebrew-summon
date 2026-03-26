"""Swap specific sdist resources to pure-Python wheels in a Homebrew formula.

Some PyPI packages ship broken sdists (e.g. missing README.md). This script
replaces those specific resource blocks with their py3-none-any wheel.

With --platform, it handles packages that have NO sdist at all (only
platform-specific wheels). It replaces the RESOURCE-ERROR comment left by
`brew update-python-resources --ignore-errors` with a proper resource block
using the macOS ARM wheel.

Usage:
  python3 prefer_wheels.py <formula-file> <package> [<package> ...]
  python3 prefer_wheels.py --platform <formula-file> <package> [<package> ...]
"""

import json
import re
import sys
import urllib.request


# Wheel tag pattern for macOS ARM (matches arm64 and universal2)
_MACOS_ARM_RE = re.compile(r"py3[^-]*-none-macosx_\d+_\d+_(arm64|universal2)\.whl$")


def _fetch_pypi(pkg: str) -> dict | None:
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{pkg}/json") as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"WARNING: could not fetch PyPI metadata for {pkg}: {e}", file=sys.stderr)
        return None


def swap_to_wheel(content: str, pkg: str) -> str:
    """Replace a single resource block's sdist with its pure-Python wheel."""
    data = _fetch_pypi(pkg)
    if not data:
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


def resolve_platform_wheel(content: str, pkg: str) -> str:
    """Replace a RESOURCE-ERROR comment with a macOS ARM wheel resource block.

    brew update-python-resources --ignore-errors leaves comments like:
      # RESOURCE-ERROR: Unable to resolve "playwright==1.58.0" (...)
    This function replaces that comment with a proper resource block.
    """
    data = _fetch_pypi(pkg)
    if not data:
        return content

    # Prefer arm64, fall back to universal2
    wheel = next(
        (
            u
            for u in data.get("urls", [])
            if u["packagetype"] == "bdist_wheel"
            and _MACOS_ARM_RE.search(u["filename"])
            and "arm64" in u["filename"]
        ),
        None,
    )
    if not wheel:
        wheel = next(
            (
                u
                for u in data.get("urls", [])
                if u["packagetype"] == "bdist_wheel"
                and _MACOS_ARM_RE.search(u["filename"])
            ),
            None,
        )
    if not wheel:
        print(f"WARNING: no macOS ARM wheel found for {pkg}", file=sys.stderr)
        return content

    whl_url = wheel["url"]
    whl_sha = wheel["digests"]["sha256"]

    # Match the RESOURCE-ERROR comment for this package
    error_re = re.compile(
        rf'^\s*# RESOURCE-ERROR:.*"{re.escape(pkg)}==.*\n',
        re.MULTILINE,
    )

    resource_block = (
        f'  resource "{pkg}" do\n'
        f'    url "{whl_url}"\n'
        f'    sha256 "{whl_sha}"\n'
        f"  end\n"
    )

    new_content = error_re.sub(resource_block, content)
    if new_content != content:
        print(f"Resolved {pkg} to macOS ARM wheel")
    else:
        print(f"WARNING: no RESOURCE-ERROR comment found for {pkg}", file=sys.stderr)

    return new_content


def main():
    args = sys.argv[1:]
    platform_mode = False

    if args and args[0] == "--platform":
        platform_mode = True
        args = args[1:]

    if len(args) < 2:
        print(
            f"Usage: {sys.argv[0]} [--platform] <formula-file> <package> [<package> ...]",
            file=sys.stderr,
        )
        sys.exit(1)

    formula = args[0]
    packages = args[1:]

    with open(formula) as f:
        content = f.read()

    for pkg in packages:
        if platform_mode:
            content = resolve_platform_wheel(content, pkg)
        else:
            content = swap_to_wheel(content, pkg)

    with open(formula, "w") as f:
        f.write(content)


if __name__ == "__main__":
    main()
