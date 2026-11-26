"""M1 Step 3：建立切分並產出 reports/03_split.md。

預設只產生預覽，不寫切分檔。確認預覽後用報告裡的雜湊鎖定：

    uv run python scripts/03_split.py                  # 預覽
    uv run python scripts/03_split.py --lock <SHA256>  # 雜湊與重算結果相同才鎖定

重複影像的來源：有 Step 2 的掃描結果就用掃描結果，否則用官方公告的配對。
"""

from __future__ import annotations

import argparse
import hashlib
import sys

import pandas as pd

from chestxraylab.data import (
    CLASSES,
    CONFIRMED_NEAR_DUPLICATE_PAIRS,
    IMAGE_COL,
    PATIENT_COL,
    RAW_DIR,
    REPORTS_DIR,
    VIEW_COL,
    duplicate_groups,
    load_drain_annotations,
    load_metadata,
    load_official_lists,
)
from chestxraylab.split import (
    SPLIT_CSV,
    build_split_table,
    duplicate_exclusions,
    near_duplicate_exclusions,
    table_bytes,
    write_split,
)

SCAN_RESULT = RAW_DIR / "image_scan.csv"


def _groups() -> tuple[list[list[str]], str]:
    """回傳重複影像群組與其來源說明。"""
    if SCAN_RESULT.exists():
        scan = pd.read_csv(SCAN_RESULT, dtype=str, keep_default_na=False)
        scan = scan[scan["pixel_sha1"] != ""]
        dup = scan[scan.duplicated("pixel_sha1", keep=False)]
        groups = sorted(sorted(g[IMAGE_COL]) for _, g in dup.groupby("pixel_sha1"))
        return groups, "Step 2 的像素雜湊掃描"
    return duplicate_groups(), "NIH 官方公告的配對（尚未自行掃描）"


def main() -> int:
    """產生預覽報告；帶 ``--lock`` 且雜湊相符時鎖定切分。"""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lock", metavar="SHA256", help="預覽報告中的雜湊；相符才鎖定")
    args = parser.parse_args()

    meta = load_metadata()
    train_val, test = load_official_lists()
    test_set = set(test)
    official = {name: ("test" if name in test_set else "train_val") for name in meta[IMAGE_COL]}
    groups, source = _groups()
    exclusions = near_duplicate_exclusions(CONFIRMED_NEAR_DUPLICATE_PAIRS, official)
    exclusions.update(duplicate_exclusions(groups, official))
    table = build_split_table(meta, train_val, test, exclusions=exclusions)
    digest = hashlib.sha256(table_bytes(table)).hexdigest()

    full = table.merge(meta, on=[IMAGE_COL, PATIENT_COL])
    lines = ["# M1 Step 3：切分", ""]
    locked = SPLIT_CSV.exists()
    lines += [f"狀態：{'已鎖定' if locked else '預覽，尚未鎖定'}", ""]
    lines += [f"SHA-256：`{digest}`", ""]
    lines += [
        "- test：NIH 官方 `test_list.txt`，原樣使用",
        "- val：官方 train_val 的病人抽 10%，種子 42",
    ]
    lines += [f"- 重複影像來源：{source}", ""]

    lines += ["## 1. 各組大小", "", "| 組 | 病人 | 影像 | PA | AP |", "|---|---|---|---|---|"]
    for name in ["train", "val", "test", "excluded"]:
        part = full[full["split"] == name]
        lines += [
            f"| {name} | {part[PATIENT_COL].nunique():,} | {len(part):,} "
            f"| {int((part[VIEW_COL] == 'PA').sum()):,} | {int((part[VIEW_COL] == 'AP').sum()):,} |"
        ]
    lines += [""]

    lines += ["## 2. 各標籤陽性張數", ""]
    lines += ["| 標籤 | train | train 比例 | val | val 比例 | test | test 比例 |"]
    lines += ["|---|---|---|---|---|---|---|"]
    for cls in [*CLASSES, "no_finding"]:
        cells = []
        for name in ["train", "val", "test"]:
            part = full[full["split"] == name]
            n = int(part[cls].sum())
            cells += [f"{n:,}", f"{100 * n / len(part):.1f}%"]
        lines += [f"| {cls} | " + " | ".join(cells) + " |"]
    lines += [""]
    lines += [
        "test 的陽性比例明顯高於 train 與 val（官方切分不是隨機抽的）。因此：",
        "",
        "- AUPRC 受盛行率影響，**val 與 test 的 AUPRC 不可直接比較**；precision 與 F1 也一樣",
        "- 需要閾值的指標在 val 上以固定 sensitivity 決定閾值，不用最大化 F1（規格第 6 節）",
        "",
    ]

    lines += ["## 3. 排除的影像", ""]
    excluded = full[full["split"] == "excluded"]
    if excluded.empty:
        lines += ["無。", ""]
    else:
        lines += ["| 影像 | 病人 | 標籤 | 原因 |", "|---|---|---|---|"]
        for r in excluded.itertuples():
            lines += [f"| {r.image_id} | {r.patient_id} | {r.labels_raw} | {r.excluded_reason} |"]
        lines += [""]
        lines += ["- `duplicate_of_test`：與官方 test 的某張影像像素完全相同"]
        lines += ["- `duplicate_within_train_val`：train_val 內部互相重複，整群排除"]
        lines += [
            "- `near_duplicate_of_test`：與官方 test 的某張影像是同一次拍攝"
            "（影像處理不同，像素不完全相同），經人工看圖並由使用者確認後排除",
            "",
        ]

    lines += ["### 3.1 留在 test 的重複影像（只列出，不處理）", ""]
    info = meta.set_index(IMAGE_COL)
    kept = [(i, g) for i, g in enumerate(groups, start=1) if any(n in test_set for n in g)]
    if not kept:
        lines += ["無。", ""]
    else:
        lines += [
            "規格第 4.2.1 節：test 一律不動。下列影像屬於重複群但位於官方 test，不排除、不改標籤。",
            "",
            "| 群 | 影像 | 病人 | 標籤 | 群的類型 | 標籤衝突 |",
            "|---|---|---|---|---|---|",
        ]
        for i, group in kept:
            inside = all(n in test_set for n in group)
            kind = "test 內部" if inside else "跨 train_val 與 test"
            conflict = len({info.loc[n, "labels_raw"] for n in group}) > 1
            for name in group:
                if name not in test_set:
                    continue
                lines += [
                    f"| {i} | {name} | {info.loc[name, PATIENT_COL]} "
                    f"| {info.loc[name, 'labels_raw']} | {kind} | {'是' if conflict else '否'} |"
                ]
        lines += [""]
        lines += ["- 「test 內部」：同一張圖在 test 中出現不只一次，計分時會被算不只一次"]
        lines += ["- 「標籤衝突」：同一張圖在群內不同檔名下掛著不同標籤（含已排除的那一邊）", ""]

    lines += ["## 4. 氣胸與胸管標註", ""]
    drain = load_drain_annotations().merge(table, on=IMAGE_COL, how="left")
    lines += ["| 組 | 氣胸張數 | 有胸管標註 | 有胸管 | 無胸管 |", "|---|---|---|---|---|"]
    for name in ["train", "val", "test"]:
        part = drain[drain["split"] == name]
        n_pneumo = int(full[full["split"] == name]["Pneumothorax"].sum())
        lines += [
            f"| {name} | {n_pneumo:,} | {len(part):,} | {int((part['drain'] == 1).sum()):,} "
            f"| {int((part['drain'] == 0).sum()):,} |"
        ]
    lines += [""]

    if args.lock:
        if args.lock != digest:
            print(f"失敗: 雜湊不符。重算結果為 {digest}，沒有鎖定。")
            return 2
        write_split(table)
        lines[2] = "狀態：已鎖定"
        print(f"完成: 已鎖定 {SPLIT_CSV}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "03_split.md"
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"已寫出 {out}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
