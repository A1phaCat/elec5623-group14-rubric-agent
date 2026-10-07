"""Locate versioned demo inputs in both source checkouts and installed wheels.

The build hook bundles only prompts and synthetic examples. Private documents,
credentials, run logs and annotation workspaces never become package data.
"""

from __future__ import annotations

from pathlib import Path


def resource_directory(name: str) -> Path:
    if name not in {"prompts", "dataset"}:
        raise ValueError(f"Unknown resource directory: {name}")
    package = Path(__file__).resolve().parent
    # Editable/source execution uses the canonical files so edits stay visible.
    source_root = package.parents[1]
    if (source_root / "pyproject.toml").is_file() and (source_root / name).is_dir():
        return source_root / name
    bundled = package / "resources" / name
    if not bundled.is_dir():
        raise FileNotFoundError(f"Missing bundled {name}; reinstall rubric-marking-agent from its source archive.")
    return bundled
