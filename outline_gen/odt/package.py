from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


class OdtPackage:
    """Small ODT zip helper for deterministic XML reads/writes."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def names(self) -> list[str]:
        with ZipFile(self.path) as zf:
            return zf.namelist()

    def read_text(self, name: str) -> str:
        with ZipFile(self.path) as zf:
            return zf.read(name).decode("utf-8", errors="replace")

    def read_bytes(self, name: str) -> bytes:
        with ZipFile(self.path) as zf:
            return zf.read(name)

    def write_replacements(self, out: Path, replacements: dict[str, bytes | str]) -> Path:
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(self.path) as src, ZipFile(out, "w") as dst:
            for info in src.infolist():
                data = src.read(info.filename)
                if info.filename in replacements:
                    repl = replacements[info.filename]
                    data = repl.encode("utf-8") if isinstance(repl, str) else repl
                compress_type = ZIP_DEFLATED if info.filename != "mimetype" else info.compress_type
                dst.writestr(info.filename, data, compress_type=compress_type)
        return out

    def has(self, name: str) -> bool:
        return name in set(self.names())
