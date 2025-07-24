import json
import re
import argparse
from typing import Dict, List, Any


def remove_bs_tags(commit_message: str) -> str:
  """
  移除 commit message 中的 [bs-xx] 標識符

  Args:
      commit_message: 原始的 commit message

  Returns:
      移除標識符後的 commit message
  """
  # 只移除 [bs-數字] 格式標識符（任何位置）
  # 原始程式碼只需要移除開頭的 ^ 符號！
  pattern = r'\[bs-\d+\]\s*'  # 移除了 ^ 符號
  cleaned_message = re.sub(pattern, '', commit_message, flags=re.IGNORECASE)

  # 保持原來的邏輯，只移除多餘的空白
  cleaned_message = cleaned_message.strip()

  return cleaned_message


def process_json_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  """
  處理 JSON 資料，移除所有 output 欄位中的 bs 標識符

  Args:
      data: 包含訓練資料的 JSON 陣列

  Returns:
      處理後的 JSON 資料
  """
  processed_data = []

  for item in data:
    if 'output' in item:
      # 保留原始資料結構，只修改 output 欄位
      processed_item = item.copy()
      processed_item['output'] = remove_bs_tags(item['output'])
      processed_data.append(processed_item)
    else:
      # 如果沒有 output 欄位，保持原樣
      processed_data.append(item)

  return processed_data


def process_file(input_file: str, output_file: str = None) -> None:
  """
  處理 JSON 檔案

  Args:
      input_file: 輸入檔案路徑
      output_file: 輸出檔案路徑（可選，預設會覆蓋原檔案）
  """
  # 設定輸出檔案路徑
  if output_file is None:
    output_file = input_file.replace('.json', '_cleaned.json')

  try:
    # 讀取 JSON 檔案
    with open(input_file, 'r', encoding='utf-8') as f:
      data = json.load(f)

    print(f"📂 載入檔案: {input_file}")
    print(f"📊 總資料筆數: {len(data)}")

    # 統計包含 bs 標識符的資料筆數
    bs_count = 0
    for item in data:
      if 'output' in item and re.search(r'\[bs-\d+\]', item['output'],
                                        re.IGNORECASE):
        bs_count += 1

    print(f"🏷️  包含 [bs-xx] 標識符的資料: {bs_count} 筆")

    # 只有當有 bs 標籤時才處理
    if bs_count == 0:
      print("✅ 沒有發現 [bs-xx] 標籤，無需處理")
      return

    # 處理資料
    processed_data = process_json_data(data)

    # 儲存處理後的資料
    with open(output_file, 'w', encoding='utf-8') as f:
      json.dump(processed_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 處理完成，已儲存至: {output_file}")

    # 只顯示實際被修改的範例
    print(f"\n📝 處理範例:")
    count = 0
    for item in data:
      if 'output' in item and re.search(r'\[bs-\d+\]', item['output'],
                                        re.IGNORECASE):
        original = item['output']
        cleaned = remove_bs_tags(original)
        print(f"原始: {original}")
        print(f"清理: {cleaned}")
        print("-" * 50)
        count += 1
        if count >= 2:  # 只顯示2個範例
          break

  except FileNotFoundError:
    print(f"❌ 錯誤: 找不到檔案 {input_file}")
  except json.JSONDecodeError:
    print(f"❌ 錯誤: {input_file} 不是有效的 JSON 檔案")
  except Exception as e:
    print(f"❌ 處理過程中發生錯誤: {str(e)}")


def main():
  """主函數"""
  parser = argparse.ArgumentParser(
    description='移除 Git commit message 中的 [bs-xx] 標識符')
  parser.add_argument('input_file', help='輸入的 JSON 檔案路徑')
  parser.add_argument('-o', '--output',
                      help='輸出檔案路徑 (預設: 原檔名_cleaned.json)')
  parser.add_argument('--preview', action='store_true',
                      help='預覽模式，只顯示會被處理的資料')

  args = parser.parse_args()

  if args.preview:
    # 預覽模式
    try:
      with open(args.input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

      print(f"📋 預覽模式 - {args.input_file}")
      print(f"總資料筆數: {len(data)}")

      bs_items = []
      for i, item in enumerate(data):
        if 'output' in item and re.search(r'\[bs-\d+\]', item['output'],
                                          re.IGNORECASE):
          bs_items.append((i, item))

      print(f"包含 [bs-xx] 的資料: {len(bs_items)} 筆")

      if len(bs_items) == 0:
        print("✅ 沒有發現需要清理的 [bs-xx] 標籤")
        return

      # 顯示前5筆會被處理的資料
      for i, (idx, item) in enumerate(bs_items[:5]):
        print(f"\n第 {idx + 1} 筆:")
        print(f"原始: {item['output']}")
        print(f"清理: {remove_bs_tags(item['output'])}")

      if len(bs_items) > 5:
        print(f"\n... 還有 {len(bs_items) - 5} 筆類似資料")

    except Exception as e:
      print(f"❌ 預覽失敗: {str(e)}")
  else:
    # 正常處理模式
    process_file(args.input_file, args.output)


# 直接使用的簡單函數
def clean_commit_data(file_path: str) -> None:
  """
  簡化版本的資料清理函數

  Args:
      file_path: JSON 檔案路徑
  """
  process_file(file_path)


if __name__ == "__main__":
  main()