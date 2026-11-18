"""Check the bundled runtime without downloading models or starting network services."""

import os
from pathlib import Path
import subprocess

from tetherto import qvac_sdk

bundle = Path(qvac_sdk.__file__).parent / "_bundle"
assert (bundle / "worker/package.json").is_file()
bare = bundle / "runtime" / ("bare.exe" if os.name == "nt" else "bare")
assert bare.is_file(), bare
subprocess.run([str(bare), "--version"], check=True, timeout=30)
