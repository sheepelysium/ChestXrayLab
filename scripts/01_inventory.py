"""M1 Step 1：用官方中繼資料核對規格第 4 節的數字，產出 reports/01_inventory.md。

只讀 CSV 與清單，不需要影像。數字與規格不符時照實寫進報告並回傳 2。
"""

from __future__ import annotations

import sys

import pandas as pd

from chestxraylab.data import (
    CLASSES,
    IMAGE_COL,
    PATIENT_COL,
    REPORTS_DIR,
    VIEW_COL,
    duplicate_groups,
    load_bboxes,
    load_drain_annotations,
    load_metadata,
    load_official_lists,
)

EXPECTED = {
    "影像總數": 112_120,
    "病人總數": 30_805,
    "官方 train_val 張數": 86_524,
    "官方 test 張數": 25_596,
}


def _table(df: pd.DataFrame) -> str:
    """把 DataFrame 轉成 Markdown 表格（不依賴 tabulate）。"""
    head = "| " + " | ".join(str(c) for c in df.columns) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    rows = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, sep, *rows])


def _pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "-"


def main() -> int:
    """執行盤點並寫出報告。

    Returns:
        0 表示所有數字與規格相符；2 表示有不符（報告仍會寫出）。
    """
    meta = load_metadata()
    train_val, test = load_official_lists()
    tv_set, test_set = set(train_val), set(test)
    meta["official"] = meta[IMAGE_COL].map(
        lambda x: "test" if x in test_set else ("train_val" if x in tv_set else "none")
    )
    tv = meta[meta["official"] == "train_val"]
    te = meta[meta["official"] == "test"]

    actual = {
        "影像總數": len(meta),
        "病人總數": meta[PATIENT_COL].nunique(),
        "官方 train_val 張數": len(train_val),
        "官方 test 張數": len(test),
    }
    problems: list[str] = []
    for key, want in EXPECTED.items():
        if actual[key] != want:
            problems.append(f"{key}：規格 {want:,}，實際 {actual[key]:,}")
    if len(tv_set) != len(train_val) or len(test_set) != len(test):
        problems.append("官方清單內有重複的檔名")
    if tv_set & test_set:
        problems.append(f"官方兩個清單共用 {len(tv_set & test_set)} 張影像")
    if (meta["official"] == "none").any() or (tv_set | test_set) - set(meta[IMAGE_COL]):
        problems.append("官方清單與中繼資料的影像對不上")
    shared_patients = set(tv[PATIENT_COL]) & set(te[PATIENT_COL])
    if shared_patients:
        problems.append(f"官方 train_val 與 test 共用 {len(shared_patients)} 位病人")

    lines: list[str] = ["# M1 Step 1：資料盤點", ""]
    lines += ["資料來源：NIH 官方 Box 資料夾的 `Data_Entry_2017_v2020.csv`、`train_val_list.txt`、"]
    lines += ["`test_list.txt`、`BBox_List_2017.csv`，以及 NEATX 胸管標註。本步驟不讀影像。", ""]

    lines += ["## 1. 總數與官方切分", ""]
    summary = pd.DataFrame(
        [
            ["全部", len(meta), meta[PATIENT_COL].nunique()],
            ["官方 train_val", len(tv), tv[PATIENT_COL].nunique()],
            ["官方 test", len(te), te[PATIENT_COL].nunique()],
        ],
        columns=["範圍", "影像", "病人"],
    )
    summary["影像"] = summary["影像"].map("{:,}".format)
    summary["病人"] = summary["病人"].map("{:,}".format)
    lines += [_table(summary), ""]
    lines += [f"- 官方 train_val 與 test 共用的病人：**{len(shared_patients)}**"]
    lines += [f"- 官方 train_val 與 test 共用的影像：**{len(tv_set & test_set)}**", ""]

    lines += ["## 2. 各標籤張數與比例", ""]
    rows = []
    for name in [*CLASSES, "no_finding"]:
        n_tv, n_te = int(tv[name].sum()), int(te[name].sum())
        rows.append(
            [
                name,
                f"{n_tv + n_te:,}",
                f"{n_tv:,}",
                _pct(n_tv, len(tv)),
                f"{n_te:,}",
                _pct(n_te, len(te)),
                f"{(n_te / len(te)) / (n_tv / len(tv)):.2f}",
            ]
        )
    cols = ["標籤", "全部", "train_val", "train_val 比例", "test", "test 比例", "比例倍數"]
    lines += [_table(pd.DataFrame(rows, columns=cols)), ""]
    lines += ["「比例倍數」是 test 的陽性比例除以 train_val 的陽性比例。"]
    lines += ["倍數離 1 越遠，代表官方 test 與 train_val 的組成差越多。", ""]
    n_labels = meta[list(CLASSES)].sum(axis=1)
    lines += [
        f"- 一張影像同時有 2 個以上異常標籤：{int((n_labels >= 2).sum()):,} 張"
        f"（{_pct(int((n_labels >= 2).sum()), len(meta))}），最多 {int(n_labels.max())} 個",
        "",
    ]

    lines += ["## 3. 拍攝方式（View Position）", ""]
    rows = []
    for label, part in [("官方 train_val", tv), ("官方 test", te)]:
        counts = part[VIEW_COL].value_counts()
        for view in sorted(counts.index):
            rows.append([label, view, f"{int(counts[view]):,}", _pct(int(counts[view]), len(part))])
    lines += [_table(pd.DataFrame(rows, columns=["範圍", "拍攝方式", "影像", "比例"])), ""]
    rows = []
    for name in CLASSES:
        pa, ap = meta[meta[VIEW_COL] == "PA"], meta[meta[VIEW_COL] == "AP"]
        rows.append([name, _pct(int(pa[name].sum()), len(pa)), _pct(int(ap[name].sum()), len(ap))])
    lines += ["各標籤在 PA 與 AP 影像中的陽性比例（全部影像）：", ""]
    lines += [_table(pd.DataFrame(rows, columns=["標籤", "PA 中的比例", "AP 中的比例"])), ""]

    lines += ["## 4. 每位病人的影像數", ""]
    per_patient = meta.groupby(PATIENT_COL).size()
    lines += [
        f"- 中位數 {int(per_patient.median())} 張，平均 {per_patient.mean():.1f} 張，"
        f"最多 {int(per_patient.max())} 張",
        f"- 只有 1 張的病人：{int((per_patient == 1).sum()):,} 位；"
        f"超過 50 張的病人：{int((per_patient > 50).sum()):,} 位，"
        f"共 {int(per_patient[per_patient > 50].sum()):,} 張",
        f"- 年齡範圍 {int(meta['age'].min())} 到 {int(meta['age'].max())} 歲",
        "",
    ]

    lines += ["## 5. 框標註", ""]
    bbox = load_bboxes()
    bbox_split = bbox[IMAGE_COL].map(lambda x: "test" if x in test_set else "train_val")
    lines += [
        f"- 框 {len(bbox):,} 個，分布在 {bbox[IMAGE_COL].nunique():,} 張影像",
        f"- 落在官方 test 的框：{int((bbox_split == 'test').sum()):,} 個；"
        f"落在 train_val：{int((bbox_split == 'train_val').sum()):,} 個",
        "",
    ]
    counts = bbox["label"].value_counts()
    lines += [_table(pd.DataFrame({"類別": counts.index, "框數": counts.values})), ""]
    mismatch = bbox.merge(meta, on=IMAGE_COL, how="left")
    n_bad = int(sum(row[row["label"]] != 1 for _, row in mismatch.iterrows()))
    lines += [f"- 框的類別在影像標籤中不是陽性的框：{n_bad} 個", ""]

    lines += ["## 6. 胸管標註（NEATX）", ""]
    drain = load_drain_annotations().merge(
        meta[[IMAGE_COL, "official", "Pneumothorax", VIEW_COL]], on=IMAGE_COL, how="left"
    )
    if drain["official"].isna().any():
        problems.append("NEATX 有影像不在 NIH 中繼資料內")
    lines += [
        f"- 標註 {len(drain):,} 張，其中 NIH 標籤為氣胸的 {int(drain['Pneumothorax'].sum()):,} 張",
        "- 標註者為兩位非醫師，授權 CC BY-NC-SA，只用於分群報告",
        "",
    ]
    rows = []
    for split in ["train_val", "test"]:
        part = drain[drain["official"] == split]
        n_pneumo = int(meta[(meta["official"] == split)]["Pneumothorax"].sum())
        rows.append(
            [
                split,
                f"{n_pneumo:,}",
                f"{len(part):,}",
                f"{int((part['drain'] == 1).sum()):,}",
                f"{int((part['drain'] == 0).sum()):,}",
            ]
        )
    cols = ["範圍", "NIH 氣胸張數", "有胸管標註", "有胸管", "無胸管"]
    lines += [_table(pd.DataFrame(rows, columns=cols)), ""]

    lines += ["## 7. 官方公告的重複影像", ""]
    lines += ["NIH 在 `LOG_CHESTXRAY.pdf`（2026-10-09）公告了 10 組像素完全相同的影像配對。"]
    lines += ["合併成群組後如下（同一群內的影像內容相同）：", ""]
    info = meta.set_index(IMAGE_COL)
    rows = []
    for i, group in enumerate(duplicate_groups(), start=1):
        for name in group:
            rec = info.loc[name]
            rows.append([i, name, rec["official"], rec[PATIENT_COL], rec["labels_raw"]])
    lines += [_table(pd.DataFrame(rows, columns=["群", "影像", "官方切分", "病人", "標籤"])), ""]
    cross = [g for g in duplicate_groups() if len({info.loc[n, "official"] for n in g}) > 1]
    lines += [f"- 橫跨 train_val 與 test 的群：**{len(cross)}** 群", ""]
    lines += ["這與「官方切分沒有洩漏」的假設不符，處理方式待使用者決定。", ""]

    lines += ["## 8. 與規格的核對結果", ""]
    if problems:
        lines += ["**有不符：**", ""] + [f"- {p}" for p in problems] + [""]
    else:
        lines += ["規格第 4 節的總數、切分張數、各標籤張數全部與官方檔案相符。", ""]

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "01_inventory.md"
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"已寫出 {out}")
    for p in problems:
        print(f"不符: {p}")
    return 2 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
