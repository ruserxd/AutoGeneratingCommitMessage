import json
import re
import sys
import argparse


def remove_pr_references(text):
  """移除文本中的 PR 引用"""
  if not isinstance(text, str):
    return text

  # 匹配 (PR #xxxx) 格式
  result = re.sub(r'\s*\(PR\s*#\d+\)', '', text, flags=re.IGNORECASE)
  return result.strip()


def process_json_data(data):
  """遞歸處理 JSON 資料"""
  if isinstance(data, dict):
    return {key: process_json_data(value) for key, value in data.items()}
  elif isinstance(data, list):
    return [process_json_data(item) for item in data]
  elif isinstance(data, str):
    return remove_pr_references(data)
  else:
    return data


def main():
  parser = argparse.ArgumentParser(description='移除 JSON 中的 PR 編號')
  parser.add_argument('input_file', help='輸入檔案路徑')
  parser.add_argument('-o', '--output', help='輸出檔案路徑 (預設: 覆蓋原檔案)')

  args = parser.parse_args()

  try:
    # 讀取 JSON 檔案
    with open(args.input_file, 'r', encoding='utf-8') as f:
      data = json.load(f)

    # 處理資料
    cleaned_data = process_json_data(data)

    # 決定輸出檔案
    output_file = args.output or args.input_file

    # 寫入檔案
    with open(output_file, 'w', encoding='utf-8') as f:
      json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

    print(f"✅ 處理完成: {output_file}")

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