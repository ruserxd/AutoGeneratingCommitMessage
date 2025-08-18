#!/usr/bin/env python3
import json
import re
import sys


def remove_hash_number(data):
  """移除 output 欄位開頭的 #xxxx 部分"""
  if isinstance(data, dict):
    for key, value in data.items():
      if key == "output" and isinstance(value, str):
        # 移除開頭的 #數字 和後面的空格
        data[key] = re.sub(r'^#\d+\s+', '', value.strip())
      elif isinstance(value, (dict, list)):
        remove_hash_number(value)
  elif isinstance(data, list):
    for item in data:
      remove_hash_number(item)


def main():
  if len(sys.argv) != 2:
    print("使用方式: python remove_hash.py <json檔案>")
    sys.exit(1)

  filename = sys.argv[1]

  try:
    with open(filename, 'r', encoding='utf-8') as f:
      data = json.load(f)

    remove_hash_number(data)

    with open(filename, 'w', encoding='utf-8') as f:
      json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ 已處理檔案: {filename}")

  except Exception as e:
    print(f"錯誤: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()