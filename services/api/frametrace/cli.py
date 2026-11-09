import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

from .config import settings
from .db import Reference, Session, initialize
from .media import extract


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
    sub.add_parser("cleanup")
    args = parser.parse_args()
    initialize()
    if args.command == "cleanup":
        from .app import cleanup

        cleanup()
        return
    with Session() as db:
        if args.command == "revoke":
            reference = db.get(Reference, args.id)
            if reference is None:
                parser.error("Unknown reference ID")
            reference.revoked = True
            db.commit()
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
            )
        )
        db.commit()
        print(json.dumps({"id": digest, "frames": len(fingerprints), "duration": duration}))


if __name__ == "__main__":
    main()
