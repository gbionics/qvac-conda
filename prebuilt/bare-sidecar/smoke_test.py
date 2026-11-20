"""Exercise the bundled runtime and its IPC channel without network access."""

import asyncio
from pathlib import Path
import tempfile

from bare_sidecar import spawn, versions


async def check():
    with tempfile.TemporaryDirectory() as directory:
        entry = Path(directory) / "smoke.js"
        entry.write_text('Bare.IPC.end(Bare.version)\n', encoding="utf-8")
        async with await spawn(entry) as sidecar:
            output = b"".join([chunk async for chunk in sidecar])
            assert await sidecar.wait() == 0
        assert output.decode() == f"v{versions['bare']}", output


asyncio.run(asyncio.wait_for(check(), timeout=30))
