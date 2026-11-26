"""NIH ChestX-ray14 中繼資料的載入與基本檢查。

所有函式只讀 ``data/raw/meta`` 與 ``data/external`` 底下的官方檔案，不碰影像。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
META_DIR = RAW_DIR / "meta"
ARCHIVE_DIR = RAW_DIR / "archives"
IMAGE_DIR = RAW_DIR / "images"
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external"
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"
REPORTS_DIR = PROJECT_ROOT / "reports"

SEED = 42

# 順序固定：模型輸出、指標、報告都依這個順序。
CLASSES: tuple[str, ...] = (
    "Atelectasis",
    "Cardiomegaly",
    "Consolidation",
    "Edema",
    "Effusion",
    "Emphysema",
    "Fibrosis",
    "Hernia",
    "Infiltration",
    "Mass",
    "Nodule",
    "Pleural_Thickening",
    "Pneumonia",
    "Pneumothorax",
)
NO_FINDING = "No Finding"

IMAGE_COL = "image_id"
PATIENT_COL = "patient_id"
VIEW_COL = "view_position"

# 不可作為模型輸入（規格第 8 節第 3 條）；view_position、follow_up 只用於分群報告。
FORBIDDEN_INPUT_COLS: tuple[str, ...] = (
    IMAGE_COL,
    PATIENT_COL,
    VIEW_COL,
    "follow_up",
    "labels_raw",
    *CLASSES,
)

_ENTRY_COLUMNS = {
    "Image Index": IMAGE_COL,
    "Finding Labels": "labels_raw",
    "Follow-up #": "follow_up",
    "Patient ID": PATIENT_COL,
    "Patient Age": "age",
    "Patient Sex": "sex",
    "View Position": VIEW_COL,
}

# 框標註檔把浸潤寫成 Infiltrate，其餘名稱與 CLASSES 相同。
_BBOX_LABEL_FIX = {"Infiltrate": "Infiltration"}

# NIH 官方 LOG_CHESTXRAY.pdf（2026-10-09）公告的像素完全相同影像配對。
OFFICIAL_DUPLICATE_PAIRS: tuple[tuple[str, str], ...] = (
    ("00005681_024.png", "00027864_003.png"),
    ("00012388_000.png", "00017214_007.png"),
    ("00027864_000.png", "00028328_000.png"),
    ("00012388_001.png", "00017214_007.png"),
    ("00012388_001.png", "00012388_000.png"),
    ("00005403_024.png", "00005537_011.png"),
    ("00007108_008.png", "00027864_002.png"),
    ("00008182_001.png", "00011504_008.png"),
    ("00027864_001.png", "00028591_002.png"),
    ("00029402_001.png", "00029476_004.png"),
)

# 感知雜湊可疑名單中，經人工看圖確認是同一次拍攝（影像處理不同、像素不完全相同）、
# 且橫跨官方 train_val 與 test 的配對。加入這份清單需要使用者確認（規格第 4.2.1 節）。
CONFIRMED_NEAR_DUPLICATE_PAIRS: tuple[tuple[str, str], ...] = (
    ("00027864_004.png", "00027927_032.png"),
)


def load_metadata(path: Path | None = None) -> pd.DataFrame:
    """讀取官方 ``Data_Entry_2017_v2020.csv`` 並展開成每類一欄的 0/1 標籤。

    Args:
        path: CSV 路徑；預設為 ``data/raw/meta/Data_Entry_2017_v2020.csv``。

    Returns:
        每張影像一列。欄位為 ``image_id``、``patient_id``、``labels_raw``、``follow_up``、
        ``age``、``sex``、``view_position``、``no_finding`` 與 ``CLASSES`` 的 14 個 0/1 欄。

    Raises:
        ValueError: 缺少必要欄位、影像檔名重複，或出現規格以外的標籤名稱。
    """
    path = path or META_DIR / "Data_Entry_2017_v2020.csv"
    raw = pd.read_csv(path, dtype=str, keep_default_na=False, usecols=range(7))
    missing = [c for c in _ENTRY_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"中繼資料缺少欄位: {missing}")
    df = raw.rename(columns=_ENTRY_COLUMNS)[list(_ENTRY_COLUMNS.values())].copy()
    if not df[IMAGE_COL].is_unique:
        raise ValueError("中繼資料的影像檔名有重複")

    tokens = df["labels_raw"].str.split("|")
    unknown = sorted({t for row in tokens for t in row} - set(CLASSES) - {NO_FINDING})
    if unknown:
        raise ValueError(f"出現規格以外的標籤: {unknown}")
    for name in CLASSES:
        df[name] = tokens.map(lambda row, n=name: int(n in row)).astype("int8")
    df["no_finding"] = (df["labels_raw"] == NO_FINDING).astype("int8")
    df["age"] = df["age"].astype(int)
    df["follow_up"] = df["follow_up"].astype(int)
    return df


def load_official_lists(meta_dir: Path | None = None) -> tuple[list[str], list[str]]:
    """讀取官方 ``train_val_list.txt`` 與 ``test_list.txt``。

    Args:
        meta_dir: 放置兩個清單的目錄；預設為 ``data/raw/meta``。

    Returns:
        ``(train_val, test)`` 兩個影像檔名清單，順序與檔案相同。
    """
    meta_dir = meta_dir or META_DIR
    train_val = (meta_dir / "train_val_list.txt").read_text(encoding="utf-8").split()
    test = (meta_dir / "test_list.txt").read_text(encoding="utf-8").split()
    return train_val, test


def load_bboxes(path: Path | None = None) -> pd.DataFrame:
    """讀取官方框標註 ``BBox_List_2017.csv``。

    Args:
        path: CSV 路徑；預設為 ``data/raw/meta/BBox_List_2017.csv``。

    Returns:
        每個框一列，欄位為 ``image_id``、``label``（已對齊 ``CLASSES`` 的名稱）、
        ``x``、``y``、``w``、``h``（1024×1024 座標，``x``、``y`` 為左上角）。

    Raises:
        ValueError: 框的類別名稱不在 ``CLASSES`` 內。
    """
    path = path or META_DIR / "BBox_List_2017.csv"
    raw = pd.read_csv(path, usecols=range(6), header=0)
    raw.columns = [IMAGE_COL, "label", "x", "y", "w", "h"]
    raw["label"] = raw["label"].replace(_BBOX_LABEL_FIX)
    unknown = sorted(set(raw["label"]) - set(CLASSES))
    if unknown:
        raise ValueError(f"框標註出現未知類別: {unknown}")
    return raw


def load_drain_annotations(path: Path | None = None) -> pd.DataFrame:
    """讀取 NEATX 的 NIH 胸管標註（非醫師標註，CC BY-NC-SA，只用於分群報告）。

    Args:
        path: CSV 路徑；預設為
            ``data/external/NIH-CX14_TubeAnnotations_NonExperts_aggregated.csv``。

    Returns:
        欄位為 ``image_id`` 與 ``drain``（1 有胸管、0 沒有）。
    """
    path = path or EXTERNAL_DIR / "NIH-CX14_TubeAnnotations_NonExperts_aggregated.csv"
    raw = pd.read_csv(path)
    out = raw[["Image Index", "Drain"]].rename(columns={"Image Index": IMAGE_COL, "Drain": "drain"})
    out["drain"] = out["drain"].astype(int)
    return out


def duplicate_groups(
    pairs: tuple[tuple[str, str], ...] = OFFICIAL_DUPLICATE_PAIRS,
) -> list[list[str]]:
    """把重複影像的配對合併成群組（配對之間有共同影像時併成同一群）。

    Args:
        pairs: 像素完全相同的影像配對。

    Returns:
        每群一個排序過的檔名清單；群組之間依第一個檔名排序。
    """
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[max(root_a, root_b)] = min(root_a, root_b)
    groups: dict[str, list[str]] = {}
    for name in parent:
        groups.setdefault(find(name), []).append(name)
    return sorted(sorted(g) for g in groups.values())
