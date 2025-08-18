import json
import re
import sys


def remove_parenthesis_number(text):
  """移除文字中的 (#數字) 格式"""
  if not isinstance(text, str):
    return text

  # 移除 (#數字) 格式，包含前面可能的空格
  cleaned_text = re.sub(r'\s*\(#\d+\)', '', text)

  return cleaned_text.strip()


def process_data(data):
  """遞迴處理資料"""
  if isinstance(data, dict):
    for key, value in data.items():
      if key == "output" and isinstance(value, str):
        data[key] = remove_parenthesis_number(value)
      elif isinstance(value, (dict, list)):
        process_data(value)
  elif isinstance(data, list):
    for item in data:
      process_data(item)


def main():
  if len(sys.argv) != 2:
    print("使用方式: python remove_parenthesis.py <json檔案>")
    sys.exit(1)

  filename = sys.argv[1]

  try:
    with open(filename, 'r', encoding='utf-8') as f:
      data = json.load(f)

    print("正在移除 (#xxxx) 格式...")
    process_data(data)

    with open(filename, 'w', encoding='utf-8') as f:
      json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ 已處理檔案: {filename}")

  except Exception as e:
    print(f"錯誤: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()