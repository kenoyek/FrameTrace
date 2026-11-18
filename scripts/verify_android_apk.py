"""Verify an actual test APK, without claiming installation/device acceptance."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path


def check_contents(path, standalone):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("APK ZIP checksum failure")
        names = set(archive.namelist())
        if not {"AndroidManifest.xml", "classes.dex"} <= names:
            raise ValueError("Missing Android manifest or application bytecode")
        if not any(
            name.startswith("lib/arm64-v8a/") and name.endswith(".so") for name in names
        ):
            raise ValueError("Missing ARM64 native libraries")
        if standalone and "assets/index.android.bundle" not in names:
            raise ValueError(
                "Standalone preview is missing its embedded JavaScript bundle"
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument(
        "--variant", choices=["debug", "internal-preview"], required=True
    )
    parser.add_argument("--build-tools", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    standalone = args.variant == "internal-preview"
    check_contents(args.apk, standalone)
    signing = subprocess.run(
        [
            str(args.build_tools / "apksigner"),
            "verify",
            "--verbose",
            "--print-certs",
            str(args.apk),
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if "CN=Android Debug" not in signing:
        raise ValueError("Expected Android development signing certificate")
    badging = subprocess.run(
        [str(args.build_tools / "aapt"), "dump", "badging", str(args.apk)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if not re.search(
        r"^package: name='app\.frametrace\.mobile'", badging, re.MULTILINE
    ):
        raise ValueError("Unexpected application ID")
    if standalone and "application-debuggable" in badging:
        raise ValueError("Internal preview should use the bundled release variant")
    if not standalone and "application-debuggable" not in badging:
        raise ValueError("Development APK must be debuggable")
    with args.apk.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "file": args.apk.name,
                "sha256": digest,
                "variant": args.variant,
                "application_id": "app.frametrace.mobile",
                "architecture": "arm64-v8a",
                "requires_metro": not standalone,
                "development_signed": True,
                "source_revision": os.environ.get("GITHUB_SHA"),
                "installed_or_device_tested": False,
                "api_configured": bool(os.environ.get("EXPO_PUBLIC_API_URL")),
            },
            indent=2,
        )
        + "\n"
    )
    print(
        f"Verified {args.apk.name}: development signature, package, ARM64 and bundle policy. SHA256 {digest}"
    )


if __name__ == "__main__":
    main()
