#!/usr/bin/env python3
import json
import re
import sys
import argparse


def remove_fixes_references(text):
  """移除 Fixes/Closes/Resolves 等 issue 引用"""
  if not isinstance(text, str):
    return text

  # 移除各種 issue 引用格式
  patterns = [
    r'\s*fix\s*#\d+',  # fix #1234
    r'\s*fixes\s*#\d+',  # fixes #1234
    r'\n\nFixes #\d+.*$',  # Fixes #1234
    r'\n\nCloses #\d+.*$',  # Closes #1234
    r'\n\nResolves #\d+.*$',  # Resolves #1234
    r'\n\nRef #\d+.*$',  # Ref #1234
    r'\n\nSee #\d+.*$',  # See #1234
    r'\n\nRelated to #\d+.*$',  # Related to #1234
    r'\n\nFix #\d+.*$',  # Fix #1234
    r'\n\nAddress #\d+.*$',  # Address #1234
    r'\s*\(#\d+\)',  # (#1234)
    r'\s*\([Ff]ix\s*#\d+\)',  # (Fix #1234)
    r'\s*\([Ff]ixes\s*#\d+\)',  # (Fixes #1234)
  ]

  cleaned_text = text.strip()
  for pattern in patterns:
    cleaned_text = re.sub(pattern, '', cleaned_text,
                          flags=re.MULTILINE | re.IGNORECASE)

  # 清理多餘的空白和換行
  cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text)  # 移除多餘空行
  cleaned_text = re.sub(r'\s+$', '', cleaned_text, flags=re.MULTILINE)  # 移除行尾空白

  return cleaned_text.strip()


def process_json_data(data):
  """遞歸處理 JSON 資料"""
  if isinstance(data, dict):
    return {key: process_json_data(value) for key, value in data.items()}
  elif isinstance(data, list):
    return [process_json_data(item) for item in data]
  elif isinstance(data, str):
    return remove_fixes_references(data)
  else:
    return data


def main():
  parser = argparse.ArgumentParser(
    description='移除 JSON 中的 Fixes/Closes 等 issue 引用')
  parser.add_argument('input_file', help='輸入 JSON 檔案路徑')
  parser.add_argument('-o', '--output', help='輸出檔案路徑 (預設: 覆蓋原檔案)')
  parser.add_argument('--dry-run', action='store_true',
                      help='預覽模式，不實際修改檔案')

  args = parser.parse_args()

  try:
    # 讀取 JSON 檔案
    with open(args.input_file, 'r', encoding='utf-8') as f:
      original_data = json.load(f)

    print("正在移除 Fixes/issue 引用...")
    cleaned_data = process_json_data(original_data)

    # 預覽模式
    if args.dry_run:
      print("\n=== 預覽結果 ===")
      print(json.dumps(cleaned_data, indent=2, ensure_ascii=False))
      return

    # 決定輸出檔案
    output_file = args.output or args.input_file

    # 寫入檔案
    with open(output_file, 'w', encoding='utf-8') as f:
      json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

    print(f"✅ 已處理檔案: {output_file}")

  except FileNotFoundError:
    print(f"❌ 檔案不存在: {args.input_file}")
    sys.exit(1)
  except json.JSONDecodeError:
    print(f"❌ JSON 格式錯誤: {args.input_file}")
    sys.exit(1)
  except Exception as e:
    print(f"❌ 錯誤: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()