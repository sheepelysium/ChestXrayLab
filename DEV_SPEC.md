# ChestXrayLab 開發規格 v1.0

> 狀態：2026-11-26 使用者確認。動手前先讀完，以本檔為準。
> 標「待核對」的數字來自第三方頁面或論文轉述，M1 資料盤點時要用實際檔案逐項核對；對不上就停下回報。

## 1. 專案定位

求職作品集＋學習用專案：在 NIH ChestX-ray14 上微調影像模型，做 14 類胸部 X 光多標籤分類，並比較微調方式、預訓練來源，最後檢查模型有沒有走捷徑。

- 非醫療用途，README 與報告都不可寫成診斷工具
- 對應職缺要求「CV + 微調模型」；評測方法沿用 DermCaseLab M1（按病人切分、鎖定 test、信賴區間、捷徑稽核）
- 不做物件偵測與分割
- 硬體：單張 RTX 5080（16 GB），所有實驗以本機跑得完為準
- 兩台機器（2026-11-26 使用者確認）：公司與家裡各有一張 RTX 5080。**家裡那台是正式機**，所有訓練都在家裡跑，寫進報告的數字與 `checkpoints/` 都出自這台；公司那台只用來寫程式與跑測試，不長期保留影像。兩台只靠 git 同步，資料與權重不跟著走
- Repo：https://github.com/sheepelysium/ChestXrayLab（單人專案，直接 commit 到 `main`）

## 2. 學習目標

### 2.1 五個能力目標

| # | 學什麼 | 對應里程碑 |
|---|---|---|
| 1 | 影像訓練流程：資料讀取、增強、混合精度、早停、存檔 | M2 |
| 2 | 微調策略比較：只訓練分類頭、全部微調、LoRA（同一個骨幹） | M4 |
| 3 | 預訓練來源的影響：一般影像預訓練對上 X 光專用預訓練 | M5 |
| 4 | 多標籤與類別不平衡：loss 與指標的選擇 | M3 |
| 5 | 模型在看哪裡、有沒有走捷徑 | M6 |

### 2.2 七題驗收

主線完成時，使用者要能在有 AI 輔助的情況下把下面 7 題解釋清楚。每個里程碑結束時考相關的題目，M6 結束時七題全部再考一次。

| # | 題目 | 第一次考 |
|---|---|---|
| Q1 | 多標籤為什麼用 sigmoid＋BCE，而不是 softmax＋CE？ | M2 |
| Q2 | 混合精度為什麼需要 GradScaler？ | M2 |
| Q3 | 全部微調時，為什麼骨幹要用比較小的學習率？ | M4 |
| Q4 | LoRA 為什麼省記憶體？rank 調大調小有什麼影響？ | M4 |
| Q5 | 類別不平衡時，AUROC 和 AUPRC 差在哪？ | M3 |
| Q6 | 怎麼從曲線看出過擬合？發生了怎麼辦？ | M2 |
| Q7 | batch 很小的時候，BatchNorm 會出什麼問題？ | M4 |

Q7 的說明：主骨幹是 ViT，用的是 LayerNorm，本身沒有這個問題。M4 會加一個小示範（ResNet-50 在 batch 2 與 batch 32 下的差異），讓這題有實際數字可以對照，並說明 ViT 為什麼不受影響。

## 3. 學習方式（Learning 模式）

主線採家教模式：agent 當家教，使用者當學生。

### 3.1 留給使用者寫的三個函式

每個 10 到 30 行。agent 先寫好介面（函式簽名、docstring、型別）與測試，使用者寫完、測試通過就算完成。

| 函式 | 內容 | 里程碑 |
|---|---|---|
| `train_step` | 單一訓練步：forward → loss → backward → 混合精度 | M2 |
| 不平衡處理的 loss | 例如帶正樣本權重的 BCE | M3 |
| LoRA 設定 | 加在哪幾層、rank、alpha | M4 |

- 只有這三處可以出現 `TODO(human)`；其他地方出現會讓測試失敗
- 使用者還沒寫完時，該里程碑的訓練不開跑

### 3.2 提示規則

使用者卡住時分三段給提示，一次只給一段，使用者要求才給下一段：

1. 觀念：這一步在解決什麼問題
2. 方向：會用到哪些 API、步驟順序
3. 程式碼：最後才給

不可以一開始就給答案。

### 3.3 其餘部分

其餘程式全部由 agent 實作，並在回覆中用 Insight 段落說明設計理由（為什麼這樣做、另一種做法是什麼、取捨在哪）。

## 4. 資料

### 4.1 NIH ChestX-ray14

| 項目 | 數值 | 來源與狀態 |
|---|---|---|
| 影像／病人 | 112,120 張／30,805 人 | 多個來源一致 |
| 格式 | PNG，1024×1024，灰階 | NIH README 轉述 |
| 下載量 | 45.09 GB，12 個壓縮檔 | Academic Torrents 檔案清單 |
| 標籤 | 14 類＋No Finding，多標籤 | 一致 |
| 標籤來源 | 用 NLP 從放射科報告抽取，官方估計正確率 > 90% | NIH README 轉述 |
| 官方切分 | train_val 86,524 張／test 25,596 張 | 第三方鏡像，待核對 |
| 中繼資料 | Patient ID、Age、Gender、View Position、Follow-up # 等 | NIH README 轉述 |
| 框標註 | 約 1,000 張、8 類 | 確切張數各來源不一（880 到 984），待核對 |
| 授權 | 使用不受限；需註明來源、引用論文、致謝 NIH Clinical Center | NIH README 轉述 |

各標籤張數（第三方鏡像統計，待核對；train_val／test）：

| 標籤 | 全部 | train_val | test |
|---|---|---|---|
| No Finding | 60,361 | 50,500 | 9,861 |
| Infiltration 浸潤 | 19,894 | 13,782 | 6,112 |
| Effusion 肋膜積水 | 13,317 | 8,659 | 4,658 |
| Atelectasis 肺塌陷 | 11,559 | 8,280 | 3,279 |
| Nodule 結節 | 6,331 | 4,708 | 1,623 |
| Mass 腫塊 | 5,782 | 4,034 | 1,748 |
| Pneumothorax 氣胸 | 5,302 | 2,637 | 2,665 |
| Consolidation 實變 | 4,667 | 2,852 | 1,815 |
| Pleural Thickening 肋膜增厚 | 3,385 | 2,242 | 1,143 |
| Cardiomegaly 心臟肥大 | 2,776 | 1,707 | 1,069 |
| Emphysema 肺氣腫 | 2,516 | 1,423 | 1,093 |
| Edema 肺水腫 | 2,303 | 1,378 | 925 |
| Fibrosis 肺纖維化 | 1,686 | 1,251 | 435 |
| Pneumonia 肺炎 | 1,431 | 876 | 555 |
| Hernia 橫膈疝氣 | 227 | 141 | 86 |

值得注意：官方 test 的異常比例明顯高於 train_val（例如氣胸在 test 的張數比 train_val 還多）。這代表官方切分不是隨機抽的，val 分數和 test 分數不能直接比。M1 要把這個差異量出來寫進報告。

### 4.2 切分

- **test**：直接使用 NIH 官方 `test_list.txt`，不自己切
- **val**：從官方 `train_val_list.txt` 按病人切出約 10% 的病人，種子 42
- M1 要驗證：官方 train_val 與 test 沒有共用病人；val 與 train 沒有共用病人
- 切分檔寫成 `data/splits/split_v1.csv` 並附 SHA-256，鎖定後只能讀取
- val 每一類的陽性張數要列出來。Hernia 預期只有十幾張，屬預期，照實報告，不換種子重切

### 4.2.1 重複影像（2026-11-26 使用者確認，規則先於掃描訂定）

背景：NIH 官方 `LOG_CHESTXRAY.pdf` 公告了像素完全相同的影像配對，其中有幾群橫跨官方 train_val 與 test。M1 另外自行掃描全部影像，掃描結果取代官方公告清單。

**像素完全相同的影像群**（解碼成 8 位元灰階後逐像素相同）依下列規則處理，規則在掃描前訂定，掃描後不依結果修改：

| 群的組成 | 處理 |
|---|---|
| 橫跨官方 train_val 與 test | 排除 train_val 那一邊的所有影像（`duplicate_of_test`），test 那一邊保留 |
| 全部在官方 train_val 內 | 整群排除（`duplicate_within_train_val`） |
| 全部在官方 test 內 | 不動，只在報告中列出 |

- **test 一律不動**：test 內部的重複、以及同一張圖掛著不同標籤（標籤衝突）的情形，只在報告中列出，不排除、不改標籤
- 被排除的影像在 `split_v1.csv` 中記為 `split = excluded` 並附原因；val 的病人在排除前就抽定，排除清單不會讓其他病人換組
- 排除只移除個別影像，不移除整位病人

**感知雜湊（perceptual hash）掃描**：另外用感知雜湊掃一次，找出「看起來幾乎相同但像素不完全相同」的影像配對（例如重新存檔、輕微裁切或亮度調整）。這份結果**只列成可疑名單寫進報告，不自動排除**；要不要處理由使用者看過名單後決定。

**人工確認的近似重複**（2026-11-26 使用者確認，原則：訓練與測試之間不可有汙染）：可疑名單中經人工看圖確認是同一次拍攝、且橫跨官方 train_val 與 test 的配對，排除 train_val 那一邊（`near_duplicate_of_test`），test 那一邊不動。確認過的配對寫在 `chestxraylab.data.CONFIRMED_NEAR_DUPLICATE_PAIRS`，每一筆都要使用者確認才能加入；切分腳本只讀這份清單，不讀感知雜湊的掃描結果。目前有 1 對：`00027864_004.png`（train_val）與 `00027927_032.png`（test）。兩張都在 test 內的近似重複照樣不動，只在報告中列出。

鎖定 `split_v1.csv` 之前，最終排除名單要先給使用者確認。

### 4.3 胸管標註（已查到公開資料）

NIH 原始標籤沒有胸管資訊，但有一份公開的補充標註：

- 名稱：NEATX（Non-Expert Annotations of Tubes in X-rays），Zenodo DOI 10.5281/zenodo.14944064
- 內容：NIH 中標為氣胸的影像，3,543 張有「有／無胸管」的影像層級標註
- 標註者：兩位資料科學學生，不是醫師。論文說和放射科醫師的標註一致性高，但我沒查到 NIH 這部分的具體數字
- 授權：CC BY-NC-SA 2.0（非商業、相同方式分享）。這份檔案不進 repo，使用時下載，報告註明來源
- 另有一份放射科醫師標註（1,592 張，Oakden-Rayner 等人 2020），沒查到公開下載處，不使用

待核對：這 3,543 張有多少落在官方 test。落在 test 的張數太少時回報，由使用者決定怎麼處理。

### 4.4 前處理

- 原圖解壓後另存一份 512 px 的快取，訓練時從快取讀取
- 資料下載優先用 NIH 官方來源；下載後核對檔案完整性（壓縮檔可完整解開、影像張數與 `Data_Entry` 清單逐一對上、每張都能開啟）
- 磁碟：D 槽目前剩 656 GB。壓縮檔 45 GB＋解壓約 45 GB＋快取，估計共 100 GB 以內

## 5. 模型

### 5.1 骨幹

三種微調方式共用同一個骨幹：**ViT-B/14（DINOv2 架構）**。

選它的理由：

- LoRA 適用：注意力層的 query、value 是 LoRA 的標準掛載位置
- 一般預訓練與 X 光預訓練有同架構的權重可以比，目標 3 只換權重、不換架構
- 16 GB 放得下全部微調

### 5.2 預訓練權重與訓練資料

| 權重 | 架構 | 訓練資料 | 用過 NIH 影像？ | 處理方式 |
|---|---|---|---|---|
| `facebook/dinov2-base` | ViT-B/14 | 一般網路影像（模型頁沒寫資料集，需讀論文確認） | 未記載，推定沒有 | 主骨幹，目標 2 用它 |
| `microsoft/rad-dino` | ViT-B/14 | MIMIC-CXR 368,960、CheXpert 223,648、NIH-CXR 112,120、PadChest 136,787、BRAX 41,260 | **有，112,120 張等於整份 NIH** | 納入比較，所有表格標註「預訓練看過全部 NIH 影像（含 val 與 test）」 |
| `microsoft/BiomedCLIP` 影像編碼器 | ViT-B/16 | PubMed Central 的 1,500 萬組圖文 | 模型頁只列這份資料 | 選做的乾淨對照（見下） |

RAD-DINO 的說明：

- 它是自監督預訓練，沒有用到 NIH 的標籤，但看過全部 NIH 影像，包含我們的 train、val 與官方 test。所以不只 test 分數可能偏高，**val 上的比較同樣受影響**，M5 報告要寫明這一點
- 模型頁附有訓練影像清單 `training_images.csv`。M5 開始前要拿它和官方 `test_list.txt` 比對，確認與 train／val／test 各自的重疊張數後寫進報告
- 釋出的權重和論文不同（拿掉私有資料、訓練步數較少），引用數字時不可拿論文的當對照

其他查過但不採用的權重：

- CheXzero：只用 MIMIC-CXR，沒用 NIH，但架構沒有在說明文件中寫明，權重放在 Google Drive
- Google CXR Foundation：沒用 NIH，但需同意條款才能下載，架構是 EfficientNet，和主骨幹不同
- TorchXRayVision 的 `all` 系列：訓練資料包含 NIH 且用了標籤，排除

選做的乾淨對照：如果 RAD-DINO 明顯勝過 DINOv2，沒辦法分辨是「X 光預訓練有用」還是「看過這些影像」。這時加跑 BiomedCLIP（沒看過 NIH，但架構與訓練方式都不同，只能當旁證）。要不要跑在 M5 看結果再決定。

### 5.3 三種微調方式（目標 2）

骨幹固定為 `facebook/dinov2-base`：

| 方式 | 訓練哪些參數 |
|---|---|
| Linear probe | 只訓練分類頭，骨幹凍結 |
| Full fine-tuning | 全部參數，骨幹用較小的學習率 |
| LoRA | 骨幹凍結，只訓練 LoRA 的低秩矩陣與分類頭 |

每種方式記錄：val 指標、可訓練參數量、GPU 記憶體峰值、每個 epoch 的時間。

### 5.4 輸入解析度

主要比較全部用 224 px，讓每個實驗跑得快、三種方式條件一致。小病灶（結節）在這個解析度會吃虧，這點寫進限制。最佳設定另外在 val 上用較高解析度跑一次當敏感度分析，不上 test。

### 5.5 M5 比較預訓練來源時的輸入設定

- **正規化**：兩個權重各自使用原生設定（從各自模型的前處理設定檔讀取平均值與標準差），不共用同一組數字
- **解析度**：兩個權重各自使用原生的輸入解析度。原生解析度的實際數值在 M5 開始前從模型的前處理設定檔與論文查清楚並寫進報告
- 如果 16 GB 記憶體或訓練時間讓原生解析度跑不動，改用較低的共同解析度，並在報告中說明：和原生差多少、哪一個權重比較吃虧、對結論的影響
- 兩個權重的解析度不同時，報告要說明差異有多少可能來自解析度而不是預訓練資料

## 6. 評測

- 主指標：14 類各算 AUROC 再取平均（macro AUROC）；同時報 macro AUPRC 與各類的 AUROC、AUPRC
- 信賴區間：按病人重抽的 bootstrap，2,000 次，種子 42
- 版本之間的差異用配對 bootstrap
- 調參、選模型、早停只看 val
- **需要閾值的指標**（recall、precision、F1，例如氣胸 recall）：閾值一律在 val 上決定並記錄決定方式，上 test 時沿用同一個數值，不可看 test 再調。分群分析（PA／AP、有／無胸管）也用同一個閾值，不分群各調
- **閾值的決定方式：在 val 上固定 sensitivity**（2026-11-26 使用者確認）。每一類各自取「val 上 sensitivity（= recall）達到目標值」的閾值，不用最大化 F1。理由：官方 test 的盛行率與 train_val 差很多（氣胸陽性比例是 3.4 倍），F1 含 precision，最佳閾值會隨盛行率移動，在 val 上最大化 F1 得到的閾值搬到 test 並不是最佳；sensitivity 只看陽性樣本，不受盛行率影響。**目標 sensitivity 為 0.80，14 類統一**（2026-11-26 使用者確認）；報告要同時列出 val 上的閾值、val 實際達到的 sensitivity 與 specificity。Hernia 在 val 只有十幾張陽性，閾值很不穩定，報告要特別註明
- **AUPRC 受盛行率影響**：AUPRC 的隨機基準線等於該類的陽性比例，同一個模型在陽性比例較高的資料上 AUPRC 會自然變高。所有列出 AUPRC 的報告都要註明「val 與 test 的 AUPRC 不可直接比較」，並在 AUPRC 旁列出該組該類的陽性比例；precision 與 F1 同樣受盛行率影響，val 與 test 之間也不可直接比較。AUROC、sensitivity、specificity 不受盛行率影響
- **test 每個版本只評估一次**，全部集中在 M6。要上 test 的版本在 M6 開始前列成清單，由使用者確認
- **官方 test 與清理後 test 並列**（2026-11-26 使用者確認）：M6 的每個指標除了在官方 test 上報告，另外在「清理後 test」上報告一次，兩者並列。**官方 test 為主要成績**，清理後 test 是輔助，用來看重複影像與標籤衝突對分數的影響有多大。定義見第 6.1 節

### 6.1 清理後 test

清理後 test 是官方 test 的子集，只拿掉有問題的影像，不新增、不改標籤：

| 重複群的情形 | 處理 |
|---|---|
| 群內標籤全部相同 | 群內位於 test 的影像只留一張（檔名排序最前面的那張） |
| 群內有標籤衝突（同一張圖掛著不同標籤） | 群內位於 test 的影像全部移除 |

- 「重複群」包含兩種：像素完全相同的影像群（第 4.2.1 節），以及人工看圖確認為同一次拍攝的近似重複配對
- 群若橫跨 train_val 與 test，判斷標籤衝突時把已排除的 train_val 那一邊也算進去；群內只有一張在 test 且無衝突時，那一張保留
- 感知雜湊名單中未經人工確認的配對（例如同一位病人的連拍）不算重複群，不影響清理後 test
- 清理名單只依掃描結果與中繼資料決定，**不看任何模型的輸出**，並在 M6 開始前、任何版本上 test 之前定案，隨程式碼進版控
- 清理後 test 的指標用同一次 test 推論的結果取子集計算，不另外再跑一次，所以不違反「test 每個版本只評估一次」
- 信賴區間與配對 bootstrap 在兩份 test 上各算一次；報告註明清理後 test 拿掉了幾張、各類陽性各少幾張

依 M1 的掃描結果預估會拿掉 15 張（官方 test 25,596 張 → 清理後 25,581 張），確切名單在 M6 定案時產出。

## 7. 里程碑

每個里程碑結束時在 `reports/` 產出 Markdown 報告、回報關鍵數字、考相關題目，**等使用者確認後才做下一個**。

| 里程碑 | 內容 | 使用者寫 | 考題 |
|---|---|---|---|
| M1 資料 | 環境建置、下載、盤點（核對第 4 節所有數字）、切分並鎖定、建 512 px 快取 | 無 | 無 |
| M2 訓練流程 | 資料讀取與增強、訓練迴圈、混合精度、早停、存檔、曲線圖；跑出 linear probe 第一個數字 | `train_step` | Q1、Q2、Q6 |
| M3 不平衡與指標 | 指標模組、bootstrap、比較有無不平衡處理 | 不平衡 loss | Q5 |
| M4 微調策略 | 三種微調方式比較；BatchNorm 小示範 | LoRA 設定 | Q3、Q4、Q7 |
| M5 預訓練來源 | 比對 RAD-DINO 訓練清單與 test；DINOv2 對上 RAD-DINO | 無 | 複習 Q3、Q6 |
| M6 稽核與 test | 預先列出的版本上 test（官方 test 與清理後 test 並列）；PA／AP 分群；氣胸有／無胸管分群；熱力圖對照醫師的框；限制段落 | 無 | 七題全考 |

選做（主線完成後再決定）：CheXpert 外部驗證、MedGemma 4B 的 QLoRA 微調。

### M6 捷徑稽核的三項

1. **PA／AP 分群**：所有 test 指標按拍攝方式分兩群報告；另外訓練一個只吃 View Position 的 baseline，看光靠拍攝方式能猜到多準
2. **氣胸有／無胸管**：用 NEATX 標註把 test 的氣胸影像分兩群，分別算氣胸的 AUROC 與 recall（閾值在 val 上決定）。模型如果只在有胸管的那群表現好，代表它認的是管子。報告註明標註者不是醫師、授權為非商業
3. **熱力圖對照框**：在有醫師畫框的影像上，檢查熱力圖最亮的點是否落在框內（pointing game），按類別報告命中率

## 8. 不可違反的規則

1. 同一位病人的影像不可跨 train／val／test
2. `split_v1.csv` 鎖定後只能讀取；調參只用 train／val；test 每個版本只評估一次
3. 不可作為模型輸入：標籤、Patient ID、檔名、View Position、Follow-up #、胸管標註（後三者只用於分群報告）
4. 不 commit 原始影像、快取、模型權重、NEATX 檔案；只 commit 程式碼、報告、切分清單與雜湊
5. 隨機種子固定為 42，結果要能重跑出相同數字（GPU 上的微小浮點差異在報告中說明容許範圍）
6. 數字不如預期時只回報，不可自行換種子重跑挑結果
7. 預訓練權重用過 NIH 影像的，所有表格都要標註
8. 需要閾值的指標，閾值只在 val 上以固定 sensitivity 決定，不可看 test 再調
9. 規格與實際資料矛盾時停下回報，不自行假設
10. 重複影像依第 4.2.1 節的規則處理：test 一律不動；感知雜湊的結果只列名單，不自動排除
11. 官方 test 為主要成績；清理後 test（第 6.1 節）只並列當輔助，清理名單不可看模型輸出決定

## 9. 技術選擇

- Python 3.11，環境管理用 uv；PyTorch 需選支援 RTX 50 系列的 CUDA 版本（M1 查文件確認）
- 模型載入用 `transformers`，LoRA 用 `peft`；API 用法在實作前查當時的文件
- 格式化與 lint 用 ruff；docstring 用 Google style
- Windows 終端編碼 cp950：執行 Python 前設 `PYTHONIOENCODING=utf-8`，程式輸出不用 emoji

## 10. 目錄結構（預定）

```
data/raw/            原始壓縮檔與解壓影像（不進版控）
data/cache/          512 px 快取（不進版控）
data/external/       NEATX 等補充標註（不進版控）
data/splits/         split_v1.csv 與 split_v1.sha256（進版控）
src/chestxraylab/    data / split / transforms / models / train / losses / lora / metrics
scripts/             每個里程碑的步驟腳本
reports/             每步驟報告與圖表
checkpoints/         模型權重（不進版控）
tests/
```

## 11. 還沒核對的項目

| 項目 | 何時核對 |
|---|---|
| 官方 train_val／test 的張數、病人數、是否按病人切 | M1 |
| 各標籤張數、PA／AP 張數 | M1 |
| 框標註的確切影像數、框數、8 個類別 | M1 |
| NEATX 落在官方 test 的張數 | M1 |
| 自行掃描的重複影像群是否涵蓋官方公告的全部配對 | M1 |
| DINOv2 的訓練資料（讀論文） | M5 之前 |
| RAD-DINO 訓練清單與 train／val／test 的重疊張數 | M5 之前 |
| 兩個權重的原生解析度與正規化數值 | M5 之前 |
| 每個 epoch 的實際時間與記憶體用量 | M2 |

## 12. 查證來源

- NIH ChestX-ray14 下載頁：https://nihcc.app.box.com/v/ChestXray-NIHCC
- NIH README 轉述與檔案清單：https://academictorrents.com/details/557481faacd824c83fbf57dcf7b6da9383b3235a
- 各標籤與切分張數（第三方鏡像）：https://huggingface.co/datasets/alkzar90/NIH-Chest-X-ray-dataset
- 資料集論文：Wang et al., ChestX-ray8, CVPR 2017，https://arxiv.org/abs/1705.02315
- NEATX：https://zenodo.org/records/14944064 ，論文 https://arxiv.org/abs/2309.02244
- RAD-DINO：https://huggingface.co/microsoft/rad-dino
- DINOv2：https://huggingface.co/facebook/dinov2-base
- BiomedCLIP：https://huggingface.co/microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224
- CheXzero：https://github.com/rajpurkarlab/CheXzero
- CXR Foundation：https://huggingface.co/google/cxr-foundation
- TorchXRayVision：https://github.com/mlmed/torchxrayvision
