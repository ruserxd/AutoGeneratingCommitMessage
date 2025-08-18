import json
import re
import sys


def remove_former_commit_id(data):
  if isinstance(data, dict):
    for key, value in data.items():
      if key == "output" and isinstance(value, str):
        data[key] = re.sub(r'Former-commit-id:.*$', '', value.strip())
      elif isinstance(value, (dict, list)):
        remove_former_commit_id(value)
  elif isinstance(data, list):
    for item in data:
      remove_former_commit_id(item)


def main():
  if len(sys.argv) != 2:
    print("使用方式: python remove_commit_id.py <json檔案>")
    sys.exit(1)

  filename = sys.argv[1]

  try:
    with open(filename, 'r', encoding='utf-8') as f:
      data = json.load(f)

    remove_former_commit_id(data)

    with open(filename, 'w', encoding='utf-8') as f:
      json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ 已處理檔案: {filename}")

  except Exception as e:
    print(f"錯誤: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()