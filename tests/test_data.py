"""中繼資料載入的測試。用到官方檔案的測試在檔案不存在時跳過。"""

from __future__ import annotations

import pandas as pd
import pytest

from chestxraylab.data import (
    CLASSES,
    IMAGE_COL,
    META_DIR,
    PATIENT_COL,
    load_bboxes,
    load_metadata,
    load_official_lists,
)

HEADER = (
    "Image Index,Finding Labels,Follow-up #,Patient ID,Patient Age,Patient Sex,View Position,"
    "OriginalImage[Width,Height],OriginalImagePixelSpacing[x,y]\n"
)
needs_raw = pytest.mark.skipif(
    not (META_DIR / "Data_Entry_2017_v2020.csv").exists(), reason="需要官方中繼資料"
)


def test_labels_expand_to_one_column_per_class(tmp_path) -> None:
    path = tmp_path / "entry.csv"
    path.write_text(
        HEADER
        + "00000001_000.png,Cardiomegaly|Emphysema,0,1,57,M,PA,2682,2749,0.143,0.143\n"
        + "00000002_000.png,No Finding,0,2,80,F,AP,2500,2048,0.171,0.171\n",
        encoding="utf-8",
    )
    df = load_metadata(path)
    assert df.loc[0, "Cardiomegaly"] == 1 and df.loc[0, "Emphysema"] == 1
    assert df.loc[0, list(CLASSES)].sum() == 2
    assert df.loc[1, list(CLASSES)].sum() == 0 and df.loc[1, "no_finding"] == 1
    assert df[PATIENT_COL].tolist() == ["1", "2"]


def test_unknown_label_is_rejected(tmp_path) -> None:
    path = tmp_path / "entry.csv"
    path.write_text(HEADER + "a.png,Covid,0,1,57,M,PA,1,1,0.1,0.1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_metadata(path)


def test_classes_are_fourteen_and_sorted() -> None:
    assert len(CLASSES) == 14
    assert list(CLASSES) == sorted(CLASSES)


@needs_raw
def test_official_numbers() -> None:
    meta = load_metadata()
    train_val, test = load_official_lists()
    assert len(meta) == 112_120
    assert meta[PATIENT_COL].nunique() == 30_805
    assert (len(train_val), len(test)) == (86_524, 25_596)
    assert int(meta["Pneumothorax"].sum()) == 5_302
    assert int(meta["Hernia"].sum()) == 227
    tv_patients = set(meta[meta[IMAGE_COL].isin(set(train_val))][PATIENT_COL])
    test_patients = set(meta[meta[IMAGE_COL].isin(set(test))][PATIENT_COL])
    assert not tv_patients & test_patients


@needs_raw
def test_bboxes_use_class_names() -> None:
    bbox = load_bboxes()
    assert len(bbox) == 984
    assert set(bbox["label"]) <= set(CLASSES)
    assert isinstance(bbox, pd.DataFrame)
