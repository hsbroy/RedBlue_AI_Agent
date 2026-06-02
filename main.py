import os
from dotenv import load_dotenv

# 1. 載入環境變數（包含 API 金鑰或環境變數配置），override=True 代表優先覆蓋已存在的變數
load_dotenv(override=True)

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from skills.tools import search_vault, execute_garak_attack  # 引入定義好的 RAG 檢索與 Garak 掃描工具

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
# === 🧠 核心模組 2：大腦初始化與工具綁定 (LLM & Tools Setup) ===
# ==========================================================

# 初始化本地大腦（Llama 3.2 3B 模型），將 temperature 設為 0 以追求最高的穩定性與指令遵循度
llm = ChatOllama(model="llama3.2:3b", temperature=0)
# 定位工具列表，並透過 bind_tools 將這些工具插槽提供給 LLM
tools = [search_vault, execute_garak_attack]
llm_with_tools = llm.bind_tools(tools)
''' 
llm: 這是一個 ChatOllama 類別的實例，它是 LangChain 用來與本地 Ollama 伺服器程式 通訊的介面。當你呼叫它時，它背後會透過 API 發送請求給正在你電腦後台執行的 LLM 程式。
llm_with_tools: 這是 llm 的增強版。它依然是那個 LLM，只是多了一份「工具清單」，讓 LLM 知道它在思考時可以選擇呼叫這些工具。
'''

# 建立工具名稱與實體函數的對照表，方便在 Agent 控制循環中快速查找並呼叫
tools_map = {tool.name: tool for tool in tools}

# ==========================================================
# === ⚙️ 核心模組 3：紅方 Agent 核心控制循環 (Control Loop) ===
# ==========================================================

def run_red_agent_loop(user_question: str):
    """
    Agent 運作的核心入口。接收使用者的提問，驅動大腦思考、呼叫外部工具並進行最終分析。
    """
    print(f"\n=== ☠️ 收到紅方指令：'{user_question}' ===")
    
    # 建立對話上下文歷史：將組裝好的 system_instruction 放入 SystemMessage，強制約束大腦
    messages = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=user_question)
    ]
    
    # 【第一步：紅方大腦思考 (Reasoning)】
    print("🧠 [紅方大腦] 正在分析攻擊策略並規劃工具調用...")
    ai_response = llm_with_tools.invoke(messages)
    ''' 
    當你執行 llm_with_tools.invoke(messages) 時：
    呼叫對象:llm_with_tools 的本體就是 LLM 推論引擎。
    底層動作:LangChain 會把 messages 轉換成特定格式(JSON)，並透過 HTTP 請求發送給 Ollama 程式。
    模型推論:Ollama 收到請求後，載入 llama3.2:3b 的權重檔案，進行數學運算（推論），產出回應。
    --------------------------------------------------------------------------------------
    根據原始碼定義與流程，invoke()的核心功能包括：
    單次任務執行：它是 LangChain 中最常用的同步呼叫介面，接受一個輸入並回傳一個輸出。  
    模型推論：當對象是 llm 時，invoke()會根據傳入的 Prompt 生成回應文字。  
    工具觸發：當對象是 tool（例如 tools_map[tool_name].invoke(tool_args)）時，
             它會實際執行該工具函數的程式碼邏輯（例如在背景啟動子程序執行 Garak 掃描）。
    '''
    
    # 判斷大腦是否決定調用工具 (Function Calling)
    if ai_response.tool_calls:
        for tool_call in ai_response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            print(f"👉 [紅方決策] 決定使用武器: '{tool_name}'")
            print(f"📦 [武器參數] 攻擊配置: {tool_args}")
            
            ''' 
            簡單來說，當 LLM 判斷它無法僅憑自身的知識回答問題(例如需要執行 Garak 掃描或查詢保險庫機密)，
            它就不會回傳普通的文字，而是回傳一個包含工具名稱與參數的結構化指令，這就是 tool_calls。
            以下為tool_calls 的結構例子:
            [
                {
                    "name": "execute_garak_attack",
                    "args": {
                    "attack_type": "promptinject.HijackHateHumans",
                    "target_model": "ollama/tinydolphin"
                    },
                    "id": "call_abc123"
                }
            ]
            '''
            
            # 【第二步：Agent 執行 (Acting)】
            if tool_name in tools_map:
                # 實際呼叫 tools.py 中定義的外部工具（例如：subprocess 呼叫 Garak 掃描）
                action_result = tools_map[tool_name].invoke(tool_args)
                
                # 【第三步：紅方大腦最終分析 (Observation & Response)】
                print("🧠 [紅方大腦] 正在閱讀 Garak 攻擊報告，分析漏洞風險...")
                
                # 將工具傳回的解析結果與原始問題包裝成 prompt，再次詢問 LLM 進行專業分析
                final_prompt = f"""
                使用者問題：{user_question}
                
                Garak 工具回傳的攻擊報告總結：
                {action_result}
                
                請根據使用者問題與工具報告，以專業駭客思維進行最終的漏洞風險分析。
                如果工具回傳的內容是錯誤訊息（例如 usage 錯誤），請直接指出工具執行失敗的原因，不要捏造模型漏洞。
                """
                
                # 大腦產出最終的文字分析
                final_response = llm.invoke([HumanMessage(content=final_prompt)])
                
                # 💡 1. 終端機顯示：輸出大腦產出的初版分析報告
                print("\n" + "="*40)
                print("💡 [紅方大腦分析結果（初版）]")
                print("="*40)
                print(final_response.content)
                
                # 💡 2. 終端機顯示：輸出 Garak 原始報告內容（供攻擊者比對驗證）
                print("\n" + "="*40)
                print("🔬 [攻擊者驗證區] Garak 原始回傳內容")
                print("="*40)
                print(action_result)
                print("="*40)
                
                # 💡 3. 本地儲存：自動匯出成 Markdown 檔，方便團隊留存紀錄與撰寫專題報告
                report_filename = "red_attack_analysis_v1.md"
                with open(report_filename, "w", encoding="utf-8") as f:
                    f.write(f"# 紅方 Agent 攻擊分析報告 (對照版)\n\n")
                    f.write(f"## 1. 大腦分析結果\n{final_response.content}\n\n")
                    f.write(f"## 2. Garak 原始報告內容\n```text\n{action_result}\n```")
                
                print(f"\n💾 已將分析與原始報告匯出至 `{report_filename}`。")
                return
    else:
        # 如果大腦認為不需要呼叫工具，則直接以純文字回應使用者
        print(f"\n💡 [紅方直接回答]：\n{ai_response.content}")

# ==========================================================
# === 🎯 測試區 ===
# ==========================================================
if __name__ == "__main__":
    # 啟動紅方 Agent，測試其是否能精準查閱手冊並轉譯成正確參數呼叫武器
    # run_red_agent_loop("我想對靶機 tinydolphin 進行 HijackHateHumans 提示詞注入測試，請發動攻擊。")
    print("我可以正常執行")