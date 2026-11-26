"""感知雜湊（perceptual hash）：找出看起來幾乎相同、但像素不完全相同的影像。

結果只用來列可疑名單，不用來自動排除影像（規格第 4.2.1 節）。

做法是標準的 pHash：縮小成 64×64 灰階 → 二維 DCT → 取左上角 16×16 的低頻係數 →
每個係數與中位數比大小，得到 256 個位元。兩張圖的雜湊相差的位元數（Hamming 距離）
越小，畫面越像；重新存檔、輕微亮度或大小變化只會改變少數幾個位元。
"""

from __future__ import annotations

import numpy as np
from PIL import Image

HASH_SIZE = 16
RESIZE = HASH_SIZE * 4
HASH_BITS = HASH_SIZE * HASH_SIZE
HASH_WORDS = HASH_BITS // 64


def _dct_matrix(n: int) -> np.ndarray:
    """回傳 n×n 的 DCT-II 轉換矩陣（未正規化；只比大小，不需要正規化）。"""
    k = np.arange(n)[:, None]
    x = np.arange(n)[None, :]
    return np.cos(np.pi * (2 * x + 1) * k / (2 * n))


_DCT = _dct_matrix(RESIZE)


def phash_hex(image: Image.Image) -> str:
    """計算一張影像的 256 位元感知雜湊。

    Args:
        image: 任何色彩模式的 PIL 影像。

    Returns:
        64 個十六進位字元的字串。
    """
    small = image.convert("L").resize((RESIZE, RESIZE), Image.Resampling.LANCZOS)
    pixels = np.asarray(small, dtype=np.float64)
    low = (_DCT @ pixels @ _DCT.T)[:HASH_SIZE, :HASH_SIZE]
    bits = (low > np.median(low)).reshape(-1)
    return np.packbits(bits).tobytes().hex()


def hex_to_words(hashes: list[str]) -> np.ndarray:
    """把十六進位雜湊轉成 ``(N, HASH_WORDS)`` 的 uint64 陣列，方便批次算距離。

    Args:
        hashes: ``phash_hex`` 的輸出。

    Returns:
        形狀 ``(len(hashes), HASH_WORDS)`` 的 uint64 陣列。

    Raises:
        ValueError: 有雜湊的長度不是 ``HASH_BITS / 4`` 個字元。
    """
    if any(len(h) != HASH_BITS // 4 for h in hashes):
        raise ValueError("感知雜湊的長度不正確")
    raw = np.frombuffer(bytes.fromhex("".join(hashes)), dtype=np.uint64)
    return raw.reshape(len(hashes), HASH_WORDS)


def near_pairs(words: np.ndarray, max_distance: int, *, chunk: int = 256) -> np.ndarray:
    """找出 Hamming 距離不超過門檻的所有配對（暴力比對，分批做以控制記憶體）。

    Args:
        words: ``hex_to_words`` 的輸出。
        max_distance: 距離門檻（含）。
        chunk: 每批比對的列數。

    Returns:
        形狀 ``(M, 3)`` 的整數陣列，每列為 ``(i, j, 距離)`` 且 ``i < j``，
        依 ``(距離, i, j)`` 排序。
    """
    n = len(words)
    found: list[np.ndarray] = []
    for start in range(0, n, chunk):
        block = words[start : start + chunk]
        rest = words[start:]
        dist = np.zeros((len(block), len(rest)), dtype=np.uint16)
        for w in range(words.shape[1]):
            dist += np.bitwise_count(block[:, None, w] ^ rest[None, :, w])
        rows, cols = np.nonzero(dist <= max_distance)
        keep = cols > rows  # rest 從 start 起算，cols > rows 等於 j > i
        rows, cols = rows[keep], cols[keep]
        if len(rows):
            found.append(np.stack([rows + start, cols + start, dist[rows, cols]], axis=1))
    if not found:
        return np.empty((0, 3), dtype=np.int64)
    pairs = np.concatenate(found).astype(np.int64)
    order = np.lexsort((pairs[:, 1], pairs[:, 0], pairs[:, 2]))
    return pairs[order]
