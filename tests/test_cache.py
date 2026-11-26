"""512 px 快取的測試（用合成影像，不需要原始資料）。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from chestxraylab.cache import CACHE_SIZE, to_cache_image, write_cache_image


def _synthetic(seed: int, size: int = 1024) -> Image.Image:
    rng = np.random.default_rng(seed)
    return Image.fromarray(rng.integers(0, 256, size=(size, size), dtype=np.uint8), mode="L")


def test_output_is_grayscale_at_cache_size() -> None:
    small = to_cache_image(_synthetic(0))
    assert small.mode == "L"
    assert small.size == (CACHE_SIZE, CACHE_SIZE)


def test_downscale_is_2x2_average() -> None:
    image = _synthetic(1)
    pixels = np.asarray(image, dtype=np.float64)
    expected = pixels.reshape(CACHE_SIZE, 2, CACHE_SIZE, 2).mean(axis=(1, 3))
    got = np.asarray(to_cache_image(image), dtype=np.float64)
    assert np.abs(got - expected).max() <= 1.0


def test_rgba_and_grayscale_give_same_cache() -> None:
    image = _synthetic(2)
    assert to_cache_image(image).tobytes() == to_cache_image(image.convert("RGBA")).tobytes()


def test_write_cache_image_round_trips_and_leaves_no_tmp(tmp_path: Path) -> None:
    source, dest = tmp_path / "src.png", tmp_path / "out" / "src.png"
    dest.parent.mkdir()
    image = _synthetic(3)
    image.save(source)
    write_cache_image(source, dest)
    with Image.open(dest) as saved:
        assert saved.tobytes() == to_cache_image(image).tobytes()
    assert [p.name for p in dest.parent.iterdir()] == ["src.png"]
