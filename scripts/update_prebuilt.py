"""Update the SDK recipe from stable GitHub releases (standard library only)."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "prebuilt/tetherto-qvac-sdk/recipe.yaml"
API = "https://api.github.com/repos/tetherto/qvac/releases"
TAG = re.compile(r"sdk-v(\d+\.\d+\.\d+)\Z")
BLOCK = re.compile(r"(?<=  # BEGIN RELEASE - maintained by scripts/update_prebuilt.py\n).*?(?=  # END RELEASE)", re.S)
PLATFORMS = {
    "linux_64": r"manylinux_(\d+)_(\d+)_x86_64",
    "linux_aarch64": r"manylinux_(\d+)_(\d+)_aarch64",
    "osx_arm64": r"macosx_(\d+)_(\d+)_arm64",
    "win_64": r"win_amd64",
}


def version_key(version):
    return tuple(map(int, version.split(".")))


def request(url, *, authenticated=False):
    headers = {"User-Agent": "qvac-conda-release-updater"}
    if authenticated and os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120)


def releases():
    # Do not use /latest: this repo contains releases for more than one product.
    page = 1
    while True:
        with request(f"{API}?per_page=100&page={page}", authenticated=True) as response:
            batch = json.load(response)
        if not batch:
            return
        yield from batch
        page += 1


def latest_release(items, current):
    stable = [r for r in items if not r.get("draft") and not r.get("prerelease") and TAG.fullmatch(r["tag_name"])]
    if not stable:
        raise ValueError("No stable SDK releases found")
    latest = max(stable, key=lambda r: version_key(TAG.fullmatch(r["tag_name"])[1]))
    version = TAG.fullmatch(latest["tag_name"])[1]
    return latest if version_key(version) > version_key(current) else None


def checksum(asset):
    digest = asset.get("digest") or ""
    if re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        return digest.removeprefix("sha256:")
    # Older GitHub releases may not provide a digest. Hash the bytes in that case.
    digest = hashlib.sha256()
    with request(asset["browser_download_url"]) as response:
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def release_context(release):
    version = TAG.fullmatch(release["tag_name"])[1]
    context = {"version": version, "build_number": 0}
    minimums = {}
    for platform, pattern in PLATFORMS.items():
        wheel_pattern = re.compile(rf"tetherto_qvac_sdk-{re.escape(version)}-py3-none-{pattern}\.whl\Z")
        matches = [(asset, wheel_pattern.fullmatch(asset["name"])) for asset in release["assets"]]
        matches = [(a, m) for a, m in matches if m]
        if len(matches) != 1:
            raise ValueError(f"Expected one {platform} wheel for {version}, found {len(matches)}; refusing a partial update")
        asset, match = matches[0]
        expected_url = f"https://github.com/tetherto/qvac/releases/download/sdk-v{version}/{asset['name']}"
        if asset["browser_download_url"] != expected_url:
            raise ValueError(f"Unexpected download URL: {asset['browser_download_url']}")
        context[f"wheel_{platform}"] = asset["name"]
        context[f"sha256_{platform}"] = checksum(asset)
        if match.groups():
            minimums[platform] = ".".join(match.groups())
    if minimums["linux_64"] != minimums["linux_aarch64"]:
        raise ValueError("Linux wheels have different glibc requirements; update the recipe manually")
    context["minimum_glibc"] = minimums["linux_64"]
    context["minimum_osx"] = minimums["osx_arm64"]
    return context


def updated_recipe(text, release):
    if len(BLOCK.findall(text)) != 1:
        raise ValueError("Expected exactly one managed release block")
    context = release_context(release)
    block = "".join(f"  {key}: {json.dumps(value)}\n" for key, value in context.items())
    return BLOCK.sub(lambda _: block, text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--releases-json", type=Path, help="Use saved API data instead of the network")
    parser.add_argument("--dry-run", action="store_true", help="Print the candidate recipe without changing files")
    args = parser.parse_args()
    text = RECIPE.read_text()
    current = re.search(r'^  version: "(\d+\.\d+\.\d+)"$', text, re.M)[1]
    items = json.loads(args.releases_json.read_text()) if args.releases_json else releases()
    release = latest_release(items, current)
    if release is None:
        print(f"QVAC SDK {current} is up to date")
        return
    candidate = updated_recipe(text, release)
    version = TAG.fullmatch(release["tag_name"])[1]
    if args.dry_run:
        print(candidate, end="")
        return
    RECIPE.write_text(candidate)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"version={version}\n")
    print(f"Updated QVAC SDK {current} -> {version}")


if __name__ == "__main__":
    main()
