import json
import re
import sys
import os


def clean_signatures(text):
  patterns = [
    r'\s*Co-authored-by:.*?(?=\n|$)',
    r'\s*Signed-off-by:.*?(?=\n|$)',
    r'\s*Reviewed-by:.*?(?=\n|$)',
    r'\s*Tested-by:.*?(?=\n|$)',
    r'\s*Acked-by:.*?(?=\n|$)',
    r'\s*Change-Id:.*?(?=\n|$)',
  ]

  cleaned = text
  for pattern in patterns:
    cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)

  cleaned = re.sub(r'\n\s*\n+', '\n', cleaned)
  return cleaned.strip()


def process_file(file_path):
  with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

  count = 0
  if isinstance(data, list):
    for item in data:
      if isinstance(item, dict) and 'output' in item:
        original = item['output']
        cleaned = clean_signatures(original)
        if original != cleaned:
          item['output'] = cleaned
          count += 1

  with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

  print(f"✅ {file_path}: 清理 {count} 筆")


def main():
  if len(sys.argv) != 2:
    print("用法: python clean_sigs.py <檔案或目錄>")
    sys.exit(1)

  path = sys.argv[1]

  if os.path.isfile(path):
    process_file(path)
  elif os.path.isdir(path):
    for f in os.listdir(path):
      if f.endswith('.json'):
        process_file(os.path.join(path, f))


if __name__ == '__main__':
  main()