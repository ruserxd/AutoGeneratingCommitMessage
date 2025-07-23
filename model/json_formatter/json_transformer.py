import json
import sys
import os
from pathlib import Path

def transform_json_format(input_file, output_file=None, use_commit_message=True):
    """
    轉換 JSON 格式
    
    從：
    {
        "input": "...",
        "output": {
            "why": "...",
            "commit_message": "..."
        }
    }
    
    到：
    {
        "input": "...",
        "output": "..."
    }
    
    Args:
        input_file: 輸入檔案路徑
        output_file: 輸出檔案路徑 (如果為 None，會自動生成)
        use_commit_message: True=使用commit_message, False=使用why
    """
    
    # 檢查輸入檔案是否存在
    if not os.path.exists(input_file):
        print(f"❌ 錯誤：找不到檔案 '{input_file}'")
        return False
    
    # 自動生成輸出檔案名稱
    if output_file is None:
        input_path = Path(input_file)
        suffix = "_commit_message" if use_commit_message else "_why"
        output_file = str(input_path.parent / f"{input_path.stem}{suffix}.json")
    
    print(f"📖 讀取檔案: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ 錯誤：JSON 格式不正確 - {e}")
        return False
    except Exception as e:
        print(f"❌ 錯誤：讀取檔案失敗 - {e}")
        return False
    
    if not isinstance(data, list):
        print(f"❌ 錯誤：JSON 應該是一個陣列格式")
        return False
    
    print(f"📊 原始資料: {len(data)} 筆")
    
    transformed_data = []
    stats = {
        'total': len(data),
        'success': 0,
        'skipped': 0,
        'errors': 0
    }
    
    target_field = 'commit_message' if use_commit_message else 'why'
    print(f"🎯 提取欄位: {target_field}")
    
    for i, item in enumerate(data):
        try:
            # 檢查必要的欄位
            if 'input' not in item:
                if i < 5:  # 只顯示前 5 個錯誤
                    print(f"⚠️  第 {i+1} 筆：缺少 'input' 欄位")
                stats['skipped'] += 1
                continue
                
            if 'output' not in item:
                if i < 5:
                    print(f"⚠️  第 {i+1} 筆：缺少 'output' 欄位")
                stats['skipped'] += 1
                continue
            
            # 獲取 input
            input_text = item['input']
            
            # 處理 output
            output_data = item['output']
            
            # 如果 output 已經是字串，直接使用
            if isinstance(output_data, str):
                output_text = output_data
                if i < 3:  # 顯示前 3 筆的處理過程
                    print(f"✓ 第 {i+1} 筆：output 已經是字串格式")
            
            # 如果 output 是字典，提取所需欄位
            elif isinstance(output_data, dict):
                if target_field in output_data:
                    output_text = output_data[target_field]
                    if i < 3:
                        print(f"✓ 第 {i+1} 筆：成功提取 '{target_field}' 欄位")
                else:
                    if i < 5:
                        available_fields = list(output_data.keys())
                        print(f"⚠️  第 {i+1} 筆：找不到 '{target_field}' 欄位，可用欄位: {available_fields}")
                    stats['skipped'] += 1
                    continue
            else:
                if i < 5:
                    print(f"⚠️  第 {i+1} 筆：output 格式不正確（類型: {type(output_data)}）")
                stats['skipped'] += 1
                continue
            
            # 檢查 output 是否有效
            if not output_text or not str(output_text).strip():
                if i < 5:
                    print(f"⚠️  第 {i+1} 筆：output 內容為空")
                stats['skipped'] += 1
                continue
            
            # 創建新的資料項目
            new_item = {
                'input': input_text,
                'output': str(output_text).strip()
            }
            
            transformed_data.append(new_item)
            stats['success'] += 1
            
            # 顯示前 2 筆的轉換結果詳情
            if i < 2:
                print(f"\n--- 第 {i+1} 筆轉換詳情 ---")
                print(f"Input: {str(input_text)[:80]}...")
                print(f"Output: {str(output_text)[:80]}...")
                print("-" * 40)
                
        except Exception as e:
            if i < 5:
                print(f"❌ 第 {i+1} 筆處理錯誤: {e}")
            stats['errors'] += 1
    
    # 保存轉換後的資料
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transformed_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 轉換完成！")
        print(f"📊 統計結果:")
        print(f"   總筆數: {stats['total']}")
        print(f"   成功轉換: {stats['success']}")
        print(f"   跳過: {stats['skipped']}")
        print(f"   錯誤: {stats['errors']}")
        if stats['total'] > 0:
            print(f"   成功率: {stats['success']/stats['total']*100:.1f}%")
        print(f"💾 結果已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 保存檔案失敗: {e}")
        return False

def analyze_json_structure(file_path):
    """分析 JSON 檔案結構"""
    
    print(f"🔍 分析檔案結構: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 找不到檔案: {file_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON 格式錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 讀取檔案失敗: {e}")
        return False
    
    if not isinstance(data, list):
        print(f"❌ 檔案格式錯誤：應該是陣列格式，實際是 {type(data)}")
        return False
    
    print(f"📊 資料筆數: {len(data)}")
    
    if not data:
        print("❌ 檔案為空")
        return False
    
    # 分析前幾筆資料的結構
    print(f"\n🔍 資料結構分析:")
    
    for i, item in enumerate(data[:3]): 
        print(f"\n--- 第 {i+1} 筆 ---")
        if isinstance(item, dict):
            print(f"   頂層欄位: {list(item.keys())}")
            
            if 'output' in item:
                output_data = item['output']
                if isinstance(output_data, dict):
                    print(f"   output 子欄位: {list(output_data.keys())}")
                    
                    # 顯示每個子欄位的範例內容
                    for key, value in output_data.items():
                        preview = str(value)[:60] + "..." if len(str(value)) > 60 else str(value)
                        print(f"      {key}: {preview}")
                elif isinstance(output_data, str):
                    preview = output_data[:60] + "..." if len(output_data) > 60 else output_data
                    print(f"   output (字串): {preview}")
                else:
                    print(f"   output 類型: {type(output_data)}")
        else:
            print(f"   資料類型: {type(item)}")
    
    return True

def main():
    """主程式"""
    
    if len(sys.argv) < 2:
        print("🔧 JSON 格式轉換工具")
        print("="*50)
        print("使用方式:")
        print("  python script.py <json檔案路徑> [選項]")
        print("")
        print("選項:")
        print("  --commit-message    提取 commit_message 欄位 (預設)")
        print("  --why              提取 why 欄位")
        print("  --output <檔案>     指定輸出檔案路徑")
        print("  --analyze-only     只分析檔案結構，不轉換")
        print("")
        print("範例:")
        print("  python script.py data.json")
        print("  python script.py data.json --why")
        print("  python script.py data.json --output result.json")
        print("  python script.py data.json --analyze-only")
        return
    
    input_file = sys.argv[1]
    
    # 解析命令列參數
    use_commit_message = True
    output_file = None
    analyze_only = False
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--why':
            use_commit_message = False
        elif arg == '--commit-message':
            use_commit_message = True
        elif arg == '--output' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 1
        elif arg == '--analyze-only':
            analyze_only = True
        else:
            print(f"⚠️  未知參數: {arg}")
        i += 1
    
    print("🔧 JSON 格式轉換工具")
    print("="*50)
    
    # 分析檔案結構
    if not analyze_json_structure(input_file):
        return
    
    if analyze_only:
        print("\n📋 只進行結構分析，不執行轉換")
        return
    
    print("\n" + "="*50)
    
    # 執行轉換
    field_name = "commit_message" if use_commit_message else "why"
    print(f"📝 開始轉換（提取 '{field_name}' 欄位）:")
    
    success = transform_json_format(input_file, output_file, use_commit_message)
    
    if success:
        print(f"\n🎉 轉換成功完成！")
    else:
        print(f"\n💥 轉換失敗！")

if __name__ == "__main__":
    main()