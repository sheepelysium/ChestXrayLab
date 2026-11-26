"""M1 Step 2：核對影像檔的完整性，產出 reports/02_verify_images.md。

子指令依序執行：

    uv run python scripts/02_verify_images.py md5       # 壓縮檔 MD5 對照官方 FAQ
    uv run python scripts/02_verify_images.py extract   # 解壓到 data/raw/images
    uv run python scripts/02_verify_images.py scan      # 逐張開啟、算像素雜湊與感知雜湊，再寫報告
    uv run python scripts/02_verify_images.py report    # 只用既有的掃描結果重寫報告

MD5 來源：NIH 官方 FAQ_CHESTXRAY.pdf 的 Q07。
重複影像的處理規則見規格第 4.2.1 節：本腳本只負責找出來與列出，排除在 Step 3 進行；
感知雜湊的結果只列可疑名單，不會被 Step 3 讀取。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tarfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, UnidentifiedImageError

from chestxraylab.data import (
    ARCHIVE_DIR,
    IMAGE_COL,
    IMAGE_DIR,
    OFFICIAL_DUPLICATE_PAIRS,
    PATIENT_COL,
    RAW_DIR,
    REPORTS_DIR,
    duplicate_groups,
    load_metadata,
    load_official_lists,
)
from chestxraylab.phash import HASH_BITS, hex_to_words, near_pairs, phash_hex

OFFICIAL_MD5 = {
    "images_001.tar.gz": "fe8ed0a6961412fddcbb3603c11b3698",
    "images_002.tar.gz": "ab07a2d7cbe6f65ddd97b4ed7bde10bf",
    "images_003.tar.gz": "2301d03bde4c246388bad3876965d574",
    "images_004.tar.gz": "9f1b7f5aae01b13f4bc8e2c44a4b8ef6",
    "images_005.tar.gz": "1861f3cd0ef7734df8104f2b0309023b",
    "images_006.tar.gz": "456b53a8b351afd92a35bc41444c58c8",
    "images_007.tar.gz": "1075121ea20a137b87f290d6a4a5965e",
    "images_008.tar.gz": "b61f34cec3aa69f295fbb593cbd9d443",
    "images_009.tar.gz": "442a3caa61ae9b64e61c561294d1e183",
    "images_010.tar.gz": "09ec81c4c31e32858ad8cf965c494b74",
    "images_011.tar.gz": "499aefc67207a5a97692424cf5dbeed5",
    "images_012.tar.gz": "dc9fda1757c2de0032b63347a7d2895c",
}
MD5_RESULT = RAW_DIR / "md5_result.json"
SCAN_RESULT = RAW_DIR / "image_scan.csv"
NEAR_CSV = REPORTS_DIR / "02_near_duplicates.csv"
# 感知雜湊的距離門檻（256 個位元中相差幾個以內算可疑）。只影響可疑名單的長度，不影響切分。
PHASH_MAX_DISTANCE = 30
# 報告中每一類可疑配對最多列幾列；完整名單在 NEAR_CSV。
NEAR_ROWS_IN_REPORT = 100
NEAR_KINDS = (
    "跨 train_val 與 test",
    "train_val 內、不同病人",
    "train_val 內、同一病人",
    "test 內、不同病人",
    "test 內、同一病人",
)


def _md5(path: Path) -> str:
    digest = hashlib.md5()  # noqa: S324 - 只用來對照官方公布的校驗碼
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cmd_md5() -> int:
    """計算 12 個壓縮檔的 MD5 並對照官方數值。"""
    result = {}
    for name, want in OFFICIAL_MD5.items():
        path = ARCHIVE_DIR / name
        got = _md5(path) if path.exists() else "missing"
        result[name] = {
            "expected": want,
            "actual": got,
            "ok": got == want,
            "bytes": (path.stat().st_size if path.exists() else 0),
        }
        print(f"{name}: {'ok' if got == want else 'MISMATCH ' + got}")
    MD5_RESULT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if all(r["ok"] for r in result.values()) else 2


def cmd_extract() -> int:
    """把 12 個壓縮檔解到 data/raw/images（只接受檔名為 *.png 的一般檔案）。"""
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    for name in OFFICIAL_MD5:
        marker = IMAGE_DIR / f".{name}.extracted"
        if marker.exists():
            continue
        count = 0
        with tarfile.open(ARCHIVE_DIR / name, "r:gz") as tar:
            for member in tar:
                base = Path(member.name).name
                if not member.isfile() or not base.endswith(".png"):
                    continue
                source = tar.extractfile(member)
                if source is None:
                    continue
                (IMAGE_DIR / base).write_bytes(source.read())
                count += 1
        marker.write_text(str(count), encoding="utf-8")
        print(f"{name}: 解出 {count:,} 張")
    return 0


def _scan_one(path_str: str) -> tuple[str, str, int, int, str, str]:
    """開啟一張影像，回傳 (檔名, 模式, 寬, 高, 像素雜湊, 感知雜湊)；打不開時兩個雜湊為空字串。"""
    path = Path(path_str)
    try:
        with Image.open(path) as im:
            im.load()
            mode, (width, height) = im.mode, im.size
            # 轉成 8 位元灰階後算雜湊，所以 RGBA 與灰階存檔的同一張圖會算成相同。
            gray = im.convert("L")
            pixels = gray.tobytes()
            perceptual = phash_hex(gray)
    except (OSError, UnidentifiedImageError, ValueError):
        return path.name, "unreadable", 0, 0, "", ""
    return path.name, mode, width, height, hashlib.sha1(pixels).hexdigest(), perceptual  # noqa: S324


def cmd_scan(workers: int, max_distance: int) -> int:
    """逐張開啟影像，算像素雜湊與感知雜湊，存成掃描結果後寫報告。"""
    files = sorted(IMAGE_DIR.glob("*.png"))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(_scan_one, [str(f) for f in files], chunksize=256))
    scan = pd.DataFrame(rows, columns=[IMAGE_COL, "mode", "width", "height", "pixel_sha1", "phash"])
    scan.to_csv(SCAN_RESULT, index=False, lineterminator="\n")
    print(f"已寫出 {SCAN_RESULT}（{len(scan):,} 張）")
    return cmd_report(max_distance)


def _pixel_corr(name_a: str, name_b: str) -> float | None:
    """兩張影像縮成 256×256 後的像素相關係數；影像檔不在磁碟上時回傳 ``None``。"""
    arrays = []
    for name in (name_a, name_b):
        path = IMAGE_DIR / name
        if not path.exists():
            return None
        with Image.open(path) as im:
            small = im.convert("L").resize((256, 256), Image.Resampling.BILINEAR)
            arrays.append(np.asarray(small, dtype=np.float64).ravel())
    return float(np.corrcoef(arrays[0], arrays[1])[0, 1])


def _near_duplicates(readable: pd.DataFrame, info: pd.DataFrame, max_distance: int) -> pd.DataFrame:
    """用感知雜湊找出可疑配對（已排除像素完全相同的配對）。

    Args:
        readable: 掃描結果中打得開的影像。
        info: 以影像檔名為索引的表，含 ``official``、病人編號與 ``labels_raw``。
        max_distance: Hamming 距離門檻。

    Returns:
        每個配對一列，依距離排序。
    """
    names = readable[IMAGE_COL].tolist()
    sha = readable["pixel_sha1"].tolist()
    pairs = near_pairs(hex_to_words(readable["phash"].tolist()), max_distance)
    rows = []
    for i, j, dist in pairs.tolist():
        if sha[i] == sha[j]:
            continue
        a, b = info.loc[names[i]], info.loc[names[j]]
        same_patient = a[PATIENT_COL] == b[PATIENT_COL]
        who = "同一病人" if same_patient else "不同病人"
        if a["official"] != b["official"]:
            kind = "跨 train_val 與 test"
        else:
            kind = f"{a['official']} 內、{who}"
        corr = _pixel_corr(names[i], names[j])
        rows.append(
            {
                "distance": dist,
                "pixel_corr": "" if corr is None else f"{corr:.4f}",
                "kind": kind,
                "image_a": names[i],
                "split_a": a["official"],
                "patient_a": a[PATIENT_COL],
                "labels_a": a["labels_raw"],
                "image_b": names[j],
                "split_b": b["official"],
                "patient_b": b[PATIENT_COL],
                "labels_b": b["labels_raw"],
                "same_labels": a["labels_raw"] == b["labels_raw"],
            }
        )
    columns = [
        "distance",
        "pixel_corr",
        "kind",
        "image_a",
        "split_a",
        "patient_a",
        "labels_a",
        "image_b",
        "split_b",
        "patient_b",
        "labels_b",
        "same_labels",
    ]
    return pd.DataFrame(rows, columns=columns)


def cmd_report(max_distance: int) -> int:
    """用既有的掃描結果找出重複與可疑影像，寫出報告。"""
    meta = load_metadata()
    _, test = load_official_lists()
    test_set = set(test)
    scan = pd.read_csv(SCAN_RESULT, dtype=str, keep_default_na=False)

    expected, found = set(meta[IMAGE_COL]), set(scan[IMAGE_COL])
    unreadable = scan[scan["mode"] == "unreadable"]
    readable = scan[(scan["mode"] != "unreadable") & scan[IMAGE_COL].isin(expected)]
    readable = readable.reset_index(drop=True)
    dup = readable[readable.duplicated("pixel_sha1", keep=False)]
    groups = sorted(sorted(g[IMAGE_COL]) for _, g in dup.groupby("pixel_sha1"))
    official_groups = duplicate_groups(OFFICIAL_DUPLICATE_PAIRS)
    info = meta.set_index(IMAGE_COL)
    info["official"] = ["test" if name in test_set else "train_val" for name in info.index]

    lines = ["# M1 Step 2：影像完整性", ""]
    lines += ["## 1. 壓縮檔 MD5（對照官方 FAQ）", ""]
    if MD5_RESULT.exists():
        md5 = json.loads(MD5_RESULT.read_text(encoding="utf-8"))
        lines += ["| 檔案 | 大小（GB） | 結果 |", "|---|---|---|"]
        for name, rec in md5.items():
            status = "相符" if rec["ok"] else "不符"
            lines += [f"| {name} | {rec['bytes'] / 1e9:.2f} | {status} |"]
        lines += [""]
    else:
        lines += ["尚未執行 md5 子指令。", ""]

    lines += ["## 2. 影像張數與可讀性", ""]
    lines += [
        f"- 中繼資料列出 {len(expected):,} 張，磁碟上找到 {len(found):,} 張",
        f"- 中繼資料有、磁碟沒有：{len(expected - found):,} 張",
        f"- 磁碟有、中繼資料沒有：{len(found - expected):,} 張",
        f"- 打不開的影像：{len(unreadable):,} 張",
        "",
    ]
    sizes = scan[scan["mode"] != "unreadable"]
    sizes = sizes.groupby(["mode", "width", "height"]).size().reset_index(name="n")
    lines += ["| 色彩模式 | 寬 | 高 | 張數 |", "|---|---|---|---|"]
    lines += [f"| {r.mode} | {r.width} | {r.height} | {r.n:,} |" for r in sizes.itertuples()]
    lines += [""]

    lines += ["## 3. 像素完全相同的影像", ""]
    lines += [
        "判定方式：解碼成 8 位元灰階後逐像素相同。處理規則在掃描前就寫進規格第 4.2.1 節：",
        "群組橫跨 train_val 與 test 時排除 train_val 那一邊；全部在 train_val 內時整群排除；",
        "test 一律不動。",
        "",
        f"- 自己掃描找到 {len(groups)} 群，共 {sum(len(g) for g in groups)} 張",
        f"- 官方公告的 {len(official_groups)} 群中，掃描結果涵蓋 "
        f"{sum(any(set(o) <= set(g) for g in groups) for o in official_groups)} 群",
        "",
    ]
    lines += [
        "| 群 | 影像 | 官方切分 | 病人 | 標籤 | 群的類型 | 處置 |",
        "|---|---|---|---|---|---|---|",
    ]
    counts = {"跨 train_val 與 test": 0, "train_val 內部": 0, "test 內部": 0}
    n_patients = n_labels = 0
    test_kept: list[tuple[int, str, str, bool]] = []
    for i, group in enumerate(groups, start=1):
        sides = {info.loc[n, "official"] for n in group}
        if len(sides) > 1:
            kind = "跨 train_val 與 test"
        else:
            kind = f"{next(iter(sides))} 內部"
        counts[kind] += 1
        conflict = len({info.loc[n, "labels_raw"] for n in group}) > 1
        n_labels += conflict
        n_patients += len({info.loc[n, PATIENT_COL] for n in group}) > 1
        for name in group:
            side = info.loc[name, "official"]
            action = "保留（test 不動）" if side == "test" else "排除"
            if side == "test":
                test_kept.append((i, name, kind, conflict))
            lines += [
                f"| {i} | {name} | {side} | {info.loc[name, PATIENT_COL]} "
                f"| {info.loc[name, 'labels_raw']} | {kind}{'、標籤衝突' if conflict else ''} "
                f"| {action} |"
            ]
    lines += [""]
    lines += [f"- {kind}：{n} 群" for kind, n in counts.items()]
    lines += [
        f"- 同一張圖掛在不同病人名下：{n_patients} 群",
        f"- 同一張圖但標籤不同（標籤衝突）：{n_labels} 群",
        "",
    ]

    lines += ["### 3.1 留在 test 的重複影像（只列出，不處理）", ""]
    if not test_kept:
        lines += ["無。", ""]
    else:
        lines += [
            "下列影像屬於重複群但位於官方 test，依規則不排除、不改標籤。",
            "「test 內部」的群代表同一張圖在 test 中被計分不只一次；",
            "「標籤衝突」代表同一張圖在不同檔名下掛著不同標籤，其中至少一邊的標籤有誤。",
            "",
            "| 群 | 影像 | 病人 | 標籤 | 群的類型 | 標籤衝突 |",
            "|---|---|---|---|---|---|",
        ]
        for i, name, kind, conflict in test_kept:
            lines += [
                f"| {i} | {name} | {info.loc[name, PATIENT_COL]} | {info.loc[name, 'labels_raw']} "
                f"| {kind} | {'是' if conflict else '否'} |"
            ]
        lines += [""]

    near = _near_duplicates(readable, info, max_distance)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    near.to_csv(NEAR_CSV, index=False, lineterminator="\n", encoding="utf-8")
    lines += ["## 4. 感知雜湊的可疑名單（只列出，不自動排除）", ""]
    lines += [
        "做法：每張圖縮成 64×64 灰階後做 DCT，取 16×16 的低頻係數與中位數比大小，"
        f"得到 {HASH_BITS} 個位元。",
        f"兩張圖相差 {max_distance} 個位元以內就列為可疑（門檻是經驗值，只決定名單長短）。",
        "「像素相關」是兩張圖縮成 256×256 後的像素相關係數，越接近 1 越像，供人工判斷時參考。",
        "像素完全相同的配對已在第 3 節處理，這裡不重複列。",
        "",
        "這份名單**不會**被切分腳本讀取，名單上的影像都還留在原本的組別。",
        "感知雜湊相近不等於同一張圖：同一位病人短時間內連拍的影像本來就很像。",
        "需要人看過才能判斷，要不要處理由使用者決定。",
        "",
        f"- 可疑配對共 {len(near):,} 對，完整名單在 `reports/{NEAR_CSV.name}`",
        "",
    ]
    if not near.empty:
        lines += ["| 類型 | 配對數 | 其中標籤不同 | 最小距離 |", "|---|---|---|---|"]
        for kind in NEAR_KINDS:
            part = near[near["kind"] == kind]
            if part.empty:
                lines += [f"| {kind} | 0 | 0 | - |"]
                continue
            lines += [
                f"| {kind} | {len(part):,} | {int((~part['same_labels']).sum()):,} "
                f"| {int(part['distance'].min())} |"
            ]
        lines += [""]
        lines += ["各距離的配對數：", "", "| 距離 | 配對數 |", "|---|---|"]
        hist = near["distance"].value_counts().sort_index()
        lines += [f"| {int(d)} | {int(n):,} |" for d, n in hist.items()]
        lines += [""]
        for kind in NEAR_KINDS:
            part = near[near["kind"] == kind]
            if part.empty:
                continue
            shown = part.head(NEAR_ROWS_IN_REPORT)
            title = f"### {kind}（{len(part):,} 對"
            title += f"，列出距離最小的 {len(shown)} 對）" if len(part) > len(shown) else "）"
            lines += [title, ""]
            lines += [
                "| 距離 | 像素相關 | 影像 A | 標籤 A | 影像 B | 標籤 B |",
                "|---|---|---|---|---|---|",
            ]
            lines += [
                f"| {r.distance} | {r.pixel_corr} | {r.image_a} | {r.labels_a} "
                f"| {r.image_b} | {r.labels_b} |"
                for r in shown.itertuples()
            ]
            lines += [""]

    out = REPORTS_DIR / "02_verify_images.md"
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"已寫出 {out}")
    bad = bool(expected ^ found) or len(unreadable) > 0
    return 2 if bad else 0


def main() -> int:
    """解析子指令並執行。"""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["md5", "extract", "scan", "report"])
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--phash-distance", type=int, default=PHASH_MAX_DISTANCE)
    args = parser.parse_args()
    if args.command == "md5":
        return cmd_md5()
    if args.command == "extract":
        return cmd_extract()
    if args.command == "scan":
        return cmd_scan(args.workers, args.phash_distance)
    return cmd_report(args.phash_distance)


if __name__ == "__main__":
    sys.exit(main())
