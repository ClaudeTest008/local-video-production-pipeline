"""Project file tree. Predictable folders; generated outputs auto-import here."""

import shutil
import zipfile
from pathlib import Path

from app.core.config import settings

SUBFOLDERS = (
    "research",
    "scripts",
    "storyboard",
    "assets/images",
    "assets/video",
    "assets/audio",
    "assets/music",
    "assets/thumbnails",
    "captions",
    "exports",
)


def project_dir(project_id: int) -> Path:
    return settings.projects_root / f"project-{project_id}"


def create_project_tree(project_id: int) -> Path:
    root = project_dir(project_id)
    for sub in SUBFOLDERS:
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def delete_project_tree(project_id: int) -> None:
    root = project_dir(project_id)
    if root.exists():
        shutil.rmtree(root)


def archive_project(project_id: int, dest: Path | None = None) -> Path:
    """Zip the whole project folder → exports/<name>.zip (project archive export)."""
    root = project_dir(project_id)
    dest = dest or root / "exports" / f"project-{project_id}-archive.zip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in root.rglob("*"):
            if path.is_file() and dest != path:
                zf.write(path, path.relative_to(root))
    return dest
