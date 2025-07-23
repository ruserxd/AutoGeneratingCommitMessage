import json
import re
import argparse
from typing import Dict, List, Any


def remove_closes_references(commit_message: str) -> str:
  """
  移除 commit message 中的 Closes 相關引用

  支援的格式:
  - Closes #123
  - Closes 1783 (沒有#號)
  - Closes: #456
  - Closes: 789
  - Closes gh-789
  - See gh-17491
  - Closes https://github.com/user/repo/issues/123
  - [Closes #123]
  - gh-456 (獨立出現)
  - 以及各種變體 (close, closed, fix, fixes, resolve, resolves, see)

  Args:
      commit_message: 原始的 commit message

  Returns:
      移除 Closes 引用後的 commit message
  """
  # 定義各種關鍵字的正則表達式模式
  patterns = [
    # 匹配方括號格式: [Closes #123], [Fixes #456], [See #789]
    r'\[(?:closes?|fix(?:es)?|resolves?|see)\s*#?\d+\]',

    # 匹配帶#號格式: Closes #123, See #456
    r'(?:closes?|fix(?:es)?|resolves?|see)\s*:?\s*#\d+',

    # 匹配不帶#號格式: Closes 1783, See 456
    r'(?:closes?|fix(?:es)?|resolves?|see)\s+\d+',

    # 匹配帶冒號格式: Closes: 123, See: 456
    r'(?:closes?|fix(?:es)?|resolves?|see)\s*:\s*\d+',

    # 匹配 gh- 格式: See gh-17491, Closes gh-123
    r'(?:closes?|fix(?:es)?|resolves?|see)\s+gh-\d+',

    # 匹配完整 GitHub URL
    r'(?:closes?|fix(?:es)?|resolves?|see)\s*:?\s*https?://github\.com/[\w\-./]+/(?:issues|pull)/\d+',

    # 匹配獨立的 GitHub issue 引用
    r'\(#\d+\)',

    # 匹配行尾的 issue 引用
    r'\s*#\d+\s*$',

    # 匹配獨立的 gh-數字 格式
    r'\bgh-\d+\b',
  ]

  cleaned_message = commit_message

  # 逐一應用所有模式
  for pattern in patterns:
    cleaned_message = re.sub(pattern, '', cleaned_message,
                             flags=re.IGNORECASE | re.MULTILINE)

  # 清理多餘的空白行和空格
  lines = cleaned_message.split('\n')
  cleaned_lines = []

  for line in lines:
    stripped_line = line.strip()
    if stripped_line:  # 只保留非空行
      cleaned_lines.append(stripped_line)

  # 重新組合，確保格式正確
  result = '\n'.join(cleaned_lines).strip()

  return result


def process_json_data(data: List[Dict[str, Any]]) -> tuple:
  """
  處理 JSON 資料，移除所有 output 欄位中的 Closes 引用

  Args:
      data: 包含訓練資料的 JSON 陣列

  Returns:
      (處理後的資料, 統計信息)
  """
  processed_data = []
  processed_count = 0

  for item in data:
    if 'output' in item:
      original_output = item['output']
      cleaned_output = remove_closes_references(original_output)

      # 保留原始資料結構，只修改 output 欄位
      processed_item = item.copy()
      processed_item['output'] = cleaned_output
      processed_data.append(processed_item)

      # 統計處理的資料筆數
      if original_output != cleaned_output:
        processed_count += 1
    else:
      # 如果沒有 output 欄位，保持原樣
      processed_data.append(item)

  return processed_data, processed_count


def process_file(input_file: str, output_file: str = None) -> None:
  """
  處理 JSON 檔案

  Args:
      input_file: 輸入檔案路徑
      output_file: 輸出檔案路徑（可選，預設會加上 _no_closes 後綴）
  """
  # 設定輸出檔案路徑
  if output_file is None:
    output_file = input_file.replace('.json', '_no_closes.json')

  try:
    # 讀取 JSON 檔案
    with open(input_file, 'r', encoding='utf-8') as f:
      data = json.load(f)

    print(f"📂 載入檔案: {input_file}")
    print(f"📊 總資料筆數: {len(data)}")

    # 處理資料
    processed_data, processed_count = process_json_data(data)

    print(f"🔧 處理了 {processed_count} 筆包含引用的資料")

    # 儲存處理後的資料
    with open(output_file, 'w', encoding='utf-8') as f:
      json.dump(processed_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 處理完成，已儲存至: {output_file}")

    # 顯示處理範例
    if processed_count > 0:
      print(f"\n📝 處理範例:")
      count = 0
      for i, item in enumerate(data):
        if 'output' in item:
          original = item['output']
          cleaned = remove_closes_references(original)
          if original != cleaned and count < 3:  # 顯示前3個範例
            print(f"\n範例 {count + 1}:")
            print(f"原始: {original}")
            print(f"清理: {cleaned}")
            print("-" * 50)
            count += 1

          if count >= 3:
            break

  except FileNotFoundError:
    print(f"❌ 錯誤: 找不到檔案 {input_file}")
  except json.JSONDecodeError:
    print(f"❌ 錯誤: {input_file} 不是有效的 JSON 檔案")
  except Exception as e:
    print(f"❌ 處理過程中發生錯誤: {str(e)}")


def preview_changes(input_file: str, max_examples: int = 10) -> None:
  """
  預覽會被修改的資料

  Args:
      input_file: 輸入檔案路徑
      max_examples: 最大顯示範例數
  """
  try:
    with open(input_file, 'r', encoding='utf-8') as f:
      data = json.load(f)

    print(f"📋 預覽模式 - {input_file}")
    print(f"總資料筆數: {len(data)}")

    changes = []
    for i, item in enumerate(data):
      if 'output' in item:
        original = item['output']
        cleaned = remove_closes_references(original)
        if original != cleaned:
          changes.append((i, original, cleaned))

    print(f"將會處理 {len(changes)} 筆包含引用的資料")

    # 顯示範例
    for i, (idx, original, cleaned) in enumerate(changes[:max_examples]):
      print(f"\n第 {idx + 1} 筆:")
      print(f"原始: {original}")
      print(f"清理: {cleaned}")
      print("-" * 60)

    if len(changes) > max_examples:
      print(f"\n... 還有 {len(changes) - max_examples} 筆類似資料")

  except Exception as e:
    print(f"❌ 預覽失敗: {str(e)}")


def main():
  """主函數"""
  parser = argparse.ArgumentParser(
    description='移除 Git commit message 中的各種引用')
  parser.add_argument('input_file', help='輸入的 JSON 檔案路徑')
  parser.add_argument('-o', '--output',
                      help='輸出檔案路徑 (預設: 原檔名_no_closes.json)')
  parser.add_argument('--preview', action='store_true',
                      help='預覽模式，只顯示會被處理的資料')
  parser.add_argument('--examples', type=int, default=10,
                      help='預覽模式下顯示的範例數量')

  args = parser.parse_args()

  if args.preview:
    # 預覽模式
    preview_changes(args.input_file, args.examples)
  else:
    # 正常處理模式
    process_file(args.input_file, args.output)


# 直接使用的簡單函數
def clean_closes_data(file_path: str) -> None:
  """
  簡化版本的資料清理函數

  Args:
      file_path: JSON 檔案路徑
  """
  process_file(file_path)

if __name__ == "__main__":

  # 執行主程式
  main()