"""Check the stowed worker and Bare runtime without downloading models."""

from pathlib import Path
import subprocess
import tempfile

from bare_sidecar import executable, versions
from tetherto import qvac_sdk

worker = Path(qvac_sdk.__file__).parent / "_worker"
assert (worker / "index.bundle").is_file()
assert (worker / "index.bundle.d").is_dir()
with tempfile.TemporaryDirectory() as directory:
    entry = Path(directory) / "version.js"
    entry.write_text("console.log(Bare.version)\n", encoding="utf-8")
    result = subprocess.run(
        [str(executable()), str(entry)], check=True, timeout=30,
        capture_output=True, text=True,
    )
    assert result.stdout.strip() == f"v{versions['bare']}", result.stdout
