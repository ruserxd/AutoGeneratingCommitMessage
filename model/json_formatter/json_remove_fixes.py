#!/usr/bin/env python3
import json
import re
import sys


def remove_fixes_references(text):
  """移除 Fixes/Closes/Resolves 等 issue 引用"""
  if not isinstance(text, str):
    return text

  # 移除各種 issue 引用格式
  patterns = [
    r'\n\nFixes #\d+.*$',  # Fixes #1234
    r'\n\nCloses #\d+.*$',  # Closes #1234
    r'\n\nResolves #\d+.*$',  # Resolves #1234
    r'\n\nRef #\d+.*$',  # Ref #1234
    r'\n\nSee #\d+.*$',  # See #1234
    r'\n\nRelated to #\d+.*$',  # Related to #1234
    r'\n\nFix #\d+.*$',  # Fix #1234
    r'\n\nAddress #\d+.*$',  # Address #1234
  ]

  cleaned_text = text.strip()
  for pattern in patterns:
    cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE)

  return cleaned_text.strip()


def clean_data(data):
  """遞迴清理資料"""
  if isinstance(data, dict):
    for key, value in data.items():
      if key == "output" and isinstance(value, str):
        data[key] = remove_fixes_references(value)
      elif isinstance(value, (dict, list)):
        clean_data(value)
  elif isinstance(data, list):
    for item in data:
      clean_data(item)


def main():
  if len(sys.argv) != 2:
    print("使用方式: python remove_fixes.py <json檔案>")
    sys.exit(1)

  filename = sys.argv[1]

  try:
    with open(filename, 'r', encoding='utf-8') as f:
      data = json.load(f)

    print("正在移除 Fixes 引用...")
    clean_data(data)

    with open(filename, 'w', encoding='utf-8') as f:
      json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ 已處理檔案: {filename}")

  except Exception as e:
    print(f"錯誤: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()