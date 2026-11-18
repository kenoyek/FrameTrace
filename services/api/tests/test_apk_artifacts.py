"""ZIP-policy unit checks; these fixtures are not installable Android applications."""

import importlib.util
import zipfile
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "verify_android_apk", Path(__file__).parents[3] / "scripts/verify_android_apk.py"
)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def archive(path, entries):
    with zipfile.ZipFile(path, "w") as output:
        for name in entries:
            output.writestr(name, b"unit-test-placeholder")
    return path


def test_standalone_policy_requires_embedded_bundle(tmp_path):
    path = archive(
        tmp_path / "fixture.zip", ["AndroidManifest.xml", "classes.dex", "lib/arm64-v8a/libtest.so"]
    )
    verifier.check_contents(path, standalone=False)
    with pytest.raises(ValueError, match="embedded"):
        verifier.check_contents(path, standalone=True)


def test_standalone_structure_accepts_bundle_but_does_not_assert_signature(tmp_path):
    path = archive(
        tmp_path / "fixture.zip",
        [
            "AndroidManifest.xml",
            "classes.dex",
            "lib/arm64-v8a/libtest.so",
            "assets/index.android.bundle",
        ],
    )
    verifier.check_contents(path, standalone=True)


@pytest.mark.parametrize(
    "entries", [[], ["classes.dex"], ["AndroidManifest.xml", "classes.dex", "lib/x86/libtest.so"]]
)
def test_rejects_missing_manifest_bytecode_or_arm64(tmp_path, entries):
    with pytest.raises(ValueError):
        verifier.check_contents(archive(tmp_path / "fixture.zip", entries), standalone=False)


def test_rejects_non_zip_output(tmp_path):
    path = tmp_path / "fixture.zip"
    path.write_bytes(b"failed build log")
    with pytest.raises(zipfile.BadZipFile):
        verifier.check_contents(path, standalone=False)
