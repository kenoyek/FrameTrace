"""Execute pure-Java native intake tests, without an Android runtime or a fake pass."""

import pathlib
import subprocess
import tempfile

from build_android import find_jdk17

ROOT = pathlib.Path(__file__).resolve().parents[1]
ANDROID = ROOT / "apps/mobile/modules/frametrace-share/android/src"


def main():
    jdk = find_jdk17()
    with tempfile.TemporaryDirectory(prefix="frametrace-jvm-") as directory:
        sources = [
            ANDROID / "main/java/expo/modules/frametraceshare/SharePolicy.java",
            ANDROID / "test/java/expo/modules/frametraceshare/SharePolicyTest.java",
        ]
        subprocess.run(
            [str(jdk / "bin/javac"), "-d", directory, *map(str, sources)], check=True
        )
        subprocess.run(
            [
                str(jdk / "bin/java"),
                "-ea",
                "-cp",
                directory,
                "expo.modules.frametraceshare.SharePolicyTest",
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
