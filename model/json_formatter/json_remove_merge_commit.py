import json
import sys
from pathlib import Path


def is_merge_commit(commit_message: str) -> bool:
  """檢查是否為 merge commit"""
  if not commit_message:
    return False
  first_line = commit_message.strip().split('\n')[0].strip().lower()
  return first_line.startswith('merge')


def remove_merge_commits(input_file: str, output_file: str = None):
  """移除 merge commits"""
  input_path = Path(input_file)

  if output_file is None:
    output_file = input_path.parent / f"{input_path.stem}_no_merge{input_path.suffix}"

  # 讀取資料
  with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

  # 過濾 merge commits
  filtered_data = []
  merge_count = 0

  for item in data:
    if 'output' in item and is_merge_commit(item['output']):
      merge_count += 1
    else:
      filtered_data.append(item)

  # 儲存結果
  with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f, ensure_ascii=False, indent=2)

  # 顯示結果
  print(f"原始: {len(data)} 筆")
  print(f"移除 merge: {merge_count} 筆")
  print(f"保留: {len(filtered_data)} 筆")
  print(f"儲存至: {output_file}")


if __name__ == "__main__":
  if len(sys.argv) < 2:
    sys.exit(1)

  input_file = sys.argv[1]
  output_file = sys.argv[2] if len(sys.argv) > 2 else None

  try:
    remove_merge_commits(input_file, output_file)
  except Exception as e:
    print(f"錯誤: {e}")