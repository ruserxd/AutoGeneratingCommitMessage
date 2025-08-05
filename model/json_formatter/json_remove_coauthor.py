#!/usr/bin/env python3
import json
import argparse
import re
import sys


def clean_coauthor(text):
  """移除 Co-authored-by 相關內容"""
  # 移除 Co-authored-by 行（包含前後的換行符）
  pattern = r'\s*Co-authored-by:.*?(?=\n|$)'
  cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE)

  # 清理多餘的空白和換行
  cleaned = re.sub(r'\n\s*\n', '\n', cleaned)  # 移除多餘空行
  cleaned = cleaned.strip()  # 移除前後空白

  return cleaned


def process_json_file(file_path):
  """處理 JSON 檔案"""
  try:
    with open(file_path, 'r', encoding='utf-8') as f:
      data = json.load(f)

    # 處理單個物件或物件陣列
    if isinstance(data, list):
      for item in data:
        if isinstance(item, dict) and 'output' in item:
          item['output'] = clean_coauthor(item['output'])
    elif isinstance(data, dict) and 'output' in data:
      data['output'] = clean_coauthor(data['output'])

    # 寫回檔案
    with open(file_path, 'w', encoding='utf-8') as f:
      json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已處理檔案: {file_path}")

  except FileNotFoundError:
    print(f"❌ 檔案不存在: {file_path}")
    sys.exit(1)
  except json.JSONDecodeError:
    print(f"❌ JSON 格式錯誤: {file_path}")
    sys.exit(1)
  except Exception as e:
    print(f"❌ 處理檔案時發生錯誤: {e}")
    sys.exit(1)


def main():
  parser = argparse.ArgumentParser(
    description='移除 JSON 檔案中 output 欄位的 Co-authored-by 內容')
  parser.add_argument('file', help='JSON 檔案路徑')
  parser.add_argument('--preview', '-p', action='store_true',
                      help='預覽變更但不實際修改檔案')

  args = parser.parse_args()

  if args.preview:
    # 預覽模式
    with open(args.file, 'r', encoding='utf-8') as f:
      data = json.load(f)

    if isinstance(data, dict) and 'output' in data:
      original = data['output']
      cleaned = clean_coauthor(original)
      print(f"原始內容:\n{original}\n")
      print(f"清理後:\n{cleaned}")
    else:
      print("未找到 output 欄位或格式不符")
  else:
    process_json_file(args.file)


if __name__ == '__main__':
  main()