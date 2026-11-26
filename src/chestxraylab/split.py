"""切分：test 用 NIH 官方清單，val 從官方 train_val 按病人切出。

鎖定後的 ``data/splits/split_v1.csv`` 只能讀取（規格第 8 節第 2 條）。
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from pathlib import Path

import numpy as np
import pandas as pd

from chestxraylab.data import IMAGE_COL, PATIENT_COL, SEED, SPLITS_DIR

SPLIT_CSV = SPLITS_DIR / "split_v1.csv"
SPLIT_SHA256 = SPLITS_DIR / "split_v1.sha256"
SPLIT_NAMES: tuple[str, ...] = ("train", "val", "test", "excluded")
SPLIT_COLUMNS: tuple[str, ...] = (IMAGE_COL, PATIENT_COL, "split", "excluded_reason")
VAL_FRACTION = 0.10


def assign_val_patients(
    patient_ids: Iterable[str], *, val_fraction: float = VAL_FRACTION, seed: int = SEED
) -> set[str]:
    """從 train_val 的病人中抽出 val 的病人。

    先把病人編號排序再用固定種子洗牌，所以結果只取決於「有哪些病人」與種子，
    和輸入順序無關。

    Args:
        patient_ids: 官方 train_val 內的病人編號（可重複）。
        val_fraction: val 佔病人數的比例。
        seed: 隨機種子。

    Returns:
        被分到 val 的病人編號集合。

    Raises:
        ValueError: ``val_fraction`` 不在 (0, 1) 之間。
    """
    if not 0 < val_fraction < 1:
        raise ValueError("val_fraction 必須介於 0 與 1 之間")
    patients = sorted(set(patient_ids))
    order = np.random.default_rng(seed).permutation(len(patients))
    n_val = round(len(patients) * val_fraction)
    return {patients[i] for i in order[:n_val]}


def duplicate_exclusions(
    groups: Iterable[Iterable[str]], official: Mapping[str, str]
) -> dict[str, str]:
    """決定重複影像群組中哪些影像要從 train／val 排除。

    規則：群組內所有屬於官方 train_val 的影像都排除；官方 test 的影像一律保留，
    因為 test 必須和官方清單完全相同。

    Args:
        groups: 像素完全相同的影像群組。
        official: 影像檔名到官方切分（``"train_val"`` 或 ``"test"``）的對應。

    Returns:
        要排除的影像檔名到排除原因的對應。
    """
    out: dict[str, str] = {}
    for group in groups:
        members = sorted(group)
        has_test = any(official[m] == "test" for m in members)
        reason = "duplicate_of_test" if has_test else "duplicate_within_train_val"
        for m in members:
            if official[m] == "train_val":
                out[m] = reason
    return out


def near_duplicate_exclusions(
    pairs: Iterable[tuple[str, str]], official: Mapping[str, str]
) -> dict[str, str]:
    """決定人工確認過的近似重複配對中哪些影像要排除。

    規則：配對橫跨官方 train_val 與 test 時，排除 train_val 那一邊；test 一律保留。
    兩張都在同一邊的配對不處理。

    Args:
        pairs: 人工確認為同一次拍攝的影像配對。
        official: 影像檔名到官方切分（``"train_val"`` 或 ``"test"``）的對應。

    Returns:
        要排除的影像檔名到排除原因的對應。
    """
    out: dict[str, str] = {}
    for a, b in pairs:
        if official[a] == official[b]:
            continue
        out[a if official[a] == "train_val" else b] = "near_duplicate_of_test"
    return out


def build_split_table(
    meta: pd.DataFrame,
    train_val: Iterable[str],
    test: Iterable[str],
    *,
    exclusions: Mapping[str, str] | None = None,
    val_fraction: float = VAL_FRACTION,
    seed: int = SEED,
) -> pd.DataFrame:
    """建立切分表。

    Args:
        meta: ``load_metadata`` 的結果。
        train_val: 官方 train_val 影像清單。
        test: 官方 test 影像清單。
        exclusions: 要從 train／val 排除的影像與原因；不可包含 test 的影像。
        val_fraction: val 佔 train_val 病人數的比例。
        seed: 隨機種子。

    Returns:
        欄位為 ``SPLIT_COLUMNS`` 的表，依 ``image_id`` 排序。val 的病人在排除前就決定，
        所以排除清單改變不會讓其他病人換組。

    Raises:
        ValueError: 官方清單與中繼資料對不上，或排除清單包含 test 的影像。
    """
    exclusions = dict(exclusions or {})
    tv_set, test_set = set(train_val), set(test)
    if tv_set & test_set or (tv_set | test_set) != set(meta[IMAGE_COL]):
        raise ValueError("官方清單與中繼資料的影像對不上")
    if set(exclusions) & test_set:
        raise ValueError("排除清單不可包含官方 test 的影像")
    if set(exclusions) - tv_set:
        raise ValueError("排除清單有不在官方 train_val 內的影像")

    table = meta[[IMAGE_COL, PATIENT_COL]].copy()
    in_tv = table[IMAGE_COL].isin(tv_set)
    val_patients = assign_val_patients(
        table.loc[in_tv, PATIENT_COL], val_fraction=val_fraction, seed=seed
    )
    table["split"] = "test"
    table.loc[in_tv, "split"] = "train"
    table.loc[in_tv & table[PATIENT_COL].isin(val_patients), "split"] = "val"
    table["excluded_reason"] = table[IMAGE_COL].map(lambda name: exclusions.get(name, ""))
    table.loc[table["excluded_reason"] != "", "split"] = "excluded"
    table = table.sort_values(IMAGE_COL).reset_index(drop=True)
    validate_split(table, test_images=test_set)
    return table[list(SPLIT_COLUMNS)]


def validate_split(table: pd.DataFrame, *, test_images: set[str] | None = None) -> None:
    """檢查切分表的不變量。

    Args:
        table: 切分表。
        test_images: 官方 test 影像集合；有給就檢查 test 是否與它完全相同。

    Raises:
        ValueError: 欄位不符、影像重複、組名不合法、病人跨組，或 test 與官方清單不同。
    """
    if tuple(table.columns) != SPLIT_COLUMNS:
        raise ValueError(f"切分表欄位應為 {SPLIT_COLUMNS}")
    if not table[IMAGE_COL].is_unique:
        raise ValueError("切分表的影像有重複")
    if not set(table["split"]) <= set(SPLIT_NAMES):
        raise ValueError("切分表出現不合法的組名")
    used = table[table["split"] != "excluded"]
    crossing = used.groupby(PATIENT_COL)["split"].nunique()
    if (crossing > 1).any():
        raise ValueError(f"有 {int((crossing > 1).sum())} 位病人跨組")
    if (
        test_images is not None
        and set(table.loc[table["split"] == "test", IMAGE_COL]) != test_images
    ):
        raise ValueError("test 與官方清單不同")


def sha256_of(path: Path) -> str:
    """計算檔案的 SHA-256（十六進位小寫）。"""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def table_bytes(table: pd.DataFrame) -> bytes:
    """把切分表轉成要寫進檔案的位元組（UTF-8、``\\n`` 換行）。"""
    return table.to_csv(index=False, lineterminator="\n").encode("utf-8")


def write_split(
    table: pd.DataFrame, *, csv_path: Path = SPLIT_CSV, sha_path: Path = SPLIT_SHA256
) -> str:
    """鎖定切分：以獨占方式寫出 CSV 與雜湊檔，已存在就拒絕。

    Args:
        table: 切分表。
        csv_path: CSV 輸出路徑。
        sha_path: 雜湊檔輸出路徑（內容為一行 64 字元的 hex）。

    Returns:
        CSV 的 SHA-256。

    Raises:
        FileExistsError: 任一輸出檔已存在。
    """
    validate_split(table)
    if csv_path.exists() or sha_path.exists():
        raise FileExistsError("切分已鎖定，不可覆寫")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    payload = table_bytes(table)
    digest = hashlib.sha256(payload).hexdigest()
    try:
        with csv_path.open("xb") as fh:
            fh.write(payload)
        with sha_path.open("x", encoding="utf-8", newline="\n") as fh:
            fh.write(digest + "\n")
    except OSError:
        csv_path.unlink(missing_ok=True)
        sha_path.unlink(missing_ok=True)
        raise
    return digest


def load_split(*, csv_path: Path = SPLIT_CSV, sha_path: Path = SPLIT_SHA256) -> pd.DataFrame:
    """讀取鎖定的切分表，讀之前先驗證雜湊。

    Raises:
        ValueError: CSV 的雜湊與雜湊檔不符。
    """
    expected = sha_path.read_text(encoding="utf-8").strip()
    if sha256_of(csv_path) != expected:
        raise ValueError("split_v1.csv 的雜湊與 split_v1.sha256 不符，檔案可能被改過")
    table = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    validate_split(table)
    return table
