# M1 Step 2：影像完整性

## 1. 壓縮檔 MD5（對照官方 FAQ）

| 檔案 | 大小（GB） | 結果 |
|---|---|---|
| images_001.tar.gz | 2.01 | 相符 |
| images_002.tar.gz | 3.95 | 相符 |
| images_003.tar.gz | 3.93 | 相符 |
| images_004.tar.gz | 3.84 | 相符 |
| images_005.tar.gz | 3.94 | 相符 |
| images_006.tar.gz | 3.99 | 相符 |
| images_007.tar.gz | 4.02 | 相符 |
| images_008.tar.gz | 4.02 | 相符 |
| images_009.tar.gz | 4.11 | 相符 |
| images_010.tar.gz | 4.18 | 相符 |
| images_011.tar.gz | 4.19 | 相符 |
| images_012.tar.gz | 2.91 | 相符 |

## 2. 影像張數與可讀性

- 中繼資料列出 112,120 張，磁碟上找到 112,120 張
- 中繼資料有、磁碟沒有：0 張
- 磁碟有、中繼資料沒有：0 張
- 打不開的影像：0 張

| 色彩模式 | 寬 | 高 | 張數 |
|---|---|---|---|
| L | 1024 | 1024 | 111,601 |
| RGBA | 1024 | 1024 | 519 |

## 3. 像素完全相同的影像

判定方式：解碼成 8 位元灰階後逐像素相同。處理規則在掃描前就寫進規格第 4.2.1 節：
群組橫跨 train_val 與 test 時排除 train_val 那一邊；全部在 train_val 內時整群排除；
test 一律不動。

- 自己掃描找到 25 群，共 51 張
- 官方公告的 8 群中，掃描結果涵蓋 8 群

| 群 | 影像 | 官方切分 | 病人 | 標籤 | 群的類型 | 處置 |
|---|---|---|---|---|---|---|
| 1 | 00000820_015.png | train_val | 820 | Infiltration | train_val 內部 | 排除 |
| 1 | 00000820_016.png | train_val | 820 | Infiltration | train_val 內部 | 排除 |
| 2 | 00001989_004.png | train_val | 1989 | Fibrosis | train_val 內部、標籤衝突 | 排除 |
| 2 | 00001989_005.png | train_val | 1989 | Atelectasis|Infiltration|Pneumothorax | train_val 內部、標籤衝突 | 排除 |
| 3 | 00002658_001.png | train_val | 2658 | No Finding | train_val 內部 | 排除 |
| 3 | 00002658_002.png | train_val | 2658 | No Finding | train_val 內部 | 排除 |
| 4 | 00005403_024.png | train_val | 5403 | Infiltration | train_val 內部、標籤衝突 | 排除 |
| 4 | 00005537_011.png | train_val | 5537 | No Finding | train_val 內部、標籤衝突 | 排除 |
| 5 | 00005681_024.png | test | 5681 | Emphysema|Infiltration | 跨 train_val 與 test、標籤衝突 | 保留（test 不動） |
| 5 | 00027864_003.png | train_val | 27864 | No Finding | 跨 train_val 與 test、標籤衝突 | 排除 |
| 6 | 00007108_008.png | train_val | 7108 | No Finding | train_val 內部 | 排除 |
| 6 | 00027864_002.png | train_val | 27864 | No Finding | train_val 內部 | 排除 |
| 7 | 00007633_003.png | train_val | 7633 | No Finding | train_val 內部、標籤衝突 | 排除 |
| 7 | 00007633_004.png | train_val | 7633 | Infiltration | train_val 內部、標籤衝突 | 排除 |
| 8 | 00007670_030.png | test | 7670 | Pleural_Thickening|Pneumothorax | test 內部、標籤衝突 | 保留（test 不動） |
| 8 | 00007670_031.png | test | 7670 | Effusion|Infiltration|Pneumothorax | test 內部、標籤衝突 | 保留（test 不動） |
| 9 | 00008182_001.png | train_val | 8182 | Atelectasis | train_val 內部、標籤衝突 | 排除 |
| 9 | 00011504_008.png | train_val | 11504 | No Finding | train_val 內部、標籤衝突 | 排除 |
| 10 | 00008273_004.png | train_val | 8273 | No Finding | train_val 內部 | 排除 |
| 10 | 00008273_005.png | train_val | 8273 | No Finding | train_val 內部 | 排除 |
| 11 | 00008727_014.png | test | 8727 | Infiltration | test 內部、標籤衝突 | 保留（test 不動） |
| 11 | 00008727_015.png | test | 8727 | No Finding | test 內部、標籤衝突 | 保留（test 不動） |
| 12 | 00009325_002.png | train_val | 9325 | Atelectasis|Pneumothorax | train_val 內部、標籤衝突 | 排除 |
| 12 | 00009325_005.png | train_val | 9325 | Pneumothorax | train_val 內部、標籤衝突 | 排除 |
| 13 | 00011702_060.png | test | 11702 | Effusion | test 內部 | 保留（test 不動） |
| 13 | 00011702_061.png | test | 11702 | Effusion | test 內部 | 保留（test 不動） |
| 14 | 00011723_001.png | train_val | 11723 | Atelectasis|Infiltration | train_val 內部 | 排除 |
| 14 | 00011723_002.png | train_val | 11723 | Atelectasis|Infiltration | train_val 內部 | 排除 |
| 15 | 00012388_000.png | train_val | 12388 | No Finding | 跨 train_val 與 test | 排除 |
| 15 | 00012388_001.png | train_val | 12388 | No Finding | 跨 train_val 與 test | 排除 |
| 15 | 00017214_007.png | test | 17214 | No Finding | 跨 train_val 與 test | 保留（test 不動） |
| 16 | 00015262_001.png | test | 15262 | Atelectasis | test 內部 | 保留（test 不動） |
| 16 | 00015262_003.png | test | 15262 | Atelectasis | test 內部 | 保留（test 不動） |
| 17 | 00016518_001.png | train_val | 16518 | No Finding | train_val 內部 | 排除 |
| 17 | 00016518_002.png | train_val | 16518 | No Finding | train_val 內部 | 排除 |
| 18 | 00016568_052.png | test | 16568 | Nodule | test 內部、標籤衝突 | 保留（test 不動） |
| 18 | 00016568_053.png | test | 16568 | Edema|Nodule | test 內部、標籤衝突 | 保留（test 不動） |
| 19 | 00016940_003.png | train_val | 16940 | No Finding | train_val 內部 | 排除 |
| 19 | 00016940_004.png | train_val | 16940 | No Finding | train_val 內部 | 排除 |
| 20 | 00018721_003.png | test | 18721 | No Finding | test 內部、標籤衝突 | 保留（test 不動） |
| 20 | 00018721_005.png | test | 18721 | Infiltration|Nodule | test 內部、標籤衝突 | 保留（test 不動） |
| 21 | 00019479_008.png | train_val | 19479 | Nodule | train_val 內部 | 排除 |
| 21 | 00019479_010.png | train_val | 19479 | Nodule | train_val 內部 | 排除 |
| 22 | 00019535_003.png | train_val | 19535 | Nodule | train_val 內部、標籤衝突 | 排除 |
| 22 | 00019535_005.png | train_val | 19535 | Atelectasis|Infiltration | train_val 內部、標籤衝突 | 排除 |
| 23 | 00027864_000.png | train_val | 27864 | No Finding | 跨 train_val 與 test | 排除 |
| 23 | 00028328_000.png | test | 28328 | No Finding | 跨 train_val 與 test | 保留（test 不動） |
| 24 | 00027864_001.png | train_val | 27864 | No Finding | train_val 內部 | 排除 |
| 24 | 00028591_002.png | train_val | 28591 | No Finding | train_val 內部 | 排除 |
| 25 | 00029402_001.png | test | 29402 | No Finding | test 內部 | 保留（test 不動） |
| 25 | 00029476_004.png | test | 29476 | No Finding | test 內部 | 保留（test 不動） |

- 跨 train_val 與 test：3 群
- train_val 內部：15 群
- test 內部：7 群
- 同一張圖掛在不同病人名下：8 群
- 同一張圖但標籤不同（標籤衝突）：11 群

### 3.1 留在 test 的重複影像（只列出，不處理）

下列影像屬於重複群但位於官方 test，依規則不排除、不改標籤。
「test 內部」的群代表同一張圖在 test 中被計分不只一次；
「標籤衝突」代表同一張圖在不同檔名下掛著不同標籤，其中至少一邊的標籤有誤。

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

## 4. 感知雜湊的可疑名單（只列出，不自動排除）

做法：每張圖縮成 64×64 灰階後做 DCT，取 16×16 的低頻係數與中位數比大小，得到 256 個位元。
兩張圖相差 30 個位元以內就列為可疑（門檻是經驗值，只決定名單長短）。
「像素相關」是兩張圖縮成 256×256 後的像素相關係數，越接近 1 越像，供人工判斷時參考。
像素完全相同的配對已在第 3 節處理，這裡不重複列。

這份名單**不會**被切分腳本讀取，名單上的影像都還留在原本的組別。
感知雜湊相近不等於同一張圖：同一位病人短時間內連拍的影像本來就很像。
需要人看過才能判斷，要不要處理由使用者決定。

- 可疑配對共 60 對，完整名單在 `reports/02_near_duplicates.csv`

| 類型 | 配對數 | 其中標籤不同 | 最小距離 |
|---|---|---|---|
| 跨 train_val 與 test | 1 | 0 | 20 |
| train_val 內、不同病人 | 1 | 0 | 30 |
| train_val 內、同一病人 | 33 | 17 | 16 |
| test 內、不同病人 | 2 | 1 | 14 |
| test 內、同一病人 | 23 | 15 | 4 |

各距離的配對數：

| 距離 | 配對數 |
|---|---|
| 4 | 1 |
| 14 | 1 |
| 16 | 1 |
| 18 | 1 |
| 20 | 2 |
| 22 | 1 |
| 24 | 5 |
| 26 | 7 |
| 28 | 20 |
| 30 | 21 |

### 跨 train_val 與 test（1 對）

| 距離 | 像素相關 | 影像 A | 標籤 A | 影像 B | 標籤 B |
|---|---|---|---|---|---|
| 20 | 0.9861 | 00027864_004.png | No Finding | 00027927_032.png | No Finding |

### train_val 內、不同病人（1 對）

| 距離 | 像素相關 | 影像 A | 標籤 A | 影像 B | 標籤 B |
|---|---|---|---|---|---|
| 30 | 0.9207 | 00002876_000.png | No Finding | 00023467_000.png | No Finding |

### train_val 內、同一病人（33 對）

| 距離 | 像素相關 | 影像 A | 標籤 A | 影像 B | 標籤 B |
|---|---|---|---|---|---|
| 16 | 0.9862 | 00019528_009.png | No Finding | 00019528_012.png | No Finding |
| 20 | 0.9478 | 00018312_007.png | No Finding | 00018312_008.png | No Finding |
| 22 | 0.9775 | 00018006_022.png | Effusion|Infiltration | 00018006_023.png | Effusion|Mass |
| 24 | 0.9417 | 00008027_000.png | Infiltration | 00008027_003.png | Nodule |
| 24 | 0.8850 | 00012874_021.png | No Finding | 00012874_029.png | Infiltration |
| 24 | 0.9755 | 00025110_000.png | Infiltration | 00025110_003.png | No Finding |
| 24 | 0.9491 | 00026742_000.png | Edema|Pleural_Thickening | 00026742_001.png | Edema |
| 26 | 0.9788 | 00013620_013.png | Atelectasis | 00013620_018.png | Atelectasis |
| 26 | 0.9801 | 00017541_006.png | Atelectasis | 00017541_007.png | Atelectasis|Effusion|Infiltration|Nodule |
| 26 | 0.9837 | 00018186_008.png | No Finding | 00018186_009.png | No Finding |
| 26 | 0.9793 | 00025110_002.png | No Finding | 00025110_004.png | Infiltration |
| 28 | 0.9729 | 00005274_005.png | No Finding | 00005274_006.png | No Finding |
| 28 | 0.9440 | 00006647_001.png | Nodule | 00006647_002.png | No Finding |
| 28 | 0.9591 | 00006985_006.png | No Finding | 00006985_010.png | No Finding |
| 28 | 0.9250 | 00007450_004.png | No Finding | 00007450_005.png | Atelectasis |
| 28 | 0.9712 | 00014546_005.png | Atelectasis|Emphysema|Infiltration | 00014546_010.png | No Finding |
| 28 | 0.9661 | 00018043_004.png | No Finding | 00018043_005.png | No Finding |
| 28 | 0.9745 | 00022301_008.png | Infiltration | 00022301_011.png | Infiltration |
| 28 | 0.9650 | 00022892_001.png | No Finding | 00022892_002.png | No Finding |
| 28 | 0.9820 | 00028897_015.png | Effusion | 00028897_018.png | Effusion|Pleural_Thickening |
| 30 | 0.9690 | 00002635_001.png | Infiltration | 00002635_002.png | No Finding |
| 30 | 0.9445 | 00003585_000.png | Atelectasis|Nodule|Pneumonia | 00003585_001.png | No Finding |
| 30 | 0.9771 | 00007526_006.png | No Finding | 00007526_011.png | No Finding |
| 30 | 0.9771 | 00009867_004.png | No Finding | 00009867_008.png | No Finding |
| 30 | 0.9087 | 00009962_000.png | No Finding | 00009962_002.png | No Finding |
| 30 | 0.9622 | 00012874_019.png | No Finding | 00012874_022.png | No Finding |
| 30 | 0.9671 | 00016052_001.png | No Finding | 00016052_003.png | No Finding |
| 30 | 0.9583 | 00018037_012.png | No Finding | 00018037_014.png | No Finding |
| 30 | 0.9456 | 00025181_004.png | No Finding | 00025181_007.png | Nodule |
| 30 | 0.9013 | 00025192_002.png | Infiltration | 00025192_003.png | Infiltration |
| 30 | 0.9391 | 00025192_003.png | Infiltration | 00025192_005.png | No Finding |
| 30 | 0.9674 | 00026793_005.png | No Finding | 00026793_008.png | Pneumothorax |
| 30 | 0.9680 | 00029900_002.png | No Finding | 00029900_003.png | Infiltration |

### test 內、不同病人（2 對）

| 距離 | 像素相關 | 影像 A | 標籤 A | 影像 B | 標籤 B |
|---|---|---|---|---|---|
| 14 | 0.9904 | 00029476_001.png | No Finding | 00029707_000.png | No Finding |
| 18 | 0.9851 | 00029476_002.png | No Finding | 00029747_002.png | Effusion|Infiltration|Pneumonia |

### test 內、同一病人（23 對）

| 距離 | 像素相關 | 影像 A | 標籤 A | 影像 B | 標籤 B |
|---|---|---|---|---|---|
| 4 | 0.9995 | 00011402_004.png | No Finding | 00011402_005.png | No Finding |
| 24 | 0.9879 | 00019373_003.png | Emphysema|Mass|Pneumothorax | 00019373_004.png | Mass|Nodule|Pneumothorax |
| 26 | 0.9757 | 00011460_026.png | Pneumothorax | 00011460_028.png | Pneumothorax |
| 26 | 0.9740 | 00020318_025.png | No Finding | 00020318_026.png | No Finding |
| 26 | 0.9676 | 00028861_008.png | Pneumothorax | 00028861_010.png | Pneumothorax |
| 28 | 0.9560 | 00009349_019.png | Atelectasis|Consolidation|Infiltration|Pneumothorax | 00009349_020.png | Atelectasis|Consolidation|Pneumothorax |
| 28 | 0.9807 | 00012364_020.png | No Finding | 00012364_023.png | No Finding |
| 28 | 0.9818 | 00013670_002.png | No Finding | 00013670_006.png | Edema|Infiltration |
| 28 | 0.9881 | 00014996_006.png | No Finding | 00014996_009.png | No Finding |
| 28 | 0.9708 | 00018496_001.png | Effusion|Pneumothorax | 00018496_002.png | Pneumothorax |
| 28 | 0.9623 | 00021024_011.png | No Finding | 00021024_012.png | Fibrosis |
| 28 | 0.9785 | 00021024_019.png | Effusion|Nodule | 00021024_020.png | No Finding |
| 28 | 0.9778 | 00023065_024.png | Effusion | 00023065_029.png | Pneumothorax |
| 28 | 0.9577 | 00023075_015.png | Emphysema|Infiltration | 00023075_016.png | Infiltration |
| 28 | 0.9788 | 00028876_026.png | Mass|Pneumothorax | 00028876_028.png | Pneumothorax |
| 28 | 0.9682 | 00030637_020.png | No Finding | 00030637_021.png | No Finding |
| 30 | 0.9705 | 00002350_002.png | No Finding | 00002350_003.png | Atelectasis |
| 30 | 0.9866 | 00015794_000.png | Cardiomegaly|Nodule | 00015794_001.png | Infiltration|Nodule |
| 30 | 0.9689 | 00016971_002.png | Mass | 00016971_004.png | Mass |
| 30 | 0.9729 | 00026412_046.png | Consolidation|Emphysema|Pneumothorax | 00026412_048.png | Consolidation|Emphysema |
| 30 | 0.9620 | 00027542_002.png | Pneumothorax | 00027542_007.png | Effusion|Pneumothorax |
| 30 | 0.9780 | 00028876_060.png | Mass|Nodule | 00028876_061.png | Fibrosis|Mass|Nodule |
| 30 | 0.9772 | 00029259_009.png | Infiltration|Pneumothorax | 00029259_012.png | No Finding |
