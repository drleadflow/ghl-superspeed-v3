#!/usr/bin/env python3
"""
Apply a value-map JSON to a GHL location's A2P custom values.

Usage:
  python3 scripts/a2p_apply.py <location_id> <value_map.json> [--dry-run] [--refresh-token=TOKEN]

  <value_map.json>   a JSON object {slug: value, ...}; only the 18 A2P slugs are used.
  --dry-run          classify create/update/skip without writing anything.
  --refresh-token    a client's GHL Firebase refresh token (for non-DLF agency
                     sub-accounts); defaults to $GHL_FIREBASE_REFRESH_TOKEN.

Exit codes: 0 = ok, 1 = one or more values errored, 2 = bad arguments / unreadable value map.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.a2p_values import make_client, apply_values  # noqa: E402

_FLAG_FACTS = ("business_profile__legal_business_name", "business_profile__phone_number", "from_email")


def _parse_args(argv):
    ap = argparse.ArgumentParser(prog="a2p_apply.py", add_help=True)
    ap.add_argument("location_id")
    ap.add_argument("value_map", help="path to JSON file: {slug: value, ...}")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh-token", dest="refresh_token",
                    default=os.environ.get("GHL_FIREBASE_REFRESH_TOKEN", "") or None)
    return ap.parse_args(argv)


def _print_report(report, dry_run):
    tag = "[DRY RUN] " if dry_run else ""
    print("\n%sA2P custom values — %d value(s) to write\n" % (tag, len(report["resolved"])))
    for slug in report["created"]:
        print("  + create  %-40s = %r" % (slug, report["resolved"].get(slug, "")[:80]))
    for slug in report["updated"]:
        print("  ~ update  %-40s = %r" % (slug, report["resolved"].get(slug, "")[:80]))
    for slug, reason in report["skipped"]:
        print("  . skip    %-40s (%s)" % (slug, reason))
    for slug, msg in report["errors"]:
        print("  ! ERROR   %-40s %s" % (slug, msg))
    blanks = {s for s, _r in report["skipped"]}
    flagged = [s for s in _FLAG_FACTS if s in blanks]
    if flagged:
        print("\n  /!\\ set these manually (not derivable from URL/brief): %s" % ", ".join(flagged))
    print("\n  created=%d updated=%d skipped=%d errors=%d\n" % (
        len(report["created"]), len(report["updated"]), len(report["skipped"]), len(report["errors"])))


def main(argv):
    args = _parse_args(argv)
    try:
        with open(args.value_map) as f:
            value_map = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print("ERROR: cannot read value map %s: %s" % (args.value_map, e), file=sys.stderr)
        return 2
    if not isinstance(value_map, dict):
        print("ERROR: value map must be a JSON object {slug: value, ...}", file=sys.stderr)
        return 2
    client = make_client(args.location_id, refresh_token=args.refresh_token)
    report = apply_values(client, args.location_id, value_map, dry_run=args.dry_run)
    _print_report(report, args.dry_run)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
