# M1 總結：資料

各步驟的完整內容見 `01_inventory.md`、`02_verify_images.md`、`03_split.md`、`04_cache.md`。

## 1. 關鍵數字

- 影像 112,120 張、病人 30,805 位；12 個壓縮檔 MD5 與官方相符，全部影像可開啟
- 官方 train_val 與 test 沒有共用病人；train、val、test 之間沒有共用病人（讀取切分表時驗證）
- 512 px 快取：全部影像，8 位元灰階 PNG

| 組 | 病人 | 影像 |
|---|---|---|
| train | 25,206 | 77,706 |
| val | 2,801 | 8,783 |
| test | 2,797 | 25,596 |
| excluded | 19 | 35 |

### 切分清單的雜湊

- `split_v1.sha256` 記錄的值：`aa84f99e60465f3c38b4d419ddcabd0bb362ea3b170758ff72985e93cb59cdd7`
- 現在對 `split_v1.csv` 重新計算：`aa84f99e60465f3c38b4d419ddcabd0bb362ea3b170758ff72985e93cb59cdd7`
- 結果：**相符，鎖定後沒有變動**

## 2. RGBA 存檔的影像

原圖中有 519 張存成 RGBA（4 個色版），其餘 111,601 張是單色版灰階。

### 2.1 逐張檢查色版

- R、G、B 三個色版逐像素完全相同：519 / 519 張
- alpha 全為 255（完全不透明）：519 / 519 張
- 不符合上述任一項：0 張

全部符合，代表這些影像只是「灰階圖用 4 個色版存檔」，多出來的色版沒有額外資訊。
快取用 `convert("L")` 轉成單色版：R=G=B 時轉換結果就等於 R，alpha 直接丟棄，所以轉換沒有損失，快取裡也看不出一張圖原本是不是 RGBA。

### 2.2 這群影像落在哪裡

- 涉及病人 469 位；檔名範圍 00000004_000.png 到 00030805_000.png

| 組 | RGBA 張數 | RGBA 比例 | 其餘張數 | 其餘比例 |
|---|---|---|---|---|
| train | 416 | 80.2% | 77,290 | 69.3% |
| val | 47 | 9.1% | 8,736 | 7.8% |
| test | 56 | 10.8% | 25,540 | 22.9% |
| excluded | 0 | 0.0% | 35 | 0.0% |

| 拍攝方式 | RGBA 張數 | RGBA 比例 | 其餘張數 | 其餘比例 |
|---|---|---|---|---|
| PA | 335 | 64.5% | 66,975 | 60.0% |
| AP | 184 | 35.5% | 44,626 | 40.0% |

### 2.3 標籤分布

「比例倍數」是 RGBA 那群的陽性比例除以其餘影像的陽性比例。
RGBA 只有幾百張，陽性不到 10 張的類別比例很不穩定。

| 標籤 | RGBA 陽性 | RGBA 比例 | 其餘陽性 | 其餘比例 | 比例倍數 |
|---|---|---|---|---|---|
| Atelectasis | 37 | 7.1% | 11,522 | 10.3% | 0.69 |
| Cardiomegaly | 7 | 1.3% | 2,769 | 2.5% | 0.54 |
| Consolidation | 13 | 2.5% | 4,654 | 4.2% | 0.60 |
| Edema | 10 | 1.9% | 2,293 | 2.1% | 0.94 |
| Effusion | 46 | 8.9% | 13,271 | 11.9% | 0.75 |
| Emphysema | 9 | 1.7% | 2,507 | 2.2% | 0.77 |
| Fibrosis | 10 | 1.9% | 1,676 | 1.5% | 1.28 |
| Hernia | 0 | 0.0% | 227 | 0.2% | 0.00 |
| Infiltration | 59 | 11.4% | 19,835 | 17.8% | 0.64 |
| Mass | 17 | 3.3% | 5,765 | 5.2% | 0.63 |
| Nodule | 27 | 5.2% | 6,304 | 5.6% | 0.92 |
| Pleural_Thickening | 8 | 1.5% | 3,377 | 3.0% | 0.51 |
| Pneumonia | 10 | 1.9% | 1,421 | 1.3% | 1.51 |
| Pneumothorax | 12 | 2.3% | 5,290 | 4.7% | 0.49 |
| no_finding | 345 | 66.5% | 60,016 | 53.8% | 1.24 |

### 2.4 亮度

每張圖取 512 px 快取的平均像素值（0 到 255），再看這個值在兩群影像中的分布。
拍攝方式會影響亮度，所以同時列出 PA、AP 各自的比較。

| 範圍 | 群 | 張數 | 平均 | 標準差 | 第 5 百分位 | 中位數 | 第 95 百分位 |
|---|---|---|---|---|---|---|---|
| 全部 | RGBA | 519 | 152.6 | 22.0 | 107.1 | 159.2 | 177.3 |
| 全部 | 其餘 | 111,601 | 127.3 | 22.2 | 98.2 | 122.4 | 168.1 |
| PA | RGBA | 335 | 159.9 | 15.0 | 128.1 | 161.8 | 177.4 |
| PA | 其餘 | 66,975 | 129.0 | 23.7 | 98.0 | 123.9 | 171.8 |
| AP | RGBA | 184 | 139.2 | 26.0 | 103.5 | 140.2 | 176.1 |
| AP | 其餘 | 44,626 | 124.9 | 19.6 | 98.6 | 120.6 | 159.3 |

### 2.5 判讀：會不會成為捷徑

- **檔案格式本身不會**：模型讀的是單色版快取，第 2.1 節確認轉換沒有損失，快取裡沒有留下「原本是 RGBA」的痕跡
- **但這群影像本身和其餘影像不一樣**，差異在轉成快取後仍然存在：
  - 比較亮：平均亮度在 PA 高 30.9、在 AP 高 14.4（0 到 255 的刻度），同一種拍攝方式內也有差，所以不是 PA／AP 比例不同造成的
  - 比較健康：No Finding 佔 66.5%，其餘影像為 53.8%
  - 比較少進官方 test：10.8% 在 test，其餘影像為 22.9%
- 合理的推測是這群影像來自不同的輸出或後處理流程（未查證）。模型有可能學到「這種偏亮的影像比較常是正常」
- **影響範圍很小**：只佔全部影像的 0.46%，test 中只有 56 張，對整體指標的影響有限
- 處理方式：不排除、不特別處理（規格沒有相關規則，test 也不可更動）；列為已知的資料特性，M6 寫限制段落時引用本節

## 3. 排除名單的來源

NIH 官方 `LOG_CHESTXRAY.pdf` 公告了 10 組配對，共 17 張影像，其中 12 張在官方 train_val。只照官方公告處理的話會排除這 12 張。
M1 另外自行掃描全部影像（規格第 4.2.1 節），最終排除 35 張：

| 來源 | 排除原因 | 張數 |
|---|---|---|
| 官方公告的配對（像素完全相同） | duplicate_of_test | 4 |
| 官方公告的配對（像素完全相同） | duplicate_within_train_val | 8 |
| 自行掃描另外找到（像素完全相同） | duplicate_within_train_val | 22 |
| 感知雜湊可疑名單＋人工看圖確認 | near_duplicate_of_test | 1 |
| **合計** | | **35** |

- 官方公告中位於 train_val 的 12 張，未被排除的有 0 張
- 以 `near_duplicate_of_test` 排除、但不在人工確認清單（`CONFIRMED_NEAR_DUPLICATE_PAIRS`）內的有 0 張
- 排除的全部是官方 train_val 的影像；官方 test 的 25,596 張原樣保留

| 影像 | 病人 | 標籤 | 排除原因 | 來源 |
|---|---|---|---|---|
| 00005403_024.png | 5403 | Infiltration | duplicate_within_train_val | 官方公告的配對（像素完全相同） |
| 00005537_011.png | 5537 | No Finding | duplicate_within_train_val | 官方公告的配對（像素完全相同） |
| 00007108_008.png | 7108 | No Finding | duplicate_within_train_val | 官方公告的配對（像素完全相同） |
| 00008182_001.png | 8182 | Atelectasis | duplicate_within_train_val | 官方公告的配對（像素完全相同） |
| 00011504_008.png | 11504 | No Finding | duplicate_within_train_val | 官方公告的配對（像素完全相同） |
| 00012388_000.png | 12388 | No Finding | duplicate_of_test | 官方公告的配對（像素完全相同） |
| 00012388_001.png | 12388 | No Finding | duplicate_of_test | 官方公告的配對（像素完全相同） |
| 00027864_000.png | 27864 | No Finding | duplicate_of_test | 官方公告的配對（像素完全相同） |
| 00027864_001.png | 27864 | No Finding | duplicate_within_train_val | 官方公告的配對（像素完全相同） |
| 00027864_002.png | 27864 | No Finding | duplicate_within_train_val | 官方公告的配對（像素完全相同） |
| 00027864_003.png | 27864 | No Finding | duplicate_of_test | 官方公告的配對（像素完全相同） |
| 00028591_002.png | 28591 | No Finding | duplicate_within_train_val | 官方公告的配對（像素完全相同） |
| 00000820_015.png | 820 | Infiltration | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00000820_016.png | 820 | Infiltration | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00001989_004.png | 1989 | Fibrosis | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00001989_005.png | 1989 | Atelectasis|Infiltration|Pneumothorax | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00002658_001.png | 2658 | No Finding | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00002658_002.png | 2658 | No Finding | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00007633_003.png | 7633 | No Finding | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00007633_004.png | 7633 | Infiltration | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00008273_004.png | 8273 | No Finding | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00008273_005.png | 8273 | No Finding | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00009325_002.png | 9325 | Atelectasis|Pneumothorax | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00009325_005.png | 9325 | Pneumothorax | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00011723_001.png | 11723 | Atelectasis|Infiltration | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00011723_002.png | 11723 | Atelectasis|Infiltration | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00016518_001.png | 16518 | No Finding | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00016518_002.png | 16518 | No Finding | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00016940_003.png | 16940 | No Finding | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00016940_004.png | 16940 | No Finding | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00019479_008.png | 19479 | Nodule | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00019479_010.png | 19479 | Nodule | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00019535_003.png | 19535 | Nodule | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00019535_005.png | 19535 | Atelectasis|Infiltration | duplicate_within_train_val | 自行掃描另外找到（像素完全相同） |
| 00027864_004.png | 27864 | No Finding | near_duplicate_of_test | 感知雜湊可疑名單＋人工看圖確認 |
