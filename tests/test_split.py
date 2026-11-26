"""切分邏輯的測試（用小型假資料，不需要原始資料）。"""

from __future__ import annotations

import pandas as pd
import pytest

from chestxraylab.data import IMAGE_COL, PATIENT_COL, duplicate_groups
from chestxraylab.split import (
    assign_val_patients,
    build_split_table,
    duplicate_exclusions,
    load_split,
    near_duplicate_exclusions,
    validate_split,
    write_split,
)


def _toy() -> tuple[pd.DataFrame, list[str], list[str]]:
    rows = []
    for p in range(100):
        for k in range(1 + p % 4):
            rows.append({IMAGE_COL: f"{p:08d}_{k:03d}.png", PATIENT_COL: str(p)})
    meta = pd.DataFrame(rows)
    test = meta[meta[PATIENT_COL].astype(int) >= 80][IMAGE_COL].tolist()
    train_val = meta[meta[PATIENT_COL].astype(int) < 80][IMAGE_COL].tolist()
    return meta, train_val, test


def test_val_patients_are_deterministic_and_order_independent() -> None:
    ids = [str(i) for i in range(200)]
    a = assign_val_patients(ids)
    b = assign_val_patients(list(reversed(ids)) + ids)
    assert a == b
    assert len(a) == 20


def test_val_fraction_must_be_valid() -> None:
    with pytest.raises(ValueError):
        assign_val_patients(["1", "2"], val_fraction=1.0)


def test_no_patient_crosses_splits_and_test_is_official() -> None:
    meta, train_val, test = _toy()
    table = build_split_table(meta, train_val, test)
    per_patient = table.groupby(PATIENT_COL)["split"].nunique()
    assert (per_patient == 1).all()
    assert set(table.loc[table["split"] == "test", IMAGE_COL]) == set(test)
    assert set(table["split"]) == {"train", "val", "test"}


def test_exclusions_do_not_move_other_patients() -> None:
    meta, train_val, test = _toy()
    base = build_split_table(meta, train_val, test)
    victim = train_val[0]
    changed = build_split_table(meta, train_val, test, exclusions={victim: "duplicate_of_test"})
    merged = base.merge(changed, on=IMAGE_COL, suffixes=("_a", "_b"))
    differ = merged[merged["split_a"] != merged["split_b"]]
    assert differ[IMAGE_COL].tolist() == [victim]
    assert differ["split_b"].tolist() == ["excluded"]


def test_test_images_cannot_be_excluded() -> None:
    meta, train_val, test = _toy()
    with pytest.raises(ValueError):
        build_split_table(meta, train_val, test, exclusions={test[0]: "x"})


def test_duplicate_groups_merge_shared_members() -> None:
    groups = duplicate_groups((("b", "c"), ("a", "b"), ("x", "y")))
    assert groups == [["a", "b", "c"], ["x", "y"]]


def test_duplicate_exclusions_keep_test_and_drop_train_val() -> None:
    official = {"a": "train_val", "b": "test", "c": "train_val", "d": "train_val", "e": "test"}
    out = duplicate_exclusions([["a", "b"], ["c", "d"], ["b", "e"]], official)
    assert out == {
        "a": "duplicate_of_test",
        "c": "duplicate_within_train_val",
        "d": "duplicate_within_train_val",
    }


def test_near_duplicate_exclusions_only_drop_train_val_side_of_crossing_pairs() -> None:
    official = {"a": "train_val", "b": "test", "c": "train_val", "d": "train_val", "e": "test"}
    out = near_duplicate_exclusions([("b", "a"), ("c", "d"), ("b", "e")], official)
    assert out == {"a": "near_duplicate_of_test"}


def test_validate_rejects_patient_in_two_splits() -> None:
    meta, train_val, test = _toy()
    table = build_split_table(meta, train_val, test)
    patient = table.loc[table["split"] == "train", PATIENT_COL].iloc[0]
    rows = table.index[table[PATIENT_COL] == patient]
    broken = table.copy()
    broken.loc[rows[0], "split"] = "val"
    if len(rows) == 1:
        extra = broken.loc[[rows[0]]].assign(**{IMAGE_COL: "extra.png", "split": "train"})
        broken = pd.concat([broken, extra], ignore_index=True)
    with pytest.raises(ValueError):
        validate_split(broken)


def test_write_is_exclusive_and_load_checks_hash(tmp_path) -> None:
    meta, train_val, test = _toy()
    table = build_split_table(meta, train_val, test)
    csv_path, sha_path = tmp_path / "split.csv", tmp_path / "split.sha256"
    digest = write_split(table, csv_path=csv_path, sha_path=sha_path)
    assert sha_path.read_text(encoding="utf-8") == digest + "\n"
    assert b"\r\n" not in csv_path.read_bytes()
    loaded = load_split(csv_path=csv_path, sha_path=sha_path)
    pd.testing.assert_frame_equal(loaded, table, check_dtype=False)
    with pytest.raises(FileExistsError):
        write_split(table, csv_path=csv_path, sha_path=sha_path)
    csv_path.write_bytes(csv_path.read_bytes() + b"x")
    with pytest.raises(ValueError):
        load_split(csv_path=csv_path, sha_path=sha_path)
