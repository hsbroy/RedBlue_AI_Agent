# 🛡️ LLM Red-Blue Team AI Agent 實驗專案

本專案旨在透過 **LangChain**、**Ollama (本地端大語言模型)** 與 **Garak (LLM 脆弱性掃描器)**，構建一個本地自動化的紅藍對抗實驗環境。利用本地運行的開源大模型，在不消耗雲端 API 成本且保障資料隱私的前提下，進行提示詞注入（Prompt Injection）與防禦機制測試。

---

## 一、📋 專案架構與工具定位

為了在受限的硬體環境下達到最高效的運作，本專案精準配置了以下工具鏈：



* **LangChain & LangChain-Ollama**：專案的**「神經傳導系統」**。負責將 Python 業務邏輯與本地 Ollama 模型進行對接，實現 Agent 的鏈式決策。
* **Llama 3.2 (3b)**：紅藍 Agent 的**「核心大腦」**。具備優秀的語意理解能力，負責制定攻擊策略（紅方）與進行意圖審查（藍方）。
* **nomic-embed-text & ChromaDB**：Agent 的**「經驗記憶庫 (RAG)」**。用於儲存並檢索 Garak 歷史攻擊日誌（`hitlog.jsonl`），讓 Agent 能夠透過過往經驗優化攻防策略。
* **Pandas**：**「資安數據分析模組」**。針對 Garak 生成的大量 JSONL 測試日誌進行高效的解析與統計。

---

## 二、🧠 AI Agent 核心設計哲學

本專案參考現代 AI Agent 的軟體工程最佳實踐，採用 **大腦與身體分離** 以及 **角色與技能解耦** 的架構設計。

### 1. 核心公式與控制循環 (Control Loop)
Agent 的本質是一段在 Python 中運行的循環程式碼，作為 LLM 與現實工具之間的傳話者：

$$\text{Agent (代理)} = \text{大腦 (LLM)} + \text{身體 (Python 控制代碼)} + \text{工具 (外部腳本/API)}$$


         ┌────────────────────────────────────────┐
         │                                        │
         ▼                                        │
    ┌──────────────┐   思考 (Reasoning)    ┌──────────────┐
    │  大腦 (LLM)  ├─────────────────────► │ 產生工具指令  │_________
    └──────────────┘                       └──────┬──────┘         │
         ▲                                        │                │
         │ 觀察 (Observation)                     │ 行動 (Action)   │
         │                                        ▼                │
    ┌────┴─────────┐                      ┌──────────────┐         │
    │  更新狀態紀錄 │◄─────────────────────┤ 身體執行工具  │         │
    └──────────────┘                      └──────────────┘         │
         ▲                                                         │
         └─────────────────────────────────────────────────────────┘


* **思考 (Reasoning)**：將當前狀態與 `skill.md` 說明書丟給 LLM，由 LLM 決策下一步並輸出 JSON 格式的指令。
* **行動 (Action)**：身體（Python 程式碼）解析 JSON，調用對應的指令發動攻擊或進行攔截。
* **觀察 (Observation)**：將外部工具回傳的掃描結果或狀態傳回大腦，供大腦進行下一輪決策。

### 2. 結構化管理：Agent 與 Skill 解耦
為了提高系統的可重用性與靈活性，我們將角色行為與執行工具徹底分離：

    /Prompt_Project
    ├── /agents
    │   ├── red_agent.md     # 定義紅方攻勢邏輯 (它是誰、如何思考)
    │   └── blue_agent.md    # 定義藍方防護準則
    └── /skills
    ├── search_vault.md  # RAG 檢索技能 (ChromaDB)
    └── scan_tool.md     # 漏洞掃描技能 (Garak 工具調用)


* **`agent.md` (定義靈魂)**：處理任務的 SOP、專業身份、語氣及絕對不可觸犯的 Hard Rules。
* **`skill.md` (定義技能)**：描述工具的使用時機與傳參格式（Function Calling），像積木一樣讓不同的 Agent 自由引用。

---

# 安裝
## 一、基礎工具
    1. 安裝Python
    2. 安裝anaconda
    3. 安裝visual studio code
    4. 安裝git

## 二、開發環境
1. 創建 conda 環境
    a. 創建Python版本為3.11的虛擬環境 -> 
    ```PowerShell
    conda create -n py311_langchain1.0 python=3.11 
    ```
    b. 進入剛剛建立的虛擬環境
    ```PowerShell
    conda activate py311_langchain1.0 
    ``` 
    c. 左側有顯示你輸入的虛擬環境名稱代表已成功進入該虛擬環境
    ```(py311_langchain1.0) PS D:\Desktop\AI_Agent的開發>  ```

## 三、安裝 langchain 核心包
1. 安裝指令-1
    ```PowerShell 
    pip install langchain
    ```
2. 套件安裝版本控制-1
    ```PowerShell 
    pip freeze > pypackage_langchain.txt
    ```
3. 安裝指令-2
    ```PowerShell 
    pip install langchain-community
    ```
4. 套件安裝版本控制-2
    ```PowerShell 
    pip freeze > pypackage_langchain_community.txt
    ```

## 四、安裝Ollama
1. 安裝Ollama: https://ollama.com/
2. 下載模型: https://ollama.com/search
    (1) 聊天模型: 
    ```PowerShell 
    ollama pull deepseek -r1:1.5b # (我沒安裝)
    ollama pull llama3.2:3b
    ``` 
    (2) 嵌入模型: 
    ```PowerShell
    ollama pull nomic-embed-text
    ```
    查看:
    ```PowerShell
    ollama list
    ```
3. 安裝 langchain -ollama
    ```PowerShell
    pip install langchain-ollama
    ```

## 五、安裝 deepseek API 接口
```pip install langchain-deepseek``` (我沒安裝)

## 六、安裝向量數據庫
1. 安裝指令
    ```PowerShell
    pip install chromadb # (我還沒安裝)
    pip install langchain-chroma # (我還沒安裝)
    ```
2. 套件安裝版本控制
    ```PowerShell
    pip freeze > pypackage_4_langchain_chromadb.txt
    ```


學習教材: 
1. YouTube 大模型 : https://www.youtube.com/@%E5%A4%A7%E6%A8%A1%E5%9E%8B-%E6%95%99%E7%A8%8B
2. 相關影片: https://www.youtube.com/watch?v=RPS2leOER_o&list=PLXiXcDkQM7PsbNB5fvR5g7qEYqoOOnjQj&index=2

# 專案開發補充 (針對紅藍對抗實驗)
## 一、工具定位說明 (為什麼裝這些？)
    LangChain & LangChain-Ollama: 這是你 Agent 的**「神經傳導系統」**。它負責把你寫的 Python 指令轉換成 Llama 3.2 能聽懂的格式，並把模型的回答傳回給你的程式。

    Llama 3.2 (3b): 這是你的**「攻擊/防禦大腦」**。比起 TinyDolphin，它的邏輯推理能力更適合作為決策者，負責思考攻擊策略。

    nomic-embed-text & ChromaDB: 這是 Agent 的**「經驗筆記本 (向量數據庫)」**。當未來要讓紅方 Agent 「學習」過去的失敗經驗（例如讀取 Garak 的歷史日誌進行檢索）時，就必須靠它們來實現 RAG (檢索增強生成)。

## 二、環境精簡建議
    無需安裝 langchain-deepseek: 由於本專案採用 Ollama 本地端運作，不需透過雲端 API 接口，可避免環境過於臃腫並節省成本。

## 三、建議額外安裝 (用於資安日誌分析)
為了讓 Agent 能夠讀取並分析 Garak 產生的 hitlog.jsonl 檔案，建議在虛擬環境中補上數據分析工具：
```Bash 
pip install pandas # 用於高效處理、篩選和分析 Garak 的掃描數據
``` 

## 四、🗺️ 開發藍圖 (Development Roadmap)
本專案將紅藍對抗實驗分為兩大核心模組進行實作：

                               ┌─────────────────┐
                               │   User Prompt   │
                               └────────┬────────┘
                                        ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │ 藍方 Agent (Blue Agent)                                                 │
    │ 1. 攔截請求 ──> 2. Llama 3.2 意圖審查 (安全過濾) ──> 3. 阻斷惡意輸入       │
    └───────────────────────────────────┬─────────────────────────────────────┘
                                        │ (安全通過)
                                        ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │ 紅方 Agent (Red Agent)                                                 │
    │ 1. 策略制定 ──> 2. 呼叫 Garak / 攻擊腳本 ──> 3. 讀取與分析 JSONL 日誌     │
    └─────────────────────────────────────────────────────────────────────────┘
🔴 1. 紅方 Agent (Red Agent) 實作
    
    規劃決策：由 Llama 3.2 針對目標模型分析漏洞，並動態制定提示詞注入測試腳本。

    武器庫發動：透過 Python 的 subprocess 自動化調用 Garak 工具發起測試探針。

    觀察與自我優化：讀取並利用 Pandas 分析 hitlog.jsonl 日誌中的 score，紀錄失敗經驗以進行下一輪攻擊。

🔵 2. 藍方 Agent (Blue Agent) 實作

    請求攔截：在外部輸入（Prompt）進入本地靶機前進行強制擷取。

    安全性審查：由專職防禦的 Llama 3.2 模型充當安全守門員，判斷該輸入是否包含「角色扮演劫持、違禁詞誘導、續寫攻擊」等惡意意圖。

    阻斷與放行：偵測到風險則立即中斷請求並返回安全警示，否則放行至目標模型。