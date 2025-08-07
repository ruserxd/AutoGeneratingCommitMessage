#!/usr/bin/env python3
import json
import sys
import os


def clean_message(message: str) -> str:
  """移除開頭的破折號和空白"""
  return message.lstrip('- \t\n')


def process_file(file_path: str) -> None:
  """處理單個 JSON 檔案"""
  try:
    with open(file_path, 'r', encoding='utf-8') as f:
      data = json.load(f)

    cleaned_count = 0
    for item in data:
      if isinstance(item, dict) and 'output' in item:
        original = item['output']
        cleaned = clean_message(original)

        if cleaned != original:
          item['output'] = cleaned
          cleaned_count += 1

    with open(file_path, 'w', encoding='utf-8') as f:
      json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ {file_path}: 清理 {cleaned_count} 筆")

  except Exception as e:
    print(f"❌ {file_path}: {e}")


def main():
  if len(sys.argv) != 2:
    print("用法: python remove_dash.py <檔案或目錄>")
    sys.exit(1)

  path = sys.argv[1]

  if os.path.isfile(path):
    process_file(path)
  elif os.path.isdir(path):
    for f in os.listdir(path):
      if f.endswith('.json'):
        process_file(os.path.join(path, f))

  print("🎉 完成!")


if __name__ == "__main__":
  main()