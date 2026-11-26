# ChestXrayLab

## 專案定位

求職作品集＋學習用專案：在 NIH ChestX-ray14 上微調影像模型做 14 類胸部 X 光多標籤分類，比較微調方式與預訓練來源，並檢查模型有沒有走捷徑。

- 非醫療用途，README 與報告都不可寫成診斷工具
- 使用者正在求職，目標職缺要求「CV + 微調模型」；沒有醫療背景，解釋醫療概念時用白話
- 硬體：單張 RTX 5080（16 GB），實驗以本機跑得完為準
- Repo：https://github.com/sheepelysium/ChestXrayLab（單人專案，直接 commit 到 `main`）

## 規格文件

完整規格在 [`DEV_SPEC.md`](DEV_SPEC.md)。動手前先讀完，以它為準。規格與實際資料矛盾時**停下來回報，不要自行假設**。

## 學習方式（家教模式）

主線採家教模式：agent 當家教，使用者當學生。使用者目前還無法不靠 AI 從零寫程式。

- 留給使用者寫的只有三個函式，各 10 到 30 行：`train_step`（M2）、不平衡 loss（M3）、LoRA 設定（M4）
- 每個函式由 agent 先寫好介面與測試，使用者寫完、測試通過才算完成；沒完成前該里程碑的訓練不開跑
- `TODO(human)` 只能出現在 `src/chestxraylab/train_step.py`、`losses.py`、`lora.py`，其他地方出現會讓測試失敗
- 使用者卡住時提示分三段，一次只給一段：先講觀念，再給方向，最後才給程式碼。不可以一開始就給答案
- 其餘全部由 agent 實作，並用 Insight 段落說明設計理由
- 每個里程碑結束時，從規格第 2.2 節的七題挑相關的考使用者；M6 結束時七題全考

## 不可違反的規則

1. 同一位病人的影像不可跨 train／val／test
2. test 使用 NIH 官方 `test_list.txt`，原樣使用；`data/splits/split_v1.csv` 鎖定後只能讀取。重複影像依規格第 4.2.1 節處理：只排除 train_val 那一邊，test 一律不動；感知雜湊結果只列名單不自動排除
3. 調參、選模型、早停只用 train／val；**test 每個版本只評估一次**，集中在 M6，上 test 的版本清單要先給使用者確認
4. 需要閾值的指標（recall、precision、F1），閾值只在 val 上以固定 sensitivity 決定（不用最大化 F1），上 test 時沿用，不可看 test 再調；val 與 test 的 AUPRC 不可直接比較（盛行率不同），報告要註明
5. 不可作為模型輸入：標籤、Patient ID、檔名、View Position、Follow-up #、胸管標註（後三者只用於分群報告）
6. 不 commit 原始影像、快取、模型權重、NEATX 檔案；只 commit 程式碼、報告、切分清單與雜湊
7. 隨機種子固定為 42；數字不如預期時只回報，**不可自行換種子重跑挑結果**
8. 預訓練權重用過 NIH 影像的，所有表格都要標註。RAD-DINO 的標註文字固定為「預訓練看過全部 NIH 影像（含 val 與 test）」
9. 每個里程碑結束時在 `reports/` 產出 Markdown 報告並回報關鍵數字，**等使用者確認後才做下一個**

## 環境與指令

- Windows 11，終端編碼 cp950：執行 Python 前先設 `PYTHONIOENCODING=utf-8`；程式輸出不用 emoji；讀寫檔明確指定 `encoding="utf-8"`
- Python 3.11，環境管理用 **uv**（不用 conda／全域 pip）

```
uv sync
uv run python scripts/01_inventory.py
uv run pytest
uv run ruff format . ; uv run ruff check .
```

## 目錄結構

```
data/raw/meta/       官方中繼資料、切分清單、README／FAQ／LOG（不進版控）
data/raw/archives/   官方影像壓縮檔（不進版控）
data/raw/images/     解壓後的 PNG（不進版控）
data/cache/          512 px 快取（不進版控）
data/external/       NEATX 胸管標註（不進版控）
data/splits/         split_v1.csv 與 split_v1.sha256（進版控，固定 \n 換行）
src/chestxraylab/    data / split / 之後的 transforms / models / train / losses / lora / metrics
scripts/             每個步驟的腳本
reports/             每步驟報告與圖表
checkpoints/         模型權重（不進版控）
tests/
```

## 程式風格

- 格式化與 lint 用 `ruff`；docstring 用 Google style；例外處理要具體，不用裸 `except Exception`
- 只改被要求的部分：不順手重構、不加規格沒要求的功能
- 回報與文件用繁體中文，技術術語與識別符保持原文

## Git

- commit 訊息格式：`feat/fix/docs/refactor/chore: 中文說明`，一次 commit 只做一件事
- **只在使用者要求時 commit 或 push**
- 不用 `git add -A`；提交前用 `git ls-files --others --exclude-standard` 確認沒有夾帶資料或產出物
