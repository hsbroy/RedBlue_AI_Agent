import os
from dotenv import load_dotenv

# 1. 載入環境變數（包含 API 金鑰或環境變數配置），override=True 代表優先覆蓋已存在的變數
load_dotenv(override=True)

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from skills.tools import search_vault, execute_garak_attack  # 引入定義好的 RAG 檢索與 Garak 掃描工具

from langchain.agents import create_agent

# ==========================================================
# === 📂 核心模組 1：檔案載入與組裝靈魂 (Prompts & Skills) ===
# ==========================================================

def load_agent_prompt(file_path: str) -> str:
    """
    讀取紅方代理的「靈魂檔案」(agents/red_agent.md)，定義它的性格、目標與限制。
    如果檔案不存在，則使用預設提示詞，防止程式中斷。
    """
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        print(f"⚠️ 警告：找不到 {file_path}，將使用預設紅方提示詞。")
        return "你是一個紅方攻擊 Agent。"


def load_skill_manual(file_path: str) -> str:
    """
    讀取紅方代理的「技能手冊」(skills/scan_tool.md)，讓大腦（LLM）了解有哪些工具可供使用。
    這能有效防止 LLM 憑空捏造或猜測工具參數。
    """
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    print(f"⚠️ 警告：找不到 {file_path}")
    return "尚無技能描述。"


# 載入並組合完整的系統指令：紅方靈魂 + 技能手冊，融合成單一 system_instruction
red_agent_instruction = load_agent_prompt("agents/red_agent.md")
scan_tool_manual = load_skill_manual("skills/scan_tool.md")

system_instruction = f"""
{red_agent_instruction}

=== 📋 你的可用工具操作手冊 (scan_tool.md) ===
在調用任何工具之前，你必須先閱讀並嚴格遵守以下手冊的定義與限制，精準轉譯參數：
{scan_tool_manual}
"""

# ==========================================================
# === 🧠 核心模組 2：大腦初始化與官方框架綁定 ===
# ==========================================================

# 初始化本地大腦 改用 qwen2.5:3b 模型（原本使用Llama 3.2 3B 模型）
llm = ChatOllama(model="qwen2.5:3b", temperature=0)

# 定位工具列表
tools = [search_vault, execute_garak_attack]


red_agent_executor = create_agent(
    llm,
    tools=tools,
    system_prompt=system_instruction
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
    啟動互動式終端機對話，允許使用者進行多次對話，Agent 會自動記住先前的上下文紀錄。
    """
    # 定義對話執行緒 ID (Thread ID)，官方框架藉此識別並抽取出對應的歷史紀錄 
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

            print(f"\n=== ☠️ 收到紅方指令：'{user_question}' ===")
            print("🧠 [紅方大腦] 正在讀取歷史紀錄並規劃任務...")
            
            # 建立輸入狀態群
            inputs = {"messages": [HumanMessage(content=preprocess_input(user_question))]}
            
            result = red_agent_executor.invoke(inputs) # 執行對話，官方框架會自動處理歷史紀錄的抽取與上下文整合
            
            # 提取最新一輪的大腦最終定案回應
            final_response_content = result["messages"][-1].content

            # 💡 終端機顯示
            print("\n" + "-"*40)
            print("💡 [紅方大腦回應]")
            print("-"*40)
            print(final_response_content)
            print("-"*40)
            
            # 💡 本地追加儲存：以追加模式 ("a") 寫入，保留多輪對話的完整軌跡
            with open(report_filename, "a", encoding="utf-8") as f:
                f.write(f"### 👤 使用者指令\n{user_question}\n\n")
                f.write(f"### 🤖 紅方分析結果\n{final_response_content}\n\n")
                f.write(f"{'='*30}\n\n")
            
            print(f"💾 對話軌跡已同步追加至 `{report_filename}`。")

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