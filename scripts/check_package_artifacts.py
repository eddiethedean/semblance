"""Check release artifacts include Python and typing metadata."""

import sys
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path

PACKAGES = {
    "core": ("semblance", "semblance/py.typed", "src/semblance/py.typed"),
    "foundry": (
        "semblance-foundry",
        "semblance_foundry/py.typed",
        "src/semblance_foundry/py.typed",
    ),
    "databricks": (
        "semblance-databricks",
        "semblance_databricks/py.typed",
        "src/semblance_databricks/py.typed",
    ),
}


def _check_metadata(content: bytes, distribution: str) -> None:
    metadata = Parser().parsestr(content.decode())
    if metadata["Name"] != distribution:
        raise ValueError(f"Expected {distribution}, got {metadata['Name']}")
    if metadata["Requires-Python"] != ">=3.11":
        raise ValueError(f"{distribution} must require Python >=3.11")


def check_package_artifacts(root: Path) -> None:
    for directory, (distribution, wheel_marker, sdist_marker) in PACKAGES.items():
        files = list((root / directory).iterdir())
        wheels = [path for path in files if path.suffix == ".whl"]
        sdists = [path for path in files if path.name.endswith(".tar.gz")]
        if len(wheels) != 1 or len(sdists) != 1:
            raise ValueError(f"Expected one wheel and sdist for {distribution}")

        with zipfile.ZipFile(wheels[0]) as archive:
            metadata_name = next(
                name
                for name in archive.namelist()
                if name.endswith(".dist-info/METADATA")
            )
            _check_metadata(archive.read(metadata_name), distribution)
            if wheel_marker not in archive.namelist():
                raise ValueError(f"{distribution} wheel is missing {wheel_marker}")

        with tarfile.open(sdists[0], "r:gz") as archive:
            names = archive.getnames()
            metadata_name = next(name for name in names if name.endswith("/PKG-INFO"))
            metadata_file = archive.extractfile(metadata_name)
            if metadata_file is None:
                raise ValueError(f"Could not read {distribution} sdist metadata")
            _check_metadata(metadata_file.read(), distribution)
            if not any(name.endswith(sdist_marker) for name in names):
                raise ValueError(f"{distribution} sdist is missing {sdist_marker}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: check_package_artifacts.py ARTIFACTS_DIR")
    check_package_artifacts(Path(sys.argv[1]))
