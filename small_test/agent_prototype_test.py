import os
from dotenv import load_dotenv

# 1. 載入環境變數並解決 SSL 憑證報錯問題
load_dotenv(override=True)

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from skills.red_tools import search_vault

# 💡 這裡保留兩個 llm：
# llm: 純粹的大腦，用來做最後的總結回答
llm = ChatOllama(model="llama3.2:3b", temperature=0)

# llm_with_tools: 綁定工具的大腦，專門用來判斷要不要用工具
tools = [search_vault]
llm_with_tools = llm.bind_tools(tools)

tools_map = {tool.name: tool for tool in tools}

def run_agent_loop(user_question: str):
    print(f"\n=== 📥 收到使用者問題：'{user_question}' ===")
    
    # 建立對話紀錄
    messages = [HumanMessage(content=user_question)]
    
    # 【第一步：大腦思考 (Reasoning)】
    ai_response = llm_with_tools.invoke(messages)
    
    # 檢查大腦是否要求呼叫工具
    if ai_response.tool_calls:
        for tool_call in ai_response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            print(f"🧠 [大腦決策] 決定呼叫工具: '{tool_name}'")
            print(f"📦 [參數解析] 提取出參數: {tool_args}")
            
            # 【第二步：身體行動 (Acting)】
            if tool_name in tools_map:
                print(f"⚙️ [身體執行] 正在驅動 Python 腳本 `{tool_name}.py`...")
                
                # 執行 Python 函數
                action_result = tools_map[tool_name].invoke(tool_args)
                print(f"📄 [執行結果] 工具回傳內容: {action_result}")
                
                # ==========================================
                # 【第三步：大腦最終思考 (Observation & Response)】
                # 💡 終極修正：把對話歷史「扁平化」
                # ==========================================
                print("🧠 [大腦閱讀結果] 正在整合工具結果，生成最終回答...")
                
                # 我們把問題與工具拿到的資料，結合成一個最單純的提示詞
                final_prompt = f"""
                使用者問題：{user_question}
                
                系統檢索到的參考資料：
                {action_result}
                
                請根據上述的參考資料，直接回答使用者的問題。
                """
                
                # 💡 重點：使用「沒有綁定工具」的原始 llm 來回答，100% 不會輸出空白！
                final_response = llm.invoke([HumanMessage(content=final_prompt)])
                print(f"\n💡 [大腦最終回答]：\n{final_response.content}")
                return
                
            else:
                print(f"⚠️ 找不到名為 {tool_name} 的工具")
    else:
        # 如果不需要呼叫工具，直接印出大腦原本的回答
        print(f"\n💡 [大腦直接回答]：\n{ai_response.content}")

# --- 測試控制循環 ---
run_agent_loop("請問黑豹計畫的核心金鑰是什麼？")