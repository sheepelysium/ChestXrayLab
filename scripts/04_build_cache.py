"""M1 Step 4：建立 512 px 影像快取，產出 reports/04_cache.md。

    uv run python scripts/04_build_cache.py

把 data/raw/images 的每張原圖轉成 8 位元灰階、512×512 的 PNG，存到 data/cache/images_512。
可重跑：已存在的快取檔會跳過。建完後逐張開啟核對，再寫報告。
快取涵蓋中繼資料列出的全部影像（含 test 與被排除的影像）；哪些影像屬於哪一組仍由
split_v1.csv 決定，快取本身不含任何切分或標籤資訊。
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor

from PIL import Image, UnidentifiedImageError

from chestxraylab.cache import CACHE_DIR, CACHE_SIZE, write_cache_image
from chestxraylab.data import IMAGE_COL, IMAGE_DIR, PROJECT_ROOT, REPORTS_DIR, load_metadata


def _build_one(name: str) -> tuple[str, str]:
    """建立一張快取；回傳 (檔名, 狀態)，狀態為 built、skipped、missing 或 failed。"""
    source, dest = IMAGE_DIR / name, CACHE_DIR / name
    if dest.exists():
        return name, "skipped"
    if not source.exists():
        return name, "missing"
    try:
        write_cache_image(source, dest)
    except (OSError, UnidentifiedImageError, ValueError):
        return name, "failed"
    return name, "built"


def _check_one(name: str) -> tuple[str, bool, int]:
    """開啟一張快取，回傳 (檔名, 是否為 512×512 灰階且能完整解碼, 檔案位元組數)。"""
    path = CACHE_DIR / name
    try:
        with Image.open(path) as image:
            image.load()
            ok = image.mode == "L" and image.size == (CACHE_SIZE, CACHE_SIZE)
        return name, ok, path.stat().st_size
    except (OSError, UnidentifiedImageError, ValueError):
        return name, False, 0


def main() -> int:
    """建立快取、核對並寫報告；有任何一張缺漏或不合格時回傳 2。"""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    names = sorted(load_metadata()[IMAGE_COL])
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        built = dict(pool.map(_build_one, names, chunksize=256))
        build_seconds = time.perf_counter() - started
        checks = list(pool.map(_check_one, names, chunksize=256))

    status = {
        s: sum(v == s for v in built.values()) for s in ("built", "skipped", "missing", "failed")
    }
    bad = sorted(name for name, ok, _ in checks if not ok)
    extra = sorted({p.name for p in CACHE_DIR.iterdir()} - set(names))
    total_bytes = sum(size for _, _, size in checks)
    print(f"建立 {status}；不合格 {len(bad)} 張；多餘檔案 {len(extra)} 個")

    lines = ["# M1 Step 4：512 px 快取", ""]
    lines += [
        f"- 來源：`data/raw/images` 的原圖（1024×1024），共 {len(names):,} 張"
        "（中繼資料列出的全部影像）",
        f"- 輸出：`{CACHE_DIR.relative_to(PROJECT_ROOT).as_posix()}`，"
        f"8 位元灰階、{CACHE_SIZE}×{CACHE_SIZE}、PNG（無損）",
        '- 灰階轉換與 Step 2 的像素雜湊相同（`convert("L")`），RGBA 存檔的影像也轉成單通道',
        "- 縮小方式：BOX（每 2×2 個像素取平均）",
        "- 快取含 test 與被排除的影像；哪些影像進哪一組仍由 `split_v1.csv` 決定",
        "",
        "## 1. 建立結果",
        "",
        "| 項目 | 張數 |",
        "|---|---|",
        f"| 本次新建 | {status['built']:,} |",
        f"| 已存在而跳過 | {status['skipped']:,} |",
        f"| 找不到原圖 | {status['missing']:,} |",
        f"| 轉換失敗 | {status['failed']:,} |",
        "",
        f"本次建立耗時 {build_seconds / 60:.1f} 分鐘（{args.workers} 個行程）。",
        "",
        "## 2. 核對",
        "",
        "逐張開啟快取檔並完整解碼。",
        "",
        f"- 合格（{CACHE_SIZE}×{CACHE_SIZE} 灰階、可完整解碼）：{len(names) - len(bad):,} 張",
        f"- 缺漏或不合格：{len(bad):,} 張",
        f"- 快取目錄中不在中繼資料內的檔案：{len(extra):,} 個",
        f"- 快取總大小：{total_bytes / 1e9:.2f} GB",
        "",
    ]
    if bad:
        lines += ["缺漏或不合格的影像：", ""] + [f"- {name}" for name in bad[:100]] + [""]
    out = REPORTS_DIR / "04_cache.md"
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"已寫出 {out}")
    return 2 if bad or extra else 0


if __name__ == "__main__":
    sys.exit(main())
