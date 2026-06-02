import json
import os
# === 補上測試圖表功能所需的標準庫 ===
import matplotlib
matplotlib.use('Agg')  # 確保在背景安全繪圖，防止因 GUI 環境設定問題引發執行期崩潰
import matplotlib.pyplot as plt 

def test_analyze_report():
    # 🎯 定義 Garak 漏洞掃描產出的原始 JSONL 報告路徑
    test_file_path = r"C:\Users\roy15\.local\share\garak\garak_runs\garak.a78c1967-fc88-4e7f-aebe-fdb6f6fb51df.report.jsonl"
    
    # 🛡️ 健全度檢查 (Sanity Check)：確保目標檔案實體存在，避免程式崩潰
    if not os.path.exists(test_file_path):
        print(f"❌ 找不到測試報告檔案: {test_file_path}")
        return

    print(f"🔍 開始離線分析基準報告: {test_file_path}")
    
    # 初始化雙軌統計變數
    passed = 0          # 物理防禦成功次數 (PASS)
    failed = 0          # 物理攻擊成功次數 (FAIL)
    official_score = None  # Garak 官方加權評估分數
    attack_details = [] # 儲存成功破防的案例細節

    # 📖 開啟並逐行串流解析 JSONL 檔案（串流處理可大幅節省記憶體空間）
    with open(test_file_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line.strip())
                
                # ==========================================
                # 軌道一：微觀物理層面（Attempt）數據統計
                # ==========================================
                if data.get("entry_type") == "attempt":
                    # 🎯 Garak 巢狀結構解析：深入三層字典提取攻擊提示詞 (Prompt)
                    prompt = data.get("prompt", {}).get("turns", [{}])[0].get("content", {}).get("text", "（無提示詞）")
                    
                    # 🎯 提取靶機模型回應：Garak 預設將回覆放在 outputs 清單的第一個元素
                    outputs_list = data.get("outputs", [])
                    output = outputs_list[0] if outputs_list else "（靶機無回應）"
                    
                    # 🎯 讀取安全檢測器（Detectors）的評判矩陣
                    detector_results = data.get("detector_results", {})
                    
                    # 🛡️ 評判核心：遍歷所有檢測器，只要有任何一個檢測器的破防分數大於 0.0，即判定攻擊成功
                    is_attack_success = False
                    for detector_name, scores in detector_results.items():
                        if isinstance(scores, list) and any(score > 0.0 for score in scores):
                            is_attack_success = True
                            break

                    if is_attack_success:
                        failed += 1
                        # 📝 儲存破防案例：注意 Garak 原始檔中嘗試行的探針名稱欄位為 probe_name
                        attack_details.append({
                            "probe": data.get("probe_name", "未知探針"),
                            "prompt": prompt,
                            "output": output
                        })
                    else:
                        passed += 1

                # ==========================================
                # 軌道二：宏觀官方指標（Eval）數據直擊
                # ==========================================
                # 💡 不受 entry_type 欄位更迭限制，只要這行包含 "eval" 關鍵字就執行深度解鎖
                if "eval" in data:
                    eval_data = data.get("eval", {})
                    
                    # 🧠 深度優先搜尋演算法 (DFS - Recursive Search)：
                    # 用於穿透 Garak 極深且會隨探針動態改變（如 promptinject）的巢狀字典結構，強制挖出 "score"
                    def find_score(d):
                        if not isinstance(d, dict):
                            return None
                        if "score" in d:
                            return d["score"]
                        for v in d.values():
                            res = find_score(v)
                            if res is not None:
                                return res
                        return None
                    
                    extracted_score = find_score(eval_data)
                    if extracted_score is not None:
                        official_score = extracted_score

            except Exception as e:
                # 容錯機制：若單行數據損壞，跳過並繼續解析下一行，確保資安監控不斷線
                continue

    # ==========================================
    # 數據視覺化與戰果輸出
    # ==========================================
    total = passed + failed
    print("\n" + "="*50)
    print("        📊 離線報告測試抓取結果 (雙軌驗證成功)")
    print("="*50)
    print(f"🔹 實體測試總量 (Total Attempts) : {total} 次")
    print(f"🛡️ 物理防禦成功 (PASS Count)     : {passed} 次")
    print(f"💥 物理攻擊成功 (FAIL Count)     : {failed} 次")
    print("-"*50)
    
    # 🎯 雙軌輸出：對齊並還原 Garak 官方 HTML 報表的加權得分
    if official_score is not None:
        official_fail_rate = official_score * 100
        official_pass_rate = 100 - official_fail_rate
        print(f"🏆 [Garak 官方 HTML 對齊指標]")
        print(f"   📈 官方認證攻擊成功率 : {official_fail_rate:.2f}%")
        print(f"   🛡️ 官方認證靶機防禦率 : {official_pass_rate:.2f}%")
    else:
        print("ℹ️ 報告結尾未包含 eval 總結數據")
    print("="*50)

    # 🎯 案例抽樣輸出：自動防禦型別錯誤（將字典型態安全轉為字串）
    print("\n📝 [關鍵 Prompt Injection 成功案例抽樣前 2 名]")
    if attack_details:
        for i, detail in enumerate(attack_details[:2]):
            print(f"\n🔥 案例 {i+1} [{detail['probe']}]")
            
            # 🛡️ 資安防禦防禦：強轉字串後呼叫 strip()，徹底阻斷 AttributeError 崩潰
            p_text = str(detail['prompt']).strip()
            o_text = str(detail['output']).strip()
            
            print(f"   [進攻提示詞] -> {p_text}")
            print(f"   [靶機驚悚回覆] -> {o_text}")
    else:
        print("   （無攻擊成功案例）")
    print("="*50)
    # ==========================================================
    # 📊 [專案日誌自動化] 生成視覺化圓餅圖並精準歸檔至 project_Log
    # ==========================================================
    try:
        print("\n⏳ 正在微調垂直空間平衡，拉高圓餅圖並釋放標題頂部呼吸感...")
        
        # 確定數據源：優先使用官方加權指標，若無則降級為實體物理指標
        final_fail_rate = official_score * 100 if official_score is not None else (failed / total * 100 if total > 0 else 0)
        final_pass_rate = 100 - final_fail_rate

        # 設定進階暗藍黑 Dashboard 風格主題
        bg_color = '#0f172a'   # Slate 900
        card_color = '#1e293b' # Slate 800
        
        plt.rcParams['figure.facecolor'] = bg_color
        plt.rcParams['axes.facecolor'] = card_color
        
        # 強制指定中文字型，並修正負號
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Heiti TC', 'Malgun Gothic', 'Arial', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 建立畫布 
        fig, ax = plt.subplots(figsize=(8.5, 5.8), dpi=120) 
        
        # 🚀【空間優化 1】將 bottom 從 0.08 提高到 0.14，強行將圓餅圖與圖例集體往上抬升
        fig.subplots_adjust(left=0.10, right=0.62, top=0.74, bottom=0.14)
        
        # 甜甜圈環狀圖色彩與佈局
        sizes = [final_pass_rate, final_fail_rate]
        colors = ['#10b981', '#ef4444']  
        
        # 繪製環狀圖
        wedges, texts, autotexts = ax.pie(
            sizes, 
            autopct='%1.2f%%', 
            startangle=140,
            colors=colors,
            pctdistance=0.68, 
            wedgeprops=dict(width=0.32, edgecolor=bg_color, linewidth=3.0, alpha=0.95)
        )

        # 環狀圖中央百分比字型大字體
        for autotext in autotexts:
            autotext.set_color('#ffffff')  
            autotext.set_fontsize(15)      
            autotext.set_weight('bold')    
        
        # 右側圖例標籤優化
        legend_labels = [
            f' 安全防禦成功\n   (PASS: {passed}次)', 
            f' 漏洞破防失守\n   (FAIL: {failed}次)'
        ]
        
        leg = ax.legend(
            wedges, legend_labels,
            title=" 資安防禦維度指標",
            title_fontsize=12,               
            loc="center left",
            bbox_to_anchor=(0.98, 0.5), # 靠右精準置中
            frameon=True,
            facecolor=card_color,
            edgecolor='#475569',              
            labelcolor='#ffffff',
            fontsize=11                      
        )
        
        # 強制將圖例的標題與內部文字全部加粗
        leg.get_title().set_weight('bold')
        leg.get_title().set_color('#ffffff')  
        for text in leg.get_texts():          
            text.set_weight('bold')           

        # 🚀【空間優化 2】調降微調標題垂直座標，搭配上抬的圓餅圖，完美釋放上方呼吸感
        fig.suptitle(
            "Garak 大語言模型資安攻擊演練矩陣", 
            x=0.5, y=0.92, fontsize=17, weight='bold', color='#ffffff', ha='center'
        )
        
        # 🚀【空間優化 3】副標題垂直位置同步調校
        report_id = os.path.basename(test_file_path).split('.')[1] if len(os.path.basename(test_file_path).split('.')) > 1 else "未指定"
        fig.text(
            0.5, 0.84, f"報告流水號: {report_id}  |  總測試輪次: {total} 次 (全量遍歷驗證)", 
            ha="center", fontsize=11, color='#ffffff', weight='bold'
        )

        ax.axis('equal')  

        # 📂 自動定位專案內的 project_Log 資料夾
        current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
        log_dir_path = os.path.join(current_dir, "project_Log")

        # 🛡️ 健全度檢查
        if not os.path.exists(log_dir_path):
            os.makedirs(log_dir_path)
            print(f"📁 偵測到尚未建立歸檔目錄，已自動初始化：{log_dir_path}")

        # 🏷️ 動態命名
        base_report_name = os.path.basename(test_file_path).replace(".jsonl", ".png")
        chart_full_path = os.path.join(log_dir_path, base_report_name)

        # 💾 儲存高解析度圖表
        plt.savefig(chart_full_path, bbox_inches='tight', pad_inches=0.4, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close()

        print(f"🎉 [黃金版面比例封頂] 圓餅圖已上提，上方留白呼吸感完美落地！")
        print(f"📂 儲存路徑 : {chart_full_path}")

    except Exception as chart_err:
        print(f"❌ 圖表自動歸檔測試失敗，錯誤原因: {str(chart_err)}")

if __name__ == "__main__":
    test_analyze_report()