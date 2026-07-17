"""`sdplugin-verify` — pre-publication gate for a Stream Deck plugin.

    sdplugin-verify <UUID>.sdPlugin                # verify a plugin directory
    sdplugin-verify dist/foo.streamDeckPlugin      # verify the shipped bytes
    sdplugin-verify <plugin> --strict              # warnings become blocking
    sdplugin-verify <plugin> --foreign bluetooth,vpn   # override foreign terms

Exit non-zero on any ERROR (or any WARN under --strict).
"""
import argparse
import sys
from pathlib import Path

from . import __version__, spec
from .verify import (verify, verify_container, print_report, has_blocking)


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="sdplugin-verify",
        description="Pre-publication verifier for Elgato Stream Deck plugins.")
    p.add_argument("--version", action="version",
                   version=f"sdplugin-verify {__version__}")
    p.add_argument("target",
                   help="a <UUID>.sdPlugin directory OR a .streamDeckPlugin file")
    p.add_argument("--strict", action="store_true",
                   help="treat warnings as blocking")
    p.add_argument("--foreign",
                   help="comma-separated foreign feature terms to forbid "
                        "(default: auto — every known term the plugin doesn't own)")
    args = p.parse_args(argv)

    foreign = args.foreign.split(",") if args.foreign else None
    t = Path(args.target)
    if t.is_file() and t.name.endswith(".streamDeckPlugin"):
        findings = verify_container(args.target, foreign=foreign)
    else:
        findings = verify(args.target, foreign=foreign)
    print_report(args.target, findings, strict=args.strict)
    sys.exit(1 if has_blocking(findings, strict=args.strict) else 0)


if __name__ == "__main__":
    main()
