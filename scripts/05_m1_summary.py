"""M1 總結：彙整各步驟的關鍵數字，並補兩項檢查，產出 reports/M1_summary.md。

    uv run python scripts/05_m1_summary.py

補的兩項：

1. RGBA 存檔的影像：逐張檢查 R、G、B 是否完全相同、alpha 是否全為 255，
   並比較這群影像與全體的切分、標籤、拍攝方式與亮度分布（格式差異會不會成為捷徑）。
2. 排除名單依來源分類，並確認鎖定的 split_v1.csv 雜湊沒有變動。

本腳本只讀取 split_v1.csv，不重新切分。亮度以 512 px 快取計算（模型實際讀到的影像）。
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from PIL import Image

from chestxraylab.cache import CACHE_DIR
from chestxraylab.data import (
    CLASSES,
    CONFIRMED_NEAR_DUPLICATE_PAIRS,
    IMAGE_COL,
    IMAGE_DIR,
    OFFICIAL_DUPLICATE_PAIRS,
    PATIENT_COL,
    RAW_DIR,
    REPORTS_DIR,
    VIEW_COL,
    load_metadata,
    load_official_lists,
)
from chestxraylab.split import SPLIT_CSV, SPLIT_NAMES, SPLIT_SHA256, load_split, sha256_of

SCAN_RESULT = RAW_DIR / "image_scan.csv"
LABEL_COLS = (*CLASSES, "no_finding")
SOURCE_OFFICIAL = "官方公告的配對（像素完全相同）"
SOURCE_SCAN = "自行掃描另外找到（像素完全相同）"
SOURCE_PHASH = "感知雜湊可疑名單＋人工看圖確認"


def _check_rgba(name: str) -> tuple[str, bool, bool, int, int]:
    """檢查一張 RGBA 原圖。

    Returns:
        (檔名, R=G=B 是否逐像素成立, alpha 是否全為 255, 三個色版的最大差值, alpha 最小值)。
    """
    with Image.open(IMAGE_DIR / name) as image:
        pixels = np.asarray(image.convert("RGBA"), dtype=np.int16)
    rgb, alpha = pixels[..., :3], pixels[..., 3]
    max_diff = int((rgb.max(axis=-1) - rgb.min(axis=-1)).max())
    return name, max_diff == 0, bool((alpha == 255).all()), max_diff, int(alpha.min())


def _brightness(name: str) -> float:
    """回傳一張快取影像的平均像素值（0 到 255）。"""
    with Image.open(CACHE_DIR / name) as image:
        return float(np.asarray(image, dtype=np.uint8).mean())


def _pct(part: int, whole: int) -> str:
    return f"{part / whole:.1%}" if whole else "-"


def _compare_rows(df: pd.DataFrame, is_rgba: pd.Series, column: str, values: tuple[str, ...]):
    """產生「RGBA 那群 vs 其餘影像」在某個類別欄位上的比較列。"""
    rgba, rest = df[is_rgba], df[~is_rgba]
    for value in values:
        a, b = int((rgba[column] == value).sum()), int((rest[column] == value).sum())
        yield f"| {value} | {a:,} | {_pct(a, len(rgba))} | {b:,} | {_pct(b, len(rest))} |"


def _rgba_section(df: pd.DataFrame, checks: pd.DataFrame) -> list[str]:
    is_rgba = df["mode"] == "RGBA"
    rgba, rest = df[is_rgba], df[~is_rgba]
    bad = checks[~(checks["rgb_equal"] & checks["alpha_opaque"])]
    n_checked = len(checks)

    lines = ["## 2. RGBA 存檔的影像", ""]
    lines += [
        f"原圖中有 {len(rgba):,} 張存成 RGBA（4 個色版），其餘 {len(rest):,} 張是單色版灰階。",
        "",
        "### 2.1 逐張檢查色版",
        "",
        f"- R、G、B 三個色版逐像素完全相同：{int(checks['rgb_equal'].sum()):,} / {n_checked:,} 張",
        f"- alpha 全為 255（完全不透明）：{int(checks['alpha_opaque'].sum()):,} / {n_checked:,} 張",
        f"- 不符合上述任一項：{len(bad):,} 張",
        "",
    ]
    if bad.empty:
        lines += [
            "全部符合，代表這些影像只是「灰階圖用 4 個色版存檔」，多出來的色版沒有額外資訊。",
            '快取用 `convert("L")` 轉成單色版：R=G=B 時轉換結果就等於 R，alpha 直接丟棄，'
            "所以轉換沒有損失，快取裡也看不出一張圖原本是不是 RGBA。",
            "",
        ]
    else:
        lines += [
            "| 影像 | R=G=B | alpha 全為 255 | 色版最大差值 | alpha 最小值 |",
            "|---|---|---|---|---|",
        ]
        lines += [
            f"| {r.image_id} | {'是' if r.rgb_equal else '否'} "
            f"| {'是' if r.alpha_opaque else '否'} | {r.max_channel_diff} | {r.alpha_min} |"
            for r in bad.itertuples()
        ]
        lines += [""]

    head = "| {} | RGBA 張數 | RGBA 比例 | 其餘張數 | 其餘比例 |"
    lines += ["### 2.2 這群影像落在哪裡", ""]
    lines += [
        f"- 涉及病人 {rgba[PATIENT_COL].nunique():,} 位；"
        f"檔名範圍 {rgba[IMAGE_COL].min()} 到 {rgba[IMAGE_COL].max()}",
        "",
        head.format("組"),
        "|---|---|---|---|---|",
        *_compare_rows(df, is_rgba, "split", SPLIT_NAMES),
        "",
        head.format("拍攝方式"),
        "|---|---|---|---|---|",
        *_compare_rows(df, is_rgba, VIEW_COL, ("PA", "AP")),
        "",
        "### 2.3 標籤分布",
        "",
        "「比例倍數」是 RGBA 那群的陽性比例除以其餘影像的陽性比例。",
        "RGBA 只有幾百張，陽性不到 10 張的類別比例很不穩定。",
        "",
        "| 標籤 | RGBA 陽性 | RGBA 比例 | 其餘陽性 | 其餘比例 | 比例倍數 |",
        "|---|---|---|---|---|---|",
    ]
    for label in LABEL_COLS:
        a, b = int(rgba[label].sum()), int(rest[label].sum())
        ratio = (a / len(rgba)) / (b / len(rest)) if b else float("nan")
        lines += [
            f"| {label} | {a:,} | {_pct(a, len(rgba))} | {b:,} | {_pct(b, len(rest))} "
            f"| {ratio:.2f} |"
        ]
    lines += [
        "",
        "### 2.4 亮度",
        "",
        "每張圖取 512 px 快取的平均像素值（0 到 255），再看這個值在兩群影像中的分布。",
        "拍攝方式會影響亮度，所以同時列出 PA、AP 各自的比較。",
        "",
        "| 範圍 | 群 | 張數 | 平均 | 標準差 | 第 5 百分位 | 中位數 | 第 95 百分位 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for scope, mask in (
        ("全部", pd.Series(True, index=df.index)),
        ("PA", df[VIEW_COL] == "PA"),
        ("AP", df[VIEW_COL] == "AP"),
    ):
        for group, part in (("RGBA", df[mask & is_rgba]), ("其餘", df[mask & ~is_rgba])):
            if part.empty:
                lines += [f"| {scope} | {group} | 0 | - | - | - | - | - |"]
                continue
            b = part["brightness"]
            p5, p50, p95 = np.percentile(b, [5, 50, 95])
            lines += [
                f"| {scope} | {group} | {len(part):,} | {b.mean():.1f} | {b.std():.1f} "
                f"| {p5:.1f} | {p50:.1f} | {p95:.1f} |"
            ]
    lines += [""]

    pa = df[VIEW_COL] == "PA"
    gap_pa = df.loc[pa & is_rgba, "brightness"].mean() - df.loc[pa & ~is_rgba, "brightness"].mean()
    gap_ap = (
        df.loc[~pa & is_rgba, "brightness"].mean() - df.loc[~pa & ~is_rgba, "brightness"].mean()
    )
    nf_rgba, nf_rest = rgba["no_finding"].mean(), rest["no_finding"].mean()
    test_rgba, test_rest = (rgba["split"] == "test").mean(), (rest["split"] == "test").mean()
    lines += [
        "### 2.5 判讀：會不會成為捷徑",
        "",
        "- **檔案格式本身不會**：模型讀的是單色版快取，第 2.1 節確認轉換沒有損失，"
        "快取裡沒有留下「原本是 RGBA」的痕跡",
        "- **但這群影像本身和其餘影像不一樣**，差異在轉成快取後仍然存在：",
        f"  - 比較亮：平均亮度在 PA 高 {gap_pa:.1f}、在 AP 高 {gap_ap:.1f}（0 到 255 的刻度），"
        "同一種拍攝方式內也有差，所以不是 PA／AP 比例不同造成的",
        f"  - 比較健康：No Finding 佔 {nf_rgba:.1%}，其餘影像為 {nf_rest:.1%}",
        f"  - 比較少進官方 test：{test_rgba:.1%} 在 test，其餘影像為 {test_rest:.1%}",
        "- 合理的推測是這群影像來自不同的輸出或後處理流程（未查證）。"
        "模型有可能學到「這種偏亮的影像比較常是正常」",
        f"- **影響範圍很小**：只佔全部影像的 {len(rgba) / len(df):.2%}，"
        f"test 中只有 {int((rgba['split'] == 'test').sum())} 張，對整體指標的影響有限",
        "- 處理方式：不排除、不特別處理（規格沒有相關規則，test 也不可更動）；"
        "列為已知的資料特性，M6 寫限制段落時引用本節",
        "",
    ]
    return lines


def _exclusion_section(split: pd.DataFrame, meta: pd.DataFrame) -> list[str]:
    _, test = load_official_lists()
    test_set = set(test)
    official_images = {name for pair in OFFICIAL_DUPLICATE_PAIRS for name in pair}
    confirmed_images = {name for pair in CONFIRMED_NEAR_DUPLICATE_PAIRS for name in pair}
    excluded = split[split["split"] == "excluded"].merge(
        meta[[IMAGE_COL, "labels_raw"]], on=IMAGE_COL
    )

    def source_of(row: pd.Series) -> str:
        if row["excluded_reason"] == "near_duplicate_of_test":
            return SOURCE_PHASH
        return SOURCE_OFFICIAL if row[IMAGE_COL] in official_images else SOURCE_SCAN

    excluded["source"] = excluded.apply(source_of, axis=1)
    official_tv = sorted(official_images - test_set)
    stray = sorted(
        set(excluded.loc[excluded["source"] == SOURCE_PHASH, IMAGE_COL]) - confirmed_images
    )
    missed = sorted(set(official_tv) - set(excluded[IMAGE_COL]))

    lines = ["## 3. 排除名單的來源", ""]
    lines += [
        f"NIH 官方 `LOG_CHESTXRAY.pdf` 公告了 {len(OFFICIAL_DUPLICATE_PAIRS)} 組配對，"
        f"共 {len(official_images)} 張影像，其中 {len(official_tv)} 張在官方 train_val。"
        f"只照官方公告處理的話會排除這 {len(official_tv)} 張。",
        f"M1 另外自行掃描全部影像（規格第 4.2.1 節），最終排除 {len(excluded)} 張：",
        "",
        "| 來源 | 排除原因 | 張數 |",
        "|---|---|---|",
    ]
    counts = excluded.groupby(["source", "excluded_reason"]).size()
    for source in (SOURCE_OFFICIAL, SOURCE_SCAN, SOURCE_PHASH):
        if source not in counts.index.get_level_values(0):
            continue
        for reason, n in counts[source].items():
            lines += [f"| {source} | {reason} | {n} |"]
    lines += [f"| **合計** | | **{len(excluded)}** |", ""]
    lines += [
        f"- 官方公告中位於 train_val 的 {len(official_tv)} 張，未被排除的有 {len(missed)} 張"
        + (f"：{', '.join(missed)}" if missed else ""),
        f"- 以 `near_duplicate_of_test` 排除、但不在人工確認清單"
        f"（`CONFIRMED_NEAR_DUPLICATE_PAIRS`）內的有 {len(stray)} 張"
        + (f"：{', '.join(stray)}" if stray else ""),
        "- 排除的全部是官方 train_val 的影像；官方 test 的 "
        f"{int((split['split'] == 'test').sum()):,} 張原樣保留",
        "",
        "| 影像 | 病人 | 標籤 | 排除原因 | 來源 |",
        "|---|---|---|---|---|",
    ]
    order = {SOURCE_OFFICIAL: 0, SOURCE_SCAN: 1, SOURCE_PHASH: 2}
    excluded = excluded.sort_values(
        by=["source", IMAGE_COL], key=lambda s: s.map(order) if s.name == "source" else s
    )
    lines += [
        f"| {r.image_id} | {r.patient_id} | {r.labels_raw} | {r.excluded_reason} | {r.source} |"
        for r in excluded.itertuples()
    ]
    lines += [""]
    return lines


def main() -> int:
    """執行兩項檢查並寫出總結報告；有 RGBA 影像不符合或雜湊不符時回傳 2。"""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    meta = load_metadata()
    locked_sha = SPLIT_SHA256.read_text(encoding="utf-8").strip()
    actual_sha = sha256_of(SPLIT_CSV)
    split = load_split()
    scan = pd.read_csv(SCAN_RESULT, dtype=str, keep_default_na=False)
    df = meta.merge(split[[IMAGE_COL, "split"]], on=IMAGE_COL).merge(
        scan[[IMAGE_COL, "mode"]], on=IMAGE_COL
    )
    if len(df) != len(meta):
        raise ValueError("中繼資料、切分表與掃描結果的影像對不上")

    rgba_names = sorted(df.loc[df["mode"] == "RGBA", IMAGE_COL])
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        checks = pd.DataFrame(
            list(pool.map(_check_rgba, rgba_names, chunksize=16)),
            columns=[IMAGE_COL, "rgb_equal", "alpha_opaque", "max_channel_diff", "alpha_min"],
        )
        df["brightness"] = list(pool.map(_brightness, df[IMAGE_COL], chunksize=512))

    lines = ["# M1 總結：資料", ""]
    lines += [
        "各步驟的完整內容見 `01_inventory.md`、`02_verify_images.md`、`03_split.md`、"
        "`04_cache.md`。",
        "",
        "## 1. 關鍵數字",
        "",
        f"- 影像 {len(meta):,} 張、病人 {meta[PATIENT_COL].nunique():,} 位；"
        "12 個壓縮檔 MD5 與官方相符，全部影像可開啟",
        "- 官方 train_val 與 test 沒有共用病人；train、val、test 之間沒有共用病人"
        "（讀取切分表時驗證）",
        "- 512 px 快取：全部影像，8 位元灰階 PNG",
        "",
        "| 組 | 病人 | 影像 |",
        "|---|---|---|",
    ]
    for name in SPLIT_NAMES:
        part = split[split["split"] == name]
        lines += [f"| {name} | {part[PATIENT_COL].nunique():,} | {len(part):,} |"]
    lines += [
        "",
        "### 切分清單的雜湊",
        "",
        f"- `split_v1.sha256` 記錄的值：`{locked_sha}`",
        f"- 現在對 `split_v1.csv` 重新計算：`{actual_sha}`",
        f"- 結果：**{'相符，鎖定後沒有變動' if locked_sha == actual_sha else '不符'}**",
        "",
    ]
    lines += _rgba_section(df, checks)
    lines += _exclusion_section(split, meta)

    out = REPORTS_DIR / "M1_summary.md"
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"已寫出 {out}")
    all_ok = bool((checks["rgb_equal"] & checks["alpha_opaque"]).all())
    return 0 if all_ok and locked_sha == actual_sha else 2


if __name__ == "__main__":
    sys.exit(main())
