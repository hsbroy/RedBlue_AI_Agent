import json
import os
# === 補上測試圖表功能所需的標準庫 ===
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
    # 📊 [互動式圖表測試] 彈出內建儲存按鈕的視覺化圓餅圖視窗
    # ==========================================================
    try:
        print("\n⏳ 正在啟動 Matplotlib 互動式視窗，請查看彈出的圖表...")
        
        # 確定數據源：優先使用官方加權指標，若無則降級為實體物理指標
        final_fail_rate = official_score * 100 if official_score is not None else (failed / total * 100 if total > 0 else 0)
        final_pass_rate = 100 - final_fail_rate

        # 建立畫布與圓餅圖設定
        plt.figure(num="Garak 資安演練戰果圖表", figsize=(6, 5), dpi=100)
        labels = ['Defense Success (PASS)', 'Vulnerability Exploited (FAIL)']
        sizes = [final_pass_rate, final_fail_rate]
        colors = ['#2ecc71', '#e74c3c']  # 專業資安紅綠配色
        explode = (0.05, 0)  # 微調凸顯防禦成功率

        plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.2f%%', shadow=True, startangle=140,
                textprops={'fontsize': 10, 'weight': 'bold'})
        
        # 加上大標題
        plt.title("Garak Security Scan Report Matrix\n(Click disk icon below to download/save)", fontsize=11, weight='bold', pad=20)
        plt.axis('equal')  # 確保圓餅圖比例平衡

        # 🚀 核心關鍵：彈出互動式視窗，視窗工具列自帶「儲存 (Save)」按鍵
        plt.show()
        
        print("🎉 [Matplotlib 彈窗關閉] 使用者已完成圖表檢視與下載測試。")

    except Exception as chart_err:
        print(f"❌ 圖表彈窗測試失敗，錯誤原因: {str(chart_err)}")

if __name__ == "__main__":
    test_analyze_report()