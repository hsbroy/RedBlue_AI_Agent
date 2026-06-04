import os
from dotenv import load_dotenv

# 1. 載入環境變數（包含 API 金鑰或環境變數配置），override=True 代表優先覆蓋已存在的變數
load_dotenv(override=True)

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage  # SystemMessage 已由 create_agent 的 system_prompt 參數取代
from skills.red_tools import search_vault, execute_garak_attack  # 引入定義好的 RAG 檢索與 Garak 掃描工具
from skills.blue_tools import inspect_prompt  # 引入藍方意圖審查工具
from langchain.agents import create_agent

# ==========================================================
# === 📂 核心模組 1：檔案載入與組裝靈魂 (Prompts & Skills) ===
# ==========================================================

def load_agent_prompt(file_path: str) -> str:
    """
    讀取 Agent 的「靈魂檔案」（.md），定義它的身分、目標與行為限制。
    紅方讀 agents/red_agent.md，藍方讀 agents/blue_agent.md。
    如果檔案不存在，回傳預設提示詞防止程式中斷。
    """
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        print(f"⚠️ 警告：找不到 {file_path}，將使用預設提示詞。")
        return "你是一個 Agent。"


def load_skill_manual(file_path: str) -> str:
    """
    讀取 Agent 的「技能手冊」（.md），讓 LLM 知道有哪些工具可以使用以及如何傳遞參數。
    紅方讀 skills/red_scan_tool.md，藍方讀 skills/blue_scan_tool.md。
    這能有效防止 LLM 憑空捏造不存在的工具名稱或隨意猜測參數。
    """
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    print(f"⚠️ 警告：找不到 {file_path}")
    return "尚無技能描述。"


# 載入並組合完整的系統指令：紅方靈魂 + 技能手冊，融合成單一 system_instruction
red_agent_instruction = load_agent_prompt("agents/red_agent.md")
scan_tool_manual = load_skill_manual("skills/red_scan_tool.md")

system_instruction = f"""
{red_agent_instruction}

=== 📋 你的可用工具操作手冊 (scan_tool.md) ===
在調用任何工具之前，你必須先閱讀並嚴格遵守以下手冊的定義與限制，精準轉譯參數：
{scan_tool_manual}
"""

# ==========================================================
# === 🧠 核心模組 2：大腦初始化與官方框架綁定 ===
# ==========================================================

# 紅方與藍方共用同一個 LLM 實例，節省記憶體
# temperature=0 確保推理結果穩定，不會因為隨機性導致工具呼叫行為不一致
llm = ChatOllama(model="qwen2.5:3b", temperature=0)

# 紅方工具清單：攻擊掃描（execute_garak_attack）與機密查詢（search_vault）
tools = [search_vault, execute_garak_attack]

# create_agent 封裝了完整的 ReAct 多輪迴圈：
# LLM 思考 → 決定呼叫工具 → 工具執行 → 觀察結果 → 再次思考，直到不需要工具為止
red_agent_executor = create_agent(
    llm,
    tools=tools,
    system_prompt=system_instruction  # 注入紅方靈魂 + 技能手冊作為全域行為約束
)

# ==========================================================
# === 🛡️ 核心模組 2.5：藍方 Agent 初始化 ===
# ==========================================================

# 載入藍方靈魂與技能手冊，組裝成藍方的 system_instruction
# 藍方靈魂定義了 SHIELD 的身分、三段式判斷原則與標準化輸出格式
blue_agent_instruction = load_agent_prompt("agents/blue_agent.md")
# 藍方技能手冊定義了 inspect_prompt 工具的使用時機、規則清單與 LLM 審查 Prompt
blue_tool_manual = load_skill_manual("skills/blue_scan_tool.md")

blue_system_instruction = f"""
{blue_agent_instruction}

=== 📋 你的可用工具操作手冊 (blue_scan_tool.md) ===
在無法確定輸入是否安全時，你必須呼叫 inspect_prompt 工具進行深度審查：
{blue_tool_manual}
"""

# 藍方只有一個工具：inspect_prompt（兩層混合意圖審查）
# 使用與紅方相同的 LLM 實例，但注入的是藍方的靈魂與技能手冊
blue_agent_executor = create_agent(
    llm,
    tools=[inspect_prompt],
    system_prompt=blue_system_instruction
)

# ============================================================
# === 🔧 前置處理：補足小模型能力缺口（可依模型能力開關）===
# ============================================================

# 升級到更強模型後，把這個設為 True，前置處理會自動停用
STRONG_MODEL_MODE = False

ATTACK_KEYWORDS = ["掃", "測試", "攻擊", "漏洞", "注入", "scan", "attack", "probe"]

DEFAULT_PROBE = "promptinject.HijackHateHumans"
DEFAULT_TARGET = "ollama/tinydolphin"

def preprocess_input(user_question: str) -> str:
    """
    強模型模式關閉時，自動補全攻擊指令的缺失參數。
    升級模型後將 STRONG_MODEL_MODE 設為 True 即可停用。
    """
    if STRONG_MODEL_MODE:
        return user_question  # 強模型直接放行，不做補全
    
    if any(kw in user_question for kw in ATTACK_KEYWORDS):
        # 已明確指定探針就不補
        if "promptinject" not in user_question and "continuation" not in user_question \
                and "dan." not in user_question and "encoding." not in user_question \
                and "grandma." not in user_question:
            user_question += f"，使用 {DEFAULT_PROBE} 探針，目標模型 {DEFAULT_TARGET}"
    
    return user_question

# ==========================================================
# === ⚙️ 核心模組 3：紅方 Agent 多次對話控制循環 ===
# ==========================================================

def start_interactive_session():
    """
    啟動紅藍對抗互動式終端機。
    每一輪輸入都會先經過藍方 SHIELD 審查，通過才交給紅方執行。
    攻防過程與結果同步寫入 agent_conversation_record.md 保留完整軌跡。
    """
    report_filename = "agent_conversation_record.md"
    
    print("\n" + "="*50)
    print("☠️ 紅方 Agent 多次對話互動系統已啟動")
    print("提示：輸入 'exit' 或 'quit' 可結束對話視窗。")
    print("="*50)

    while True:
        try:
            # 取得使用者多次對話的輸入
            user_question = input("\n👤 請輸入指令 >> ").strip()
            
            # 離開條件
            if user_question.lower() in ["exit", "quit"]:
                print("👋 互動結束。")
                break
                
            if not user_question:
                continue

            print(f"\n=== ⚔️  收到指令：'{user_question}' ===")
            # ──────────────────────────────────────────
            # 【藍方先行】：藍方審查永遠在紅方執行之前
            # ──────────────────────────────────────────
            print("\n" + "="*50)
            print("🛡️  [藍方 SHIELD] 正在進行意圖審查...")
            print("="*50)

            blue_inputs = {"messages": [HumanMessage(content=user_question)]}
            blue_result = blue_agent_executor.invoke(blue_inputs)
            blue_response = blue_result["messages"][-1].content

            # 從藍方回應中解析 VERDICT 判定結果
            # 說明：blue_tools.py 的回傳格式保證第一行是 "VERDICT: safe/malicious/suspicious"
            verdict = "unknown"
            for line in blue_response.splitlines():
                if line.startswith("VERDICT:"):
                    verdict = line.replace("VERDICT:", "").strip().lower()
                    break

            # 並排顯示藍方審查結果
            print("\n" + "-"*50)
            print("🛡️  [藍方 SHIELD 審查結果]")
            print("-"*50)
            print(blue_response)
            print("-"*50)

            # ──────────────────────────────────────────
            # 【判斷是否放行給紅方】
            # ──────────────────────────────────────────
            if verdict in ["malicious", "suspicious"]:
                # 藍方阻斷，紅方不執行
                print("\n🚫 [藍方阻斷] 此指令已被攔截，紅方停止執行。")
                red_response_content = "（此輪紅方執行已被藍方阻斷）"

            else:
                # 藍方放行，紅方繼續執行
                print("\n✅ [藍方放行] 安全通過，移交紅方執行...")
                print("\n" + "="*50)
                print("🧠 [紅方大腦] 正在讀取歷史紀錄並規劃任務...")
                print("="*50)
                
                # 建立輸入狀態群
                red_inputs = {"messages": [HumanMessage(content=preprocess_input(user_question))]}
                red_result = red_agent_executor.invoke(red_inputs)
                red_response_content = red_result["messages"][-1].content

                # 並排顯示紅方執行結果
                print("\n" + "-"*50)
                print("💡 [紅方大腦回應]")
                print("-"*50)
                print(red_response_content)
                print("-"*50)

            # ──────────────────────────────────────────
            # 【記錄攻防軌跡】：藍方審查與紅方結果同時寫入報告
            # ──────────────────────────────────────────
            with open(report_filename, "a", encoding="utf-8") as f:
                f.write(f"### 👤 使用者指令\n{user_question}\n\n")
                f.write(f"### 🛡️ 藍方 SHIELD 審查結果\n{blue_response}\n\n")
                f.write(f"### ☠️ 紅方執行結果\n{red_response_content}\n\n")
                f.write(f"{'='*30}\n\n")

            print(f"\n💾 攻防軌跡已同步追加至 `{report_filename}`。")

        except KeyboardInterrupt:
            print("\n👋 偵測到中斷訊號，安全退出。")
            break
        except Exception as e:
            print(f"⚠️ 執行對話時發生意外錯誤: {e}")

# ==========================================================
# === 🎯 執行區 ===
# ==========================================================
if __name__ == "__main__":
    # 執行多次對話終端互動介面
    start_interactive_session()
    
# 指令範例：
# 我想對靶機 tinydolphin 進行 HijackHateHumans 提示詞注入測試，請發動攻擊。

# 改成有記憶性的agent且為多輪輸入模式之測試流程：
# 第一輪：輸入 幫我掃描 tinydolphin 的 HijackHateHumans 漏洞。
# 預期行為：程式會觸發 execute_garak_attack，終端機開始跳出 Garak 掃描進度條，最後給出數據統計。

# 第二輪（關鍵測試點）：接著輸入 那剛剛掃描成功的案例中，攻擊提示詞是什麼？
# 預期行為：此時你完全沒有提模型名稱和工具名稱。但因為掛載了 MemorySaver，Ollama 大腦會主動去調閱上一輪對話中 Garak 回傳的 Markdown 分析數據，並精準把案例的 Prompt 重新條列回答給你！