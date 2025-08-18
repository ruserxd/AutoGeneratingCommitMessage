import json
import sys


def remove_first_word(text):
  """移除文字的第一個字"""
  if not isinstance(text, str) or not text.strip():
    return text

  words = text.strip().split()
  if len(words) <= 1:
    return ""

  # 移除第一個字，保留其餘部分
  return " ".join(words[1:])


def process_data(data):
  """遞迴處理資料"""
  if isinstance(data, dict):
    for key, value in data.items():
      if key == "output" and isinstance(value, str):
        data[key] = remove_first_word(value)
      elif isinstance(value, (dict, list)):
        process_data(value)
  elif isinstance(data, list):
    for item in data:
      process_data(item)


def main():
  if len(sys.argv) != 2:
    print("使用方式: python remove_first_word.py <json檔案>")
    sys.exit(1)

  filename = sys.argv[1]

  try:
    with open(filename, 'r', encoding='utf-8') as f:
      data = json.load(f)

    print("正在移除第一個字...")
    process_data(data)

    with open(filename, 'w', encoding='utf-8') as f:
      json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ 已處理檔案: {filename}")

  except Exception as e:
    print(f"錯誤: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()