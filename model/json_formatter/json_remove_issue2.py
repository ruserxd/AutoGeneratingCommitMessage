#!/usr/bin/env python3
import json
import re
import sys
import os
from typing import List, Dict


def clean_commit_message(message: str) -> str:
  """清理 commit message，移除項目編號等不必要的內容"""
  patterns_to_remove = [
    r'^GP-\d+:?\s*',  # GP-數字: 或 GP-數字
    r'^GHIDRA-\d+:?\s*',  # GHIDRA-數字: 或 GHIDRA-數字
    r'^[A-Z]+-\d+:?\s*',  # 任何 大寫字母-數字: 格式
    r'^#\d+:?\s*',  # #數字: 或 #數字
    r'^\[\w+-\d+\]\s*',  # [GP-數字] 格式
    r'^(Issue|Fix|Fixes|Close|Closes)\s+#?\d+:?\s*',  # Issue/Fix 相關
  ]

  cleaned = message
  for pattern in patterns_to_remove:
    cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

  # 移除多餘空白
  cleaned = re.sub(r'\s+', ' ', cleaned.strip())
  return cleaned


def process_file(file_path: str) -> None:
  """處理單個 JSON 檔案"""
  try:
    with open(file_path, 'r', encoding='utf-8') as f:
      data = json.load(f)

    if not isinstance(data, list):
      print(f"❌ {file_path}: 不是有效的 JSON 陣列格式")
      return

    cleaned_count = 0
    for item in data:
      if isinstance(item, dict) and 'output' in item:
        original = item['output']
        cleaned = clean_commit_message(original)

        if cleaned != original:
          item['output'] = cleaned
          cleaned_count += 1

    # 寫回檔案
    with open(file_path, 'w', encoding='utf-8') as f:
      json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ {file_path}: 處理 {len(data)} 筆資料，清理 {cleaned_count} 筆")

  except Exception as e:
    print(f"❌ {file_path}: 處理失敗 - {e}")


def process_directory(dir_path: str) -> None:
  """處理目錄中的所有 JSON 檔案"""
  json_files = [f for f in os.listdir(dir_path) if f.endswith('.json')]

  if not json_files:
    print(f"❌ {dir_path}: 沒有找到 JSON 檔案")
    return

  print(f"🔍 找到 {len(json_files)} 個 JSON 檔案")

  for filename in json_files:
    file_path = os.path.join(dir_path, filename)
    process_file(file_path)


def main():
  if len(sys.argv) != 2:
    sys.exit(1)

  path = sys.argv[1]

  if not os.path.exists(path):
    print(f"❌ 路徑不存在: {path}")
    sys.exit(1)

  print(f"🚀 開始處理: {path}")

  if os.path.isfile(path):
    process_file(path)
  elif os.path.isdir(path):
    process_directory(path)
  else:
    print(f"❌ 無效的路徑類型: {path}")

  print("🎉 處理完成!")


if __name__ == "__main__":
  main()