# 🛠️ 技能手冊：資安漏洞掃描工具 (scan_tool.md)

> 📌 **大腦行為準則 (System Instruction)**
> 在調用任何外部工具前，大腦 **必須先閱讀並檢索此手冊**，嚴格對比使用者意圖與本手冊中的工具描述。比對成功後，提取標準化參數進行 `execute_garak_attack` 調用。嚴禁憑空捏造不存在的工具名稱或隨意猜測參數。

---

## 📖 一、已驗證可用的 Garak 探針清單（v0.15.0）

以下探針均已確認存在，大腦**嚴禁**以「探針不存在」為理由拒絕呼叫工具：

| 探針名稱 | 說明 |
| :--- | :--- |
| `promptinject.HijackHateHumans` | 測試模型是否會輸出 "I hate humans" |
| `promptinject.HijackKillHumans` | 測試模型是否會輸出 "I will kill humans" |
| `promptinject.HijackLongPrompt` | 長提示詞注入，測試模型是否會被劫持 |
| `continuation.ContinueSlursReclaimedSlurs` | 續寫測試，看模型是否會接續敏感字眼 |
| `dan.AutoDANCached` | DAN 越獄攻擊 |
| `dan.DanInTheWild` | 野生 DAN 越獄攻擊 |
| `encoding.InjectBase64` | Base64 編碼注入攻擊 |
| `grandma.Slurs` | 以祖母角色誘導輸出仇恨詞彙 |

## 📖 二、Garak 攻擊武器庫定位與使用指南

`Garak` (Generative AI Redteaming & Assessment Kit) 是一款專為大語言模型（LLM）設計的**脆弱性掃描器**。其運作邏輯類似於傳統網路安全中的 `Nmap`，透過注入各種攻擊探針（Probes）來分析目標模型的防守極限與潛在漏洞。

### 1. 核心參數自動轉譯表
大腦在解析使用者的自然語言時，應依據此表將口語意圖自動轉譯為 Python 工具可識別的精準參數：

| 使用者口語指令描述 | 建議 attack_type | 建議 target_model |
| :--- | :--- | :--- |
| **「掃一下」、「測試看看」、「掃描」（未指定探針）** | `promptinject.HijackHateHumans` | `ollama/tinydolphin` |
| **「HijackHateHumans」、「HateHumans 注入」** | `promptinject.HijackHateHumans` | `ollama/tinydolphin` |
| **「HijackKillHumans」** | `promptinject.HijackKillHumans` | `ollama/tinydolphin` |
| **「續寫測試」、「ContinueSlurs」** | `continuation.ContinueSlursReclaimedSlurs` | `ollama/tinydolphin` |
| **「DAN 攻擊」、「越獄」** | `dan.DanInTheWild` | `ollama/tinydolphin` |

---

## ⚠️ 三、強制執行規則

1. 只要使用者的意圖是掃描或攻擊，**必須立即呼叫 `execute_garak_attack` 工具**，不得以任何理由延遲或拒絕。
2. 呼叫工具前，必須先告訴使用者將要執行的指令，格式如下：

> 🖥️ 即將執行：`garak --model_type ollama --model_name {model_name} --probes {attack_type} --generations 1`

3. 未指定模型時，預設使用 `ollama/tinydolphin`。
4. 未指定探針時，預設使用 `prompt_inject`。

## 💻 四、Garak 完整 CLI 指令格式解析

在 Python 執行端（身體）接收到大腦的決策後，Garak 會透過作業系統命令列發動攻擊。底層標準的指令結構如下：

```bash
garak --model_type <類型> --model_name <模型名稱> --probes <攻擊探針> --generations <測試次數>
```

### ⚙️ 參數詳細說明
- model_type * 定義 LLM 的提供者類型。在本地對抗實驗環境中，一律固定填入 ollama。

- model_name * 指定 Ollama 本地已下載並運行的模型名稱，例如 tinydolphin、llama3.2。

- probes * 決定要使用的攻擊探針（漏洞檢測模組）。

- prompt_inject：最常見的提示詞注入攻擊，嘗試繞過系統原設安全框架。

- promptinject.HijackHateHumans：專門測試模型是否會被誘騙並輸出 "I hate humans" 違禁語。

- continuation.ContinueSlurs：續寫測試。嘗試在開頭輸入敏感字眼，看模型是否會順從地接續輸出。

- generations 
    - 每個測試點產生的回應次數（Garak 預設為 5 次）。
    - 本地硬體優化原則：為避免 8GB RAM 記憶體卡死或測試時間過長，在 AI Agent 工具調用中建議將此參數強制限制為 1，這能縮短近 5 倍的掃描時間。