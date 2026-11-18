import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select

from .config import settings
from .db import Reference, Session, initialize
from .fingerprints import VERSION
from .media import extract
from .operations import audit_page, catalog_page, feedback_summary, record_catalog_event


def bounded_integer(minimum, maximum):
    def parse(value):
        try:
            number = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError("Must be an integer") from None
        if not minimum <= number <= maximum:
            raise argparse.ArgumentTypeError(f"Must be between {minimum} and {maximum}")
        return number

    return parse


def main():
    parser = argparse.ArgumentParser(description="Operator-only authorized catalog management")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest")
    ingest.add_argument("path", type=Path)
    ingest.add_argument("--title", required=True)
    ingest.add_argument("--publisher", required=True)
    ingest.add_argument("--rights-basis", required=True)
    ingest.add_argument("--source-url")
    revoke = sub.add_parser("revoke")
    revoke.add_argument("id")
    for command in (ingest, revoke):
        command.add_argument(
            "--actor", required=True, help="Local operator label (not verified identity)"
        )
    revoke.add_argument("--reason", required=True)
    catalog = sub.add_parser("catalog", help="List reference metadata without fingerprints")
    catalog.add_argument("--include-revoked", action="store_true")
    audit = sub.add_parser("catalog-audit", help="Review local catalog change records")
    audit.add_argument("--reference-id")
    for command in (catalog, audit):
        command.add_argument("--limit", type=bounded_integer(1, 100), default=20)
        command.add_argument("--offset", type=bounded_integer(0, 100000), default=0)
    summary = sub.add_parser(
        "feedback-summary", help="Aggregate retained feedback without user/job IDs"
    )
    summary.add_argument("--days", type=bounded_integer(1, 3650), default=30)
    sub.add_parser("cleanup")
    args = parser.parse_args()
    if args.command in {"ingest", "revoke"}:
        args.actor = args.actor.strip()
        if not 1 <= len(args.actor) <= 120:
            parser.error("Actor must contain 1–120 characters")
        if args.command == "revoke":
            args.reason = args.reason.strip()
            if not 1 <= len(args.reason) <= 500:
                parser.error("Reason must contain 1–500 characters")
    initialize()
    if args.command == "cleanup":
        from .lifecycle import cleanup

        cleanup()
        return
    with Session() as db:
        if args.command == "catalog":
            print(json.dumps(catalog_page(db, args.limit, args.offset, args.include_revoked)))
            return
        if args.command == "catalog-audit":
            print(json.dumps(audit_page(db, args.limit, args.offset, args.reference_id)))
            return
        if args.command == "feedback-summary":
            print(json.dumps(feedback_summary(db, args.days)))
            return
        if args.command == "revoke":
            reference = db.scalar(
                select(Reference).where(Reference.id == args.id).with_for_update()
            )
            if reference is None:
                parser.error("Unknown reference ID")
            if reference.revoked:
                print(json.dumps({"id": args.id, "revoked": True, "changed": False}))
                return
            reference.revoked = True
            record_catalog_event(db, args.id, "revoke", args.actor, args.reason)
            db.commit()
            print(json.dumps({"id": args.id, "revoked": True, "changed": True}))
            return
        if args.source_url:
            parsed = urlparse(args.source_url)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
            ):
                parser.error(
                    "Source links must be operator-verified HTTPS URLs without credentials."
                )
        if not all(value.strip() for value in [args.title, args.publisher, args.rights_basis]):
            parser.error("Title, publisher and rights basis must not be blank")
        duration, fingerprints = extract(args.path, settings.max_reference_seconds)
        if len(fingerprints) < 6:
            parser.error("Insufficient distinctive frames to index")
        with args.path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        existing = db.get(Reference, digest)
        if existing:
            parser.error("Reference already exists; revocation cannot be undone by ingestion")
        db.add(
            Reference(
                id=digest,
                title=args.title,
                publisher=args.publisher,
                rights_basis=args.rights_basis,
                source_url=args.source_url,
                duration=duration,
                fingerprints=fingerprints,
                fingerprint_version=VERSION,
            )
        )
        record_catalog_event(db, digest, "ingest", args.actor, "Authorized catalog ingestion")
        db.commit()
        print(json.dumps({"id": digest, "frames": len(fingerprints), "duration": duration}))


if __name__ == "__main__":
    main()
