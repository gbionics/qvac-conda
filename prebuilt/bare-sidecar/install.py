"""Install the upstream wheel, preserving the bundled Bare runtime."""

import os
from pathlib import Path
import subprocess
import sys
import zipfile

wheel, = Path.cwd().glob("bare_sidecar-*.whl")
with zipfile.ZipFile(wheel) as archive:
    metadata, = {name.split("/")[0] for name in archive.namelist() if name.endswith(".dist-info/METADATA")}
    for name in ("LICENSE", "NOTICE"):
        Path(name).write_bytes(archive.read(f"{metadata}/licenses/{name}"))

subprocess.run(
    [sys.executable, "-m", "pip", "install", "--no-deps", "--no-build-isolation", str(wheel)],
    check=True,
)

from bare_sidecar import executable

bare = executable()
if os.name != "nt":
    bare.chmod(bare.stat().st_mode | 0o111)
if sys.platform == "linux":
    subprocess.run(["check-glibc", str(bare)], check=True)
