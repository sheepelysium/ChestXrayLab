# M1 Step 1：資料盤點

資料來源：NIH 官方 Box 資料夾的 `Data_Entry_2017_v2020.csv`、`train_val_list.txt`、
`test_list.txt`、`BBox_List_2017.csv`，以及 NEATX 胸管標註。本步驟不讀影像。

## 1. 總數與官方切分

| 範圍 | 影像 | 病人 |
|---|---|---|
| 全部 | 112,120 | 30,805 |
| 官方 train_val | 86,524 | 28,008 |
| 官方 test | 25,596 | 2,797 |

- 官方 train_val 與 test 共用的病人：**0**
- 官方 train_val 與 test 共用的影像：**0**

## 2. 各標籤張數與比例

| 標籤 | 全部 | train_val | train_val 比例 | test | test 比例 | 比例倍數 |
|---|---|---|---|---|---|---|
| Atelectasis | 11,559 | 8,280 | 9.6% | 3,279 | 12.8% | 1.34 |
| Cardiomegaly | 2,776 | 1,707 | 2.0% | 1,069 | 4.2% | 2.12 |
| Consolidation | 4,667 | 2,852 | 3.3% | 1,815 | 7.1% | 2.15 |
| Edema | 2,303 | 1,378 | 1.6% | 925 | 3.6% | 2.27 |
| Effusion | 13,317 | 8,659 | 10.0% | 4,658 | 18.2% | 1.82 |
| Emphysema | 2,516 | 1,423 | 1.6% | 1,093 | 4.3% | 2.60 |
| Fibrosis | 1,686 | 1,251 | 1.4% | 435 | 1.7% | 1.18 |
| Hernia | 227 | 141 | 0.2% | 86 | 0.3% | 2.06 |
| Infiltration | 19,894 | 13,782 | 15.9% | 6,112 | 23.9% | 1.50 |
| Mass | 5,782 | 4,034 | 4.7% | 1,748 | 6.8% | 1.46 |
| Nodule | 6,331 | 4,708 | 5.4% | 1,623 | 6.3% | 1.17 |
| Pleural_Thickening | 3,385 | 2,242 | 2.6% | 1,143 | 4.5% | 1.72 |
| Pneumonia | 1,431 | 876 | 1.0% | 555 | 2.2% | 2.14 |
| Pneumothorax | 5,302 | 2,637 | 3.0% | 2,665 | 10.4% | 3.42 |
| no_finding | 60,361 | 50,500 | 58.4% | 9,861 | 38.5% | 0.66 |

「比例倍數」是 test 的陽性比例除以 train_val 的陽性比例。
倍數離 1 越遠，代表官方 test 與 train_val 的組成差越多。

- 一張影像同時有 2 個以上異常標籤：20,796 張（18.5%），最多 9 個

## 3. 拍攝方式（View Position）

| 範圍 | 拍攝方式 | 影像 | 比例 |
|---|---|---|---|
| 官方 train_val | AP | 30,310 | 35.0% |
| 官方 train_val | PA | 56,214 | 65.0% |
| 官方 test | AP | 14,500 | 56.6% |
| 官方 test | PA | 11,096 | 43.4% |

各標籤在 PA 與 AP 影像中的陽性比例（全部影像）：

| 標籤 | PA 中的比例 | AP 中的比例 |
|---|---|---|
| Atelectasis | 8.5% | 13.0% |
| Cardiomegaly | 2.3% | 2.7% |
| Consolidation | 2.3% | 7.0% |
| Edema | 0.4% | 4.5% |
| Effusion | 9.8% | 15.0% |
| Emphysema | 2.2% | 2.3% |
| Fibrosis | 2.1% | 0.6% |
| Hernia | 0.3% | 0.1% |
| Infiltration | 13.9% | 23.5% |
| Mass | 5.3% | 4.9% |
| Nodule | 6.2% | 4.8% |
| Pleural_Thickening | 3.6% | 2.2% |
| Pneumonia | 0.9% | 1.8% |
| Pneumothorax | 5.1% | 4.2% |

## 4. 每位病人的影像數

- 中位數 1 張，平均 3.6 張，最多 184 張
- 只有 1 張的病人：17,503 位；超過 50 張的病人：151 位，共 10,812 張
- 年齡範圍 0 到 95 歲

## 5. 框標註

- 框 984 個，分布在 880 張影像
- 落在官方 test 的框：984 個；落在 train_val：0 個

| 類別 | 框數 |
|---|---|
| Atelectasis | 180 |
| Effusion | 153 |
| Cardiomegaly | 146 |
| Infiltration | 123 |
| Pneumonia | 120 |
| Pneumothorax | 98 |
| Mass | 85 |
| Nodule | 79 |

- 框的類別在影像標籤中不是陽性的框：0 個

## 6. 胸管標註（NEATX）

- 標註 3,543 張，其中 NIH 標籤為氣胸的 3,543 張
- 標註者為兩位非醫師，授權 CC BY-NC-SA，只用於分群報告

| 範圍 | NIH 氣胸張數 | 有胸管標註 | 有胸管 | 無胸管 |
|---|---|---|---|---|
| train_val | 2,637 | 1,783 | 616 | 1,167 |
| test | 2,665 | 1,760 | 1,021 | 739 |

## 7. 官方公告的重複影像

NIH 在 `LOG_CHESTXRAY.pdf`（2026-10-09）公告了 10 組像素完全相同的影像配對。
合併成群組後如下（同一群內的影像內容相同）：

| 群 | 影像 | 官方切分 | 病人 | 標籤 |
|---|---|---|---|---|
| 1 | 00005403_024.png | train_val | 5403 | Infiltration |
| 1 | 00005537_011.png | train_val | 5537 | No Finding |
| 2 | 00005681_024.png | test | 5681 | Emphysema|Infiltration |
| 2 | 00027864_003.png | train_val | 27864 | No Finding |
| 3 | 00007108_008.png | train_val | 7108 | No Finding |
| 3 | 00027864_002.png | train_val | 27864 | No Finding |
| 4 | 00008182_001.png | train_val | 8182 | Atelectasis |
| 4 | 00011504_008.png | train_val | 11504 | No Finding |
| 5 | 00012388_000.png | train_val | 12388 | No Finding |
| 5 | 00012388_001.png | train_val | 12388 | No Finding |
| 5 | 00017214_007.png | test | 17214 | No Finding |
| 6 | 00027864_000.png | train_val | 27864 | No Finding |
| 6 | 00028328_000.png | test | 28328 | No Finding |
| 7 | 00027864_001.png | train_val | 27864 | No Finding |
| 7 | 00028591_002.png | train_val | 28591 | No Finding |
| 8 | 00029402_001.png | test | 29402 | No Finding |
| 8 | 00029476_004.png | test | 29476 | No Finding |

- 橫跨 train_val 與 test 的群：**3** 群

這與「官方切分沒有洩漏」的假設不符，處理方式待使用者決定。

## 8. 與規格的核對結果

規格第 4 節的總數、切分張數、各標籤張數全部與官方檔案相符。
