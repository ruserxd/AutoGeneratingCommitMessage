import json
import re
import sys
from pathlib import Path


def remove_commit_prefix(commit_msg: str) -> str:
  """移除 commit message 前綴"""
  if not commit_msg:
    return commit_msg

  # 移除 "type: " 或 "type(scope): " 格式
  pattern = r'^[a-zA-Z]+(\([^)]+\))?\s*:\s*'
  cleaned = re.sub(pattern, '', commit_msg)

  # 首字母大寫
  if cleaned and cleaned[0].islower():
    cleaned = cleaned[0].upper() + cleaned[1:]

  return cleaned.strip()


def process_data(input_file: str, output_file: str = None):
  """移除 commit message 前綴"""
  input_path = Path(input_file)

  if output_file is None:
    output_file = input_path.parent / f"{input_path.stem}_no_prefix{input_path.suffix}"

  # 讀取和處理
  with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

  modified_count = 0
  for item in data:
    if 'output' in item:
      original = item['output']
      cleaned = remove_commit_prefix(original)
      item['output'] = cleaned
      if original != cleaned:
        modified_count += 1

  # 儲存
  with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

  print(f"處理: {len(data)} 筆")
  print(f"修改: {modified_count} 筆")
  print(f"儲存: {output_file}")


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("用法: python remove_prefix.py input.json [output.json]")
    sys.exit(1)

  input_file = sys.argv[1]
  output_file = sys.argv[2] if len(sys.argv) > 2 else None

  try:
    process_data(input_file, output_file)
  except Exception as e:
    print(f"錯誤: {e}")