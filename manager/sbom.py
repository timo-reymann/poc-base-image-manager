"""SBOM (Software Bill of Materials) generation using syft."""

import subprocess
import sys
from pathlib import Path

from manager.building import get_bin_path, get_image_tar_path


def get_syft_path() -> Path:
    """Get the path to the syft binary."""
    binary = get_bin_path() / "syft"
    if not binary.exists():
        raise RuntimeError(f"syft binary not found: {binary}")
    return binary


def get_sbom_path(image_ref: str, format: str = "cyclonedx-json") -> Path:
    """Get the output path for an SBOM file.

    Args:
        image_ref: Image reference in format 'name:tag'
        format: SBOM format (spdx-json, cyclonedx-json, etc.)

    Returns:
        Path to the SBOM output file
    """
    if ":" not in image_ref:
        raise ValueError(f"Invalid image reference '{image_ref}', expected format: name:tag")

    name, tag = image_ref.split(":", 1)

    # Map format to file extension
    ext_map = {
        "spdx-json": "spdx.json",
        "spdx": "spdx",
        "cyclonedx-json": "cyclonedx.json",
        "cyclonedx": "cyclonedx.xml",
        "json": "syft.json",
    }
    ext = ext_map.get(format, f"{format}.json")

    return Path("dist") / name / tag / f"sbom.{ext}"


def run_sbom(
    image_ref: str,
    format: str = "cyclonedx-json",
) -> int:
    """Generate SBOM for a built image.

    Args:
        image_ref: Image reference in format 'name:tag'
        format: Output format (spdx-json, cyclonedx-json, json, etc.)

    Returns:
        Exit code from syft
    """
    tar_path = get_image_tar_path(image_ref)

    if not tar_path.exists():
        print(f"Error: Image tar not found: {tar_path}", file=sys.stderr)
        print(f"Run 'image-manager build {image_ref}' first.", file=sys.stderr)
        return 1

    syft = get_syft_path()
    sbom_path = get_sbom_path(image_ref, format)

    cmd = [
        str(syft),
        "scan",
        f"docker-archive:{tar_path}",
        "-o", f"{format}={sbom_path}",
    ]

    print(f"Generating SBOM ({format}) for {image_ref}...")
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"SBOM saved to: {sbom_path}")
    else:
        print(f"Failed to generate SBOM", file=sys.stderr)

    return result.returncode
