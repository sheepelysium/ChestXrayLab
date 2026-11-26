"""512 px 影像快取：把 1024×1024 的原圖縮小另存，訓練時從快取讀取（規格第 4.4 節）。

快取只是原圖的縮小版，檔名與原圖相同；不含標籤或任何中繼資料。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from chestxraylab.data import PROJECT_ROOT

CACHE_SIZE = 512
CACHE_DIR = PROJECT_ROOT / "data" / "cache" / f"images_{CACHE_SIZE}"


def to_cache_image(image: Image.Image, size: int = CACHE_SIZE) -> Image.Image:
    """把一張原圖轉成快取用的影像：8 位元灰階、``size``×``size``。

    灰階轉換與 Step 2 的像素雜湊相同（``convert("L")``），所以 RGBA 存檔的影像
    與灰階存檔的同一張圖會得到相同的快取。縮小用 BOX（區域平均）：1024 → 512 剛好是
    每 2×2 個像素取平均，不會像 LANCZOS 在銳利邊緣產生振鈴。

    Args:
        image: 原圖，任何 PIL 色彩模式。
        size: 輸出邊長。

    Returns:
        模式為 ``L``、大小為 ``(size, size)`` 的影像。
    """
    return image.convert("L").resize((size, size), Image.Resampling.BOX)


def write_cache_image(source: Path, dest: Path, size: int = CACHE_SIZE) -> None:
    """讀取 ``source``，轉成快取影像後以 PNG（無損）寫到 ``dest``。

    先寫到暫存檔再改名，所以中途被中斷不會留下寫到一半的 ``dest``。

    Args:
        source: 原圖路徑。
        dest: 快取檔路徑。
        size: 輸出邊長。
    """
    with Image.open(source) as image:
        small = to_cache_image(image, size)
    tmp = dest.with_name(dest.name + ".tmp")
    small.save(tmp, format="PNG")
    tmp.replace(dest)
