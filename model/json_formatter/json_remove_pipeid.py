#!/usr/bin/env python3
import json
import re
import sys


def clean_commit_message(text):
  if not isinstance(text, str):
    return text

  patterns = [
    r'\nPiperOrigin-RevId:.*$',  # PiperOrigin-RevId
    r'\n\nRELNOTES=.*$',  # RELNOTES
    r'\n\nFixes:.*$',  # BUG
  ]

  cleaned_text = text.strip()
  for pattern in patterns:
    cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE)

  return cleaned_text.strip()


def clean_training_data(data):
  """遞迴清理訓練資料"""
  if isinstance(data, dict):
    for key, value in data.items():
      if key == "output" and isinstance(value, str):
        data[key] = clean_commit_message(value)
      elif isinstance(value, (dict, list)):
        clean_training_data(value)
  elif isinstance(data, list):
    for item in data:
      clean_training_data(item)


def main():
  if len(sys.argv) != 2:
    print("使用方式: python clean_commit.py <json檔案>")
    sys.exit(1)

  filename = sys.argv[1]

  try:
    with open(filename, 'r', encoding='utf-8') as f:
      data = json.load(f)

    print("正在清理訓練資料...")
    clean_training_data(data)

    with open(filename, 'w', encoding='utf-8') as f:
      json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ 已清理檔案: {filename}")

  except Exception as e:
    print(f"錯誤: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()