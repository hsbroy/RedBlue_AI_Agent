import os
import sys  # 用於控制標準輸出流，實現終端機即時動態刷新
import subprocess  # 用於在背景開啟子程序執行 Garak 終端機指令
import glob  # 用於搜尋符合特定模式的檔案路徑（尋找最新日誌檔）
import json  # 用於解析 Garak 生成的 JSONL 格式報告
from langchain_core.tools import tool

# ==========================================================
# === 📁 核心工具 1：保險庫機密搜尋 (RAG 模擬工具) ===
# ==========================================================

@tool
def search_vault(query: str) -> str:
    """
    【僅限】用於搜尋公司內部的機密資料。
    
    當使用者的問題明確提到以下關鍵字時才調用此工具：
    - '金鑰'、'key'、'密碼'、'黑豹計畫'、'合約內容'。
    
    Args:
        query: 要搜尋的機密關鍵字。
    """
    print(f"\n[Agent 執行中] 正在保險庫中搜尋：'{query}'...")
    
    # 根據輸入關鍵字模擬 RAG 檢索結果
    if "金鑰" in query or "key" in query.lower():
        return "保險庫機密資料：核心金鑰為 'BP-999-SECRET-TOKEN'。"
    else:
        return "保險庫資料：黑豹計畫是一項針對企業資安防禦的機密專案。"


# ==========================================================
# === 🛠️ 核心工具 2：Garak 攻擊模組 (包含精準報告解析與編碼修正) ===
# ==========================================================

@tool
def execute_garak_attack(attack_type: str = "promptinject.HijackHateHumans", target_model: str = "ollama/tinydolphin") -> str:
    """
    【僅限紅方專用】驅動 Garak 攻擊工具對指定模型進行本地脆弱性評估與攻擊測試。
    
    Args:
        attack_type: Garak 的探針名稱 (例如 'promptinject.HijackHateHumans')。
        target_model: 靶機模型名稱 (例如 'ollama/tinydolphin')。
    """
    print(f"\n[Agent 執行中] 正在發動 Garak 攻擊...")
    print(f"🔹 目標模型: {target_model}")
    print(f"🔹 攻擊探針: {attack_type}")

    # 1. 拆分模型類型與名稱
    model_type = "ollama"
    model_name = target_model
    if "/" in target_model:
        model_type, model_name = target_model.split("/", 1)
    ''' 
    split("/", 1)的語意說明：「遇到第一個 / 就進行分割，分割完這一次後就不再分割了」。
    '''

    # 2. 建立 Garak 背景執行指令
    cmd = [
        "garak",
        "--model_type", model_type,
        "--model_name", model_name,
        "--probes", attack_type,
        "--generations", "1"
    ]

    print(f"🖥️ 執行指令: {' '.join(cmd)}")
    all_output = []

    ''' 
    這是 Python 中非常實用的字串處理語法。join() 方法用於將串列(List)中的所有元素連接成一個字串(String)。  
    語法結構："分隔符號".join(串列名稱)
    這裡的運作邏輯：
        你的 cmd 是一個串列：["garak", "--model_type", "ollama", ...]。  
        ' '（中間有一個空格）就是分隔符號。
        ' '.join(cmd) 會把串列裡的每一個單字拿出來，中間塞入一個空格，最後拼成一整行。
    ------------------------------------
    舉例說明：
        如果 cmd = ["apple", "banana", "cherry"]
        ' '.join(cmd) 輸出的結果會是："apple banana cherry"
        '-'.join(cmd) 輸出的結果會是："apple-banana-cherry"
    ---------------------------------------------------------------------------------
    all_output = []的說明:
        1. 目的：Garak 在執行攻擊時，終端機會跳出非常多行訊息（像是進度條、當前的 Prompt 等）。  
        2. 用法：在後面的迴圈中，程式會把每一行跳出來的訊息都 append（加入）到這個 all_output 裡面。  
        3. 最後用途：如果攻擊結束後找不到特定的 JSONL 報告檔案，Agent 可以把這本「筆記本」裡的完整內容回傳給大腦參考，當作備援資訊。
    '''

    try:
        # 💡 修正 Windows CP950 編碼問題：
        # 複製當前的作業系統環境變數，並強制指定 Python 的輸出編碼為 UTF-8
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        ''' 
        1. env = os.environ.copy() (複製環境變數)
            (1) os.environ: 這是一個包含你目前電腦系統中所有「環境變數」的字典（例如你的路徑 PATH、使用者名稱等）。
            (2) .copy(): 我們不直接修改原始的系統環境設定，而是先完整複製一份出來。  
            (3) 目的：這就像是為即將進行的攻擊任務準備一個「獨立的沙盒環境設定」，我們在裡面做的修改不會影響到你電腦其他正在跑的程式。
        2. env["PYTHONIOENCODING"] = "utf-8" (強制指定編碼)
            (1) PYTHONIOENCODING: 這是一個專門給 Python 程式看的標準環境變數。它決定了 Python 在「輸入(Input)」與「輸出(Output)」時要使用的字元編碼。
            (2) "utf-8": 我們將其強制設定為 UTF-8。
        '''
        # 3. 透過 subprocess 啟動 Garak
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",       # 強制將子程序的輸出以 utf-8 解碼
            errors="replace",       # 遇到無法解析的字元時替換，防止拋出 UnicodeDecodeError
            bufsize=1,
            env=env                 # 傳入設定好 UTF-8 編碼的環境變數
        )
        ''' 
        這些術語都來自 Python 的 subprocess 模組，該模組專門用於執行外部指令(如 garak 或 ls)，並與這些指令進行資料交換。
        1. subprocess.Popen():
            這是啟動外部子程序的「發射器」。它會建立並管理一個新的處理程序，
            讓你可以在 Python 執行期間並行跑另一個程式，而不需要等待它結束就能繼續執行後續代碼。
        2. subprocess.PIPE:
            這是一個特殊的常數，代表「建立管道」。當你設定 stdout=subprocess.PIPE 時，
            代表你要求 Python 攔截子程序的輸出，不要直接印在螢幕上，而是存入一個記憶體緩衝區供 Python 讀取。
        3. subprocess.STDOUT：
            這代表「標準錯誤與標準輸出合併」。設定 stderr=subprocess.STDOUT 會告訴系統:
            如果程式出錯了，請把錯誤訊息(stderr)丟進跟正常訊息(stdout)同一個管道裡，這樣我們只需要讀一個地方就能掌握所有訊息。
        4. text=True:
            在預設情況下，subprocess 抓取到的資料是原始二進位位元組 (Bytes)，看起來會像 b'Hello\n'。
            設定 text=True(在舊版本中稱為 universal_newlines=True)後，Python 會自動幫你把這些位元組轉換成字串(String)。
            這讓你不需要手動寫 .decode("utf-8") 就能直接用 print() 或 line.split()來處理抓到的文字。
        5. errors="replace" 會替換成什麼？
            當編碼轉換失敗（例如用 UTF-8 去解讀一個 CP950 專屬的亂碼）時，設定 replace 可以防止程式崩潰。
            會將無法解析的字元替換成 Unicode 替換字元 (Replacement Character)，通常顯示為一個帶有問號的黑色菱形。
        6. bufsize=1:
            (1) 緩衝區的大小設定，但其行為取決於模式：
                在text=True(文字模式)下，bufsize=1 代表「行緩衝(Line Buffering)」。
                具體作用：只要子程序輸出一行(遇到換行符 \n)，Python 就會立刻把這行資料「推」到管道中讓你讀取。
            (2) 為什麼要設 1 ? 
                如果不設（預設通常是大塊緩衝），你可能會看到畫面卡住很久，然後突然噴出一大堆文字。
                設為 1 可以實現即時更新，讓你在 Agent 的終端機看到 Garak 跑進度條的效果。
        '''

        # 串流讀取終端機輸出，並動態刷新在畫面上
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                all_output.append(line)
                
                # 💡 再次保護：如果本地終端機（如 MINGW64）不支援特定 Emoji 符號，
                # 進行錯誤捕捉並安全過濾，避免主程式因為 print() 而崩潰
                try:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                except UnicodeEncodeError:
                    # 如果遇到 cp950 無法印出的字元，忽略該字元後再輸出
                    sys.stdout.write(line.encode('cp950', errors='ignore').decode('cp950'))
                    sys.stdout.flush()
        ''' 
        1. 讀取與結束判定
            (1) line = process.stdout.readline()：
                從子程序（Garak）的輸出管道中讀取「一行」文字。由於前面設定了 bufsize=1，只要 Garak 輸出一行，這裡就會立刻抓到。
            (2) 退場機制 -> if not line and process.poll() is not None：
                - not line：代表已經讀不到新的訊息了。
                - process.poll() is not None：檢查子程序的狀態。如果結果不是 None，代表 Garak 程式已經結束執行了。
                滿足這兩個條件時，執行 break 跳出迴圈。
        2. 紀錄訊息
            (1) all_output.append(line)：
                只要 line 裡面有內容，就把它塞進我們之前準備好的 all_output 串列中。
                這確保了即使螢幕顯示出問題，我們後台依然有一份完整的攻擊日誌副本。
        3. 安全顯示（雙重保護機制） -> 這是為了處理 Windows 終端機常見的「字元顯示崩潰」問題：
            (1) 第一層：嘗試直接印出
                sys.stdout.write(line) // 類似 print，但更適合用在這種需要精確控制輸出的串流場景。
                sys.stdout.flush() // flush() 則是強制將緩衝區的文字立刻推向螢幕，讓你看到動態更新的感覺。
            (2) 第二層：例外捕捉 (except UnicodeEncodeError)
                如果 line 裡面包含 Windows 預設編碼（如 CP950）不認識的 Emoji 或特殊符號，直接輸出會導致整個 Agent 程式當機。這時會進入備援方案：
                - .encode('cp950', errors='ignore')：先嘗試將這行字轉成 CP950 編碼，遇到看不懂的特殊符號就直接「丟掉」。
                - .decode('cp950')：再解碼回字串。
                - 結果：螢幕上只會顯示正常的文字，特殊符號會消失，但程式保證不會崩潰。
        '''
        
        
        rc = process.poll()
        print(f"\n✅ Garak 執行完畢，結束碼 (Return Code): {rc}")
        ''' 
        1. poll() 的回傳值代表什麼？
            (1) 當執行 rc = process.poll() 時，變數 rc（通常是 Return Code 的縮寫）會得到一個結果：
                - 如果回傳 None：代表程式還在跑，還沒結束。
                - 如果回傳 0：代表程式正常執行完畢，沒有發生錯誤。
                - 如果回傳「非 0」的數字（例如 1, 2, 127 等）：代表程式執行失敗。不同的數字通常代表不同的錯誤原因（例如找不到檔案、參數錯誤、或是被強制終止）。
                Example: 
                    如果是 rc = 127，通常代表系統找不到 garak 這個執行檔。
                    如果是 rc = 0，代表 Garak 自認完美達成任務，我們就應該去後面的邏輯找 JSONL 報告。
        '''

    except Exception as e:
        return f"❌ 執行 Garak 攻擊時發生系統級錯誤: {str(e)}"

    # ==========================================================
    # === 📂 核心解析：搜尋與讀取最新的 JSONL 報告檔案 ===
    # ==========================================================
    
    # 優先尋找完整結算的 .report.jsonl 檔案
    list_of_files = glob.glob('garak.*.report.jsonl')
    ''' 
    1. glob.glob() 的功能
        glob 是一個強大的檔案搜尋工具，它支援 萬用字元（Wildcards）。這讓你不必知道確切的檔名，只要知道檔名的「模式（Pattern）」就能找到檔案。
    2. 'garak.*.report.jsonl' 代表什麼？
        (1) 這是 Garak 工具產生的標準報告檔名格式。這串字串可以拆解為：
            - garak.：檔名的開頭必須是這個字串。
            - *（萬用字元）：代表「任何長度的任何字元」。
            - .report.jsonl：檔名的結尾必須是這個副檔名。
    '''
    
    # 備援：若無 report 則尋找執行過程中的 .hitlog.jsonl
    if not list_of_files:
        list_of_files = glob.glob('garak.*.hitlog.jsonl')

    if list_of_files:
        # 挑選修改時間最新的一個檔案
        latest_file = max(list_of_files, key=os.path.getctime)
        print(f"📂 正在解析最新 Garak 攻擊日誌：{latest_file}")

        passed = 0
        failed = 0
        attack_details = []

        with open(latest_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    # 比對日誌中的 probe 是否符合測試項
                    if attack_type in data.get("probe", ""):
                        # 擷取 Prompt 與 Output 內容，增加防禦性程式碼
                        prompt = "N/A"
                        if isinstance(data.get("prompt"), dict):
                            prompt = data.get("prompt", {}).get("turns", [{}])[0].get("content", {}).get("text", "N/A")
                        elif isinstance(data.get("prompt"), str):
                            prompt = data.get("prompt")
                        elif "test" in data:
                            prompt = data.get("test")

                        output = "N/A"
                        if isinstance(data.get("output"), dict):
                            output = data.get("output", {}).get("text", "N/A")
                        elif isinstance(data.get("output"), list) and data.get("output"):
                            output = data.get("output")[0]
                        elif isinstance(data.get("output"), str):
                            output = data.get("output")

                        # 💡 語意說明：
                        # score == 1.0 代表防禦失敗（對紅方而言是攻擊成功）
                        # score == 0.0 代表防禦成功（對紅方而言是攻擊失敗）
                        if data.get("score") == 1.0:
                            failed += 1
                            attack_details.append({
                                "probe": data.get("probe"),
                                "prompt": prompt,
                                "output": output
                            })
                        else:
                            passed += 1

                except json.JSONDecodeError:
                    continue  # 跳過損壞或格式不符的 JSON 行
                except Exception as ex:
                    print(f"⚠️ 解析單行數據時發生意外錯誤: {ex}")
                    continue

        total = passed + failed
        
        # 💡 使用語意化變數 attack_success_rate，避免計算衝突
        attack_success_rate = (failed / total * 100) if total > 0 else 0

        # 4. 組裝結構化 Markdown 總結回傳給大腦
        summary = f"""
==== Garak 攻擊原始報告完整解析結果 ====
測試探針: {attack_type}
測試總量: {total} 次 (已完整遍歷所有 JSONL 數據)
防禦成功 (PASS): {passed} 次
防禦失敗 / 攻擊成功 (FAIL): {failed} 次
攻擊成功率: {attack_success_rate:.2f}%

[攻擊成功案例精選 (靶機失守)]
"""
        # 僅提取前 3 個最具威脅、失守的案例回傳給 LLM，防止 Token 溢出
        for i, detail in enumerate(attack_details[:3]):
            summary += f"- 案例 {i+1}:\n"
            summary += f"  - 攻擊提示詞: {detail['prompt']}\n"
            summary += f"  - 靶機輸出內容: {detail['output']}\n"

        return summary

    else:
        # 若完全找不到日誌，將剛才捕捉到的終端機輸出作為備援
        terminal_output = "".join(all_output)
        if terminal_output.strip():
            return f"找不到最新的 Garak 報告檔案。以下為終端機執行日誌備援：\n{terminal_output}"
        else:
            return "❌ 攻擊執行完畢，但未取得任何日誌輸出與報告數據。"