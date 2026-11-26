# M1 Step 3：切分

狀態：已鎖定

SHA-256：`aa84f99e60465f3c38b4d419ddcabd0bb362ea3b170758ff72985e93cb59cdd7`

- test：NIH 官方 `test_list.txt`，原樣使用
- val：官方 train_val 的病人抽 10%，種子 42
- 重複影像來源：Step 2 的像素雜湊掃描

## 1. 各組大小

| 組 | 病人 | 影像 | PA | AP |
|---|---|---|---|---|
| train | 25,206 | 77,706 | 50,610 | 27,096 |
| val | 2,801 | 8,783 | 5,594 | 3,189 |
| test | 2,797 | 25,596 | 11,096 | 14,500 |
| excluded | 19 | 35 | 10 | 25 |

## 2. 各標籤陽性張數

| 標籤 | train | train 比例 | val | val 比例 | test | test 比例 |
|---|---|---|---|---|---|---|
| Atelectasis | 7,354 | 9.5% | 920 | 10.5% | 3,279 | 12.8% |
| Cardiomegaly | 1,528 | 2.0% | 179 | 2.0% | 1,069 | 4.2% |
| Consolidation | 2,546 | 3.3% | 306 | 3.5% | 1,815 | 7.1% |
| Edema | 1,243 | 1.6% | 135 | 1.5% | 925 | 3.6% |
| Effusion | 7,789 | 10.0% | 870 | 9.9% | 4,658 | 18.2% |
| Emphysema | 1,277 | 1.6% | 146 | 1.7% | 1,093 | 4.3% |
| Fibrosis | 1,124 | 1.4% | 126 | 1.4% | 435 | 1.7% |
| Hernia | 127 | 0.2% | 14 | 0.2% | 86 | 0.3% |
| Infiltration | 12,373 | 15.9% | 1,401 | 16.0% | 6,112 | 23.9% |
| Mass | 3,652 | 4.7% | 382 | 4.3% | 1,748 | 6.8% |
| Nodule | 4,244 | 5.5% | 461 | 5.2% | 1,623 | 6.3% |
| Pleural_Thickening | 2,034 | 2.6% | 208 | 2.4% | 1,143 | 4.5% |
| Pneumonia | 779 | 1.0% | 97 | 1.1% | 555 | 2.2% |
| Pneumothorax | 2,373 | 3.1% | 261 | 3.0% | 2,665 | 10.4% |
| no_finding | 45,369 | 58.4% | 5,111 | 58.2% | 9,861 | 38.5% |

test 的陽性比例明顯高於 train 與 val（官方切分不是隨機抽的）。因此：

- AUPRC 受盛行率影響，**val 與 test 的 AUPRC 不可直接比較**；precision 與 F1 也一樣
- 需要閾值的指標在 val 上以固定 sensitivity 決定閾值，不用最大化 F1（規格第 6 節）

## 3. 排除的影像

| 影像 | 病人 | 標籤 | 原因 |
|---|---|---|---|
| 00000820_015.png | 820 | Infiltration | duplicate_within_train_val |
| 00000820_016.png | 820 | Infiltration | duplicate_within_train_val |
| 00001989_004.png | 1989 | Fibrosis | duplicate_within_train_val |
| 00001989_005.png | 1989 | Atelectasis|Infiltration|Pneumothorax | duplicate_within_train_val |
| 00002658_001.png | 2658 | No Finding | duplicate_within_train_val |
| 00002658_002.png | 2658 | No Finding | duplicate_within_train_val |
| 00005403_024.png | 5403 | Infiltration | duplicate_within_train_val |
| 00005537_011.png | 5537 | No Finding | duplicate_within_train_val |
| 00007108_008.png | 7108 | No Finding | duplicate_within_train_val |
| 00007633_003.png | 7633 | No Finding | duplicate_within_train_val |
| 00007633_004.png | 7633 | Infiltration | duplicate_within_train_val |
| 00008182_001.png | 8182 | Atelectasis | duplicate_within_train_val |
| 00008273_004.png | 8273 | No Finding | duplicate_within_train_val |
| 00008273_005.png | 8273 | No Finding | duplicate_within_train_val |
| 00009325_002.png | 9325 | Atelectasis|Pneumothorax | duplicate_within_train_val |
| 00009325_005.png | 9325 | Pneumothorax | duplicate_within_train_val |
| 00011504_008.png | 11504 | No Finding | duplicate_within_train_val |
| 00011723_001.png | 11723 | Atelectasis|Infiltration | duplicate_within_train_val |
| 00011723_002.png | 11723 | Atelectasis|Infiltration | duplicate_within_train_val |
| 00012388_000.png | 12388 | No Finding | duplicate_of_test |
| 00012388_001.png | 12388 | No Finding | duplicate_of_test |
| 00016518_001.png | 16518 | No Finding | duplicate_within_train_val |
| 00016518_002.png | 16518 | No Finding | duplicate_within_train_val |
| 00016940_003.png | 16940 | No Finding | duplicate_within_train_val |
| 00016940_004.png | 16940 | No Finding | duplicate_within_train_val |
| 00019479_008.png | 19479 | Nodule | duplicate_within_train_val |
| 00019479_010.png | 19479 | Nodule | duplicate_within_train_val |
| 00019535_003.png | 19535 | Nodule | duplicate_within_train_val |
| 00019535_005.png | 19535 | Atelectasis|Infiltration | duplicate_within_train_val |
| 00027864_000.png | 27864 | No Finding | duplicate_of_test |
| 00027864_001.png | 27864 | No Finding | duplicate_within_train_val |
| 00027864_002.png | 27864 | No Finding | duplicate_within_train_val |
| 00027864_003.png | 27864 | No Finding | duplicate_of_test |
| 00027864_004.png | 27864 | No Finding | near_duplicate_of_test |
| 00028591_002.png | 28591 | No Finding | duplicate_within_train_val |

- `duplicate_of_test`：與官方 test 的某張影像像素完全相同
- `duplicate_within_train_val`：train_val 內部互相重複，整群排除
- `near_duplicate_of_test`：與官方 test 的某張影像是同一次拍攝（影像處理不同，像素不完全相同），經人工看圖並由使用者確認後排除

### 3.1 留在 test 的重複影像（只列出，不處理）

規格第 4.2.1 節：test 一律不動。下列影像屬於重複群但位於官方 test，不排除、不改標籤。

| 群 | 影像 | 病人 | 標籤 | 群的類型 | 標籤衝突 |
|---|---|---|---|---|---|
| 5 | 00005681_024.png | 5681 | Emphysema|Infiltration | 跨 train_val 與 test | 是 |
| 8 | 00007670_030.png | 7670 | Pleural_Thickening|Pneumothorax | test 內部 | 是 |
| 8 | 00007670_031.png | 7670 | Effusion|Infiltration|Pneumothorax | test 內部 | 是 |
| 11 | 00008727_014.png | 8727 | Infiltration | test 內部 | 是 |
| 11 | 00008727_015.png | 8727 | No Finding | test 內部 | 是 |
| 13 | 00011702_060.png | 11702 | Effusion | test 內部 | 否 |
| 13 | 00011702_061.png | 11702 | Effusion | test 內部 | 否 |
| 15 | 00017214_007.png | 17214 | No Finding | 跨 train_val 與 test | 否 |
| 16 | 00015262_001.png | 15262 | Atelectasis | test 內部 | 否 |
| 16 | 00015262_003.png | 15262 | Atelectasis | test 內部 | 否 |
| 18 | 00016568_052.png | 16568 | Nodule | test 內部 | 是 |
| 18 | 00016568_053.png | 16568 | Edema|Nodule | test 內部 | 是 |
| 20 | 00018721_003.png | 18721 | No Finding | test 內部 | 是 |
| 20 | 00018721_005.png | 18721 | Infiltration|Nodule | test 內部 | 是 |
| 23 | 00028328_000.png | 28328 | No Finding | 跨 train_val 與 test | 否 |
| 25 | 00029402_001.png | 29402 | No Finding | test 內部 | 否 |
| 25 | 00029476_004.png | 29476 | No Finding | test 內部 | 否 |

- 「test 內部」：同一張圖在 test 中出現不只一次，計分時會被算不只一次
- 「標籤衝突」：同一張圖在群內不同檔名下掛著不同標籤（含已排除的那一邊）

## 4. 氣胸與胸管標註

| 組 | 氣胸張數 | 有胸管標註 | 有胸管 | 無胸管 |
|---|---|---|---|---|
| train | 2,373 | 1,618 | 547 | 1,071 |
| val | 261 | 163 | 69 | 94 |
| test | 2,665 | 1,760 | 1,021 | 739 |
