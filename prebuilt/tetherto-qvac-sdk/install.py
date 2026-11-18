"""Install the intact platform wheel and check native worker addons."""

import os
from pathlib import Path
import subprocess
import sys
import sysconfig

wheel, = Path.cwd().glob("tetherto_qvac_sdk-*.whl")
subprocess.run(
    [sys.executable, "-m", "pip", "install", "--no-deps", "--no-build-isolation", str(wheel)],
    check=True,
)
if sys.platform == "linux":
    # Check every ELF file, including native addons without a .so suffix.
    package = Path(sysconfig.get_paths()["purelib"]) / "tetherto/qvac_sdk"
    binaries = []
    for path in sorted(package.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        with path.open("rb") as stream:
            if stream.read(4) == b"\x7fELF":
                binaries.append(str(path))
    if not binaries:
        raise RuntimeError("No ELF binaries found in the Linux wheel")
    print(f"Checking {len(binaries)} ELF binaries against glibc {os.environ['c_stdlib_version']}", flush=True)
    subprocess.run(["check-glibc", *binaries], check=True)
