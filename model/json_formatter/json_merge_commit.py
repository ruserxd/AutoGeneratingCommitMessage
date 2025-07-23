import json
import re
from typing import List, Dict, Any

def extract_valuable_content(merge_message: str) -> str:
    """從 merge commit 中提取有價值的內容"""
    lines = merge_message.strip().split('\n')
    valuable_lines = []
    
    for line in lines:
        line = line.strip()
        
        # 跳過無價值的行
        if (line.lower().startswith('merge ') or
            line.startswith('* ') or
            line.startswith('See merge') or
            line.startswith('Closes ') or
            not line):
            continue
        
        # 保留有價值的行
        if (len(line) > 10 and
            not line.startswith('#') and
            not re.match(r'^[a-zA-Z]+/\d+:', line)):
            valuable_lines.append(line)
    
    return '\n'.join(valuable_lines).strip()

def is_merge_commit(commit_message: str) -> bool:
    """檢查是否為 merge commit"""
    if not commit_message:
        return False
    first_line = commit_message.strip().split('\n')[0].strip()
    return first_line.lower().startswith('merge')

def process_data(input_file: str, output_file: str = None, strategy: str = 'extract'):
    """
    處理資料檔案
    
    Args:
        input_file: 輸入檔案
        output_file: 輸出檔案 (可選)
        strategy: 'remove' 或 'extract'
    """
    # 設定輸出檔案名
    if output_file is None:
        if strategy == 'extract':
            output_file = input_file.replace('.json', '_processed.json')
        else:
            output_file = input_file.replace('.json', '_no_merge.json')
    
    # 讀取資料
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    processed_data = []
    changes_count = 0
    
    print(f"處理檔案: {input_file}")
    print(f"總資料: {len(data)} 筆")
    print("=" * 60)
    
    for i, item in enumerate(data):
        if 'output' in item and is_merge_commit(item['output']):
            if strategy == 'remove':
                # 移除策略：跳過此項
                print(f"🗑️  移除第 {i+1} 筆 (Merge commit)")
                continue
            
            elif strategy == 'extract':
                # 提取策略：提取有價值內容
                original = item['output']
                extracted = extract_valuable_content(original)
                
                if extracted:
                    # 有提取到內容，保留並修改
                    new_item = {
                        'input': item['input'],
                        'output': extracted
                    }
                    processed_data.append(new_item)
                    changes_count += 1
                    
                    print(f"✏️  修改第 {i+1} 筆:")
                    print(f"   原始: {original}")
                    print(f"   修改: {extracted}")
                    print("-" * 50)
                else:
                    # 沒有提取到內容，移除
                    print(f"🗑️  移除第 {i+1} 筆 (無有價值內容)")
        else:
            # 非 merge commit，直接保留
            processed_data.append({
                'input': item['input'],
                'output': item['output']
            })
    
    # 儲存結果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print(f"處理完成:")
    print(f"  原始資料: {len(data)} 筆")
    print(f"  處理後: {len(processed_data)} 筆")
    print(f"  修改內容: {changes_count} 筆")
    print(f"  移除資料: {len(data) - len(processed_data)} 筆")
    print(f"  儲存至: {output_file}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("python3 process_merge.py input.json [strategy]")
        print("strategy: extract (預設) 或 remove")
        sys.exit(1)
    
    input_file = sys.argv[1]
    strategy = sys.argv[2] if len(sys.argv) > 2 else 'extract'
    
    if strategy not in ['extract', 'remove']:
        print("錯誤: strategy 必須是 'extract' 或 'remove'")
        sys.exit(1)
    
    try:
        process_data(input_file, strategy=strategy)
    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 {input_file}")
    except json.JSONDecodeError:
        print(f"錯誤: {input_file} 不是有效的 JSON 檔案")
    except Exception as e:
        print(f"錯誤: {str(e)}")