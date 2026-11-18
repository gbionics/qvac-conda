"""Install the intact platform wheel, retaining executable bits for Bare."""

import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import zipfile

wheel, = Path.cwd().glob("tetherto_qvac_sdk-*.whl")
# The bundled QVAC packages carry the Apache license and upstream notice.
with zipfile.ZipFile(wheel) as archive:
    for name in ("LICENSE", "NOTICE"):
        member = f"tetherto/qvac_sdk/_bundle/worker/node_modules/@qvac/inference/{name}"
        Path(name).write_bytes(archive.read(member))

subprocess.run(
    [sys.executable, "-m", "pip", "install", "--no-deps", "--no-build-isolation", str(wheel)],
    check=True,
)
# The wheel builder does not necessarily mark the embedded executable as executable.
if os.name != "nt":
    bare = Path(sysconfig.get_paths()["purelib"]) / "tetherto/qvac_sdk/_bundle/runtime/bare"
    bare.chmod(bare.stat().st_mode | 0o111)

if sys.platform == "linux":
    # Check every ELF file, including Bare and native addons without a .so suffix.
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
