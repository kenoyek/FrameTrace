"""Build the ARM64 development APK using an installed SDK and verified Gradle ZIP.

Run prebuild first. Proxy/CA adapters preserve inherited settings; no TLS bypass or
production signing is used. Gradle dependencies/caches stay outside the checkout.
"""

import os
import pathlib
import shlex
import shutil
import subprocess
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]


def find_jdk17():
    candidates = [os.environ.get("FRAMETRACE_JDK17_HOME"), os.environ.get("JAVA_HOME")]
    candidates += [
        str(path)
        for path in pathlib.Path("/workspace/.cache/frametrace-jdk17").glob("jdk-*")
    ]
    compiler = shutil.which("javac")
    if compiler:
        candidates.append(str(pathlib.Path(compiler).resolve().parents[1]))
    for candidate in candidates:
        if not candidate:
            continue
        home = pathlib.Path(candidate)
        release = home / "release"
        if (
            (home / "bin/javac").is_file()
            and release.is_file()
            and 'JAVA_VERSION="17.' in release.read_text()
        ):
            return home
    raise SystemExit(
        "Install full JDK 17 and set FRAMETRACE_JDK17_HOME; a Java runtime alone is insufficient."
    )


def main():
    android = ROOT / "apps/mobile/android"
    if not (android / "gradlew").is_file():
        raise SystemExit("Run Expo prebuild --no-install first (DEVELOPMENT.md).")
    env = os.environ.copy()
    env["JAVA_HOME"] = str(find_jdk17())
    sdk = pathlib.Path(env.get("ANDROID_HOME", "/workspace/.cache/android-sdk"))
    if not (sdk / "platforms/android-37.0/android.jar").exists():
        raise SystemExit("Install the official Android 37.0 SDK platform first.")
    env["ANDROID_HOME"] = str(sdk)
    env["ANDROID_USER_HOME"] = env.get(
        "ANDROID_USER_HOME", "/workspace/.cache/android-user"
    )
    cache = pathlib.Path(
        env.get("GRADLE_USER_HOME", "/workspace/.cache/frametrace-gradle")
    )
    cache.mkdir(parents=True, exist_ok=True)
    env["GRADLE_USER_HOME"] = str(cache)
    env["CMAKE_BUILD_PARALLEL_LEVEL"] = "2"
    options = []
    for protocol in ["http", "https"]:
        proxy = env.get(protocol.upper() + "_PROXY") or env.get(protocol + "_proxy")
        if proxy:
            parsed = urllib.parse.urlparse(proxy)
            if parsed.username or parsed.password:
                raise SystemExit(
                    "Use an approved authenticated proxy configuration; this helper does not persist proxy credentials."
                )
            if parsed.hostname:
                options += [
                    f"-D{protocol}.proxyHost={parsed.hostname}",
                    f"-D{protocol}.proxyPort={parsed.port or 80}",
                ]
    exclusions = "|".join(
        part.strip().replace("::1", "[::1]")
        for part in env.get("NO_PROXY", "").split(",")
        if part.strip()
    )
    if exclusions:
        options += [f"-Dhttp.nonProxyHosts={exclusions}"]
    cert = env.get("CODEX_PROXY_CERT")
    if cert:
        java = pathlib.Path(env["JAVA_HOME"]) / "bin/java"
        trust = cache / "frametrace-public-cacerts"
        shutil.copyfile(java.parents[1] / "lib/security/cacerts", trust)
        subprocess.run(
            [
                str(pathlib.Path(env["JAVA_HOME"]) / "bin/keytool"),
                "-importcert",
                "-noprompt",
                "-trustcacerts",
                "-alias",
                "frametrace-cloud-proxy",
                "-file",
                cert,
                "-keystore",
                str(trust),
                "-storepass",
                "changeit",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        options += [
            f"-Djavax.net.ssl.trustStore={trust}",
            "-Djavax.net.ssl.trustStorePassword=changeit",
        ]
    env["GRADLE_OPTS"] = env.get("GRADLE_OPTS", "") + " " + shlex.join(options)
    # Both wrapper bootstrap and dependency resolution need the supplied proxy/CA.
    props = cache / "gradle.properties"
    additions = ["systemProp." + option[2:] for option in options]
    managed_keys = {line.split("=", 1)[0] for line in additions}
    retained = (
        [
            line
            for line in props.read_text().splitlines()
            if line.split("=", 1)[0] not in managed_keys
        ]
        if props.exists()
        else []
    )
    props.write_text("\n".join(retained + additions) + "\n")
    wrapper = android / "gradle/wrapper/gradle-wrapper.properties"
    content = wrapper.read_text()
    if "gradle-9.4.1-bin.zip" not in content:
        raise SystemExit("Review the build helper after a Gradle version change.")
    checksum_url = (
        "https://services.gradle.org/distributions/gradle-9.4.1-bin.zip.sha256"
    )
    with urllib.request.urlopen(checksum_url, timeout=30) as response:
        digest = response.read().decode().strip()
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise SystemExit("Invalid official Gradle checksum response.")
    if "distributionSha256Sum=" not in content:
        wrapper.write_text(content + "\ndistributionSha256Sum=" + digest + "\n")
    elif "distributionSha256Sum=" + digest not in content:
        raise SystemExit(
            "Existing wrapper checksum differs; investigate without replacing it."
        )
    subprocess.run(
        [
            str(android / "gradlew"),
            ":app:assembleDebug",
            "--no-daemon",
            "--max-workers=2",
            "-PreactNativeArchitectures=arm64-v8a",
            "-Dorg.gradle.jvmargs=-Xmx4g -XX:MaxMetaspaceSize=1g",
        ],
        cwd=android,
        env=env,
        check=True,
    )


if __name__ == "__main__":
    main()
