"""repo 衛生檢查：`TODO(human)` 只能出現在規格第 3.1 節指定的三個檔案。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "TODO" + "(human)"

# 留給使用者寫的三個函式所在的檔案（M2、M3、M4 建立）。
ALLOWED = {
    ROOT / "src" / "chestxraylab" / "train_step.py",
    ROOT / "src" / "chestxraylab" / "losses.py",
    ROOT / "src" / "chestxraylab" / "lora.py",
}


def test_todo_human_only_in_allowed_files() -> None:
    offenders = []
    for folder in ("src", "scripts"):
        for path in (ROOT / folder).rglob("*.py"):
            if path in ALLOWED:
                continue
            if MARKER in path.read_text(encoding="utf-8"):
                offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_no_raw_data_tracked_paths_in_gitignore() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for needed in ("data/raw/", "data/cache/", "data/external/", "checkpoints/", ".env"):
        assert needed in ignore
