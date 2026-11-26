# ChestXrayLab

在 NIH ChestX-ray14 上微調影像模型，做 14 類胸部 X 光多標籤分類的實驗（作品集與學習用專案）。

**非醫療用途**：本專案只用於研究與學習，不可用於診斷或任何臨床決策。

目前進度：M1（資料盤點、完整性核對、切分）。規格見 [`DEV_SPEC.md`](DEV_SPEC.md)。

## 資料

- 資料集：NIH ChestX-ray14，下載頁 https://nihcc.app.box.com/v/ChestXray-NIHCC
- 提供者：NIH Clinical Center。使用不受限，但需註明下載來源、致謝 NIH Clinical Center 並引用論文
- 引用：Wang X, Peng Y, Lu L, Lu Z, Bagheri M, Summers RM. *ChestX-ray8: Hospital-scale Chest X-ray Database and Benchmarks on Weakly-Supervised Classification and Localization of Common Thorax Diseases.* IEEE CVPR 2017.
- 胸管標註：NEATX（https://zenodo.org/records/14944064），CC BY-NC-SA，標註者不是醫師，只用於分群報告

原始資料不進版控。

## 執行

```
uv sync
bash scripts/download_images.sh 0 1            # 下載 12 個官方壓縮檔（約 45 GB）
uv run python scripts/01_inventory.py          # 用官方中繼資料核對數字
uv run python scripts/02_verify_images.py md5  # 對照官方 MD5
uv run python scripts/02_verify_images.py extract
uv run python scripts/02_verify_images.py scan # 逐張開啟並找重複影像
uv run python scripts/03_split.py              # 切分預覽
uv run pytest
```

Windows 終端請先設定 `PYTHONIOENCODING=utf-8`。

## 在另一台機器重建資料

影像、中繼資料、胸管標註與模型權重都不進版控，換機器要重新取得。切分不用重做：`data/splits/split_v1.csv` 跟著 repo 走，讀取時會驗證 SHA-256。

1. `git clone` 後執行 `uv sync`
2. 從 [NIH 官方下載頁](https://nihcc.app.box.com/v/ChestXray-NIHCC)手動下載下列檔案，放進 `data/raw/meta/`：
   `Data_Entry_2017_v2020.csv`、`train_val_list.txt`、`test_list.txt`、`BBox_List_2017.csv`
   （`README_CHESTXRAY.pdf`、`FAQ_CHESTXRAY.pdf`、`LOG_CHESTXRAY.pdf` 是說明文件，可一併下載備查）
3. 從 [NEATX 的 Zenodo 頁面](https://zenodo.org/records/14944064)下載 `NIH-CX14_TubeAnnotations_NonExperts_aggregated.csv`，放進 `data/external/`
4. `bash scripts/download_images.sh 0 1` 下載影像（可續傳；想並行就開 4 個終端分別跑 `0 4`、`1 4`、`2 4`、`3 4`）
5. 依序執行 `02_verify_images.py` 的 `md5`、`extract`、`scan`。`scan` 產出的 `reports/02_verify_images.md` 應與 repo 內的版本相同（`git diff` 沒有差異），代表這台機器的影像與鎖定切分時用的那份一致
6. `uv run pytest`

磁碟需求：壓縮檔約 45 GB，解壓後約 45 GB。壓縮檔在 MD5 相符且解壓完成後可以刪除。

## 限制

- **非醫療用途**：結果不可用於診斷、分診或任何臨床決策
- **單一機構**：資料全部來自 NIH Clinical Center
- **標籤有雜訊**：標籤是用 NLP 從放射科報告抽取的，官方估計正確率高於 90%，不是醫師逐張標註
- **官方 test 與訓練集組成不同**：test 的異常比例與床邊拍攝（AP）比例都明顯較高，val 與 test 的分數不能直接比
- **資料內有重複影像**：NIH 於 2026-10-09 公告有像素完全相同的影像掛在不同病人名下，部分橫跨官方 train 與 test
