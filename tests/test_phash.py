"""感知雜湊的測試（用合成影像，不需要原始資料）。"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image, ImageEnhance

from chestxraylab.phash import HASH_BITS, HASH_WORDS, hex_to_words, near_pairs, phash_hex


def _synthetic(seed: int, size: int = 512) -> Image.Image:
    """產生一張有大塊明暗結構的灰階影像（把低解析度雜訊放大）。"""
    rng = np.random.default_rng(seed)
    coarse = rng.integers(0, 256, size=(16, 16), dtype=np.uint8)
    return Image.fromarray(coarse, mode="L").resize((size, size), Image.Resampling.BICUBIC)


def _distance(a: str, b: str) -> int:
    words = hex_to_words([a, b])
    return int(np.bitwise_count(words[0] ^ words[1]).sum())


def test_hash_has_expected_length_and_is_deterministic() -> None:
    image = _synthetic(0)
    assert len(phash_hex(image)) == HASH_BITS // 4
    assert phash_hex(image) == phash_hex(image.copy())


def test_same_picture_in_different_mode_and_size_is_close() -> None:
    image = _synthetic(1)
    base = phash_hex(image)
    assert _distance(base, phash_hex(image.convert("RGBA"))) == 0
    assert _distance(base, phash_hex(image.resize((1024, 1024)))) <= 8
    assert _distance(base, phash_hex(ImageEnhance.Brightness(image).enhance(1.05))) <= 8


def test_different_pictures_are_far() -> None:
    assert _distance(phash_hex(_synthetic(2)), phash_hex(_synthetic(3))) > 60


def test_hex_to_words_shape_and_validation() -> None:
    words = hex_to_words([phash_hex(_synthetic(4)), phash_hex(_synthetic(5))])
    assert words.shape == (2, HASH_WORDS)
    with pytest.raises(ValueError):
        hex_to_words(["abcd"])


def test_near_pairs_matches_brute_force_across_chunks() -> None:
    rng = np.random.default_rng(42)
    words = rng.integers(0, 2**63, size=(40, HASH_WORDS), dtype=np.uint64)
    words[17] = words[3]  # 距離 0
    words[30] = words[5]
    words[30, 0] ^= np.uint64(0b111)  # 距離 3
    pairs = near_pairs(words, max_distance=4, chunk=7)
    assert pairs.tolist() == [[3, 17, 0], [5, 30, 3]]
    assert near_pairs(words, max_distance=2, chunk=7).tolist() == [[3, 17, 0]]
