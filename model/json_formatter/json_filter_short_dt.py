import json
import sys
from pathlib import Path


def filter_json_data(input_file, min_words=1):
  """過濾 output 詞數不足的 JSON 資料"""

  # 讀取檔案
  try:
    with open(input_file, 'r', encoding='utf-8') as f:
      data = json.load(f)
  except Exception as e:
    print(f"❌ 讀取失敗: {e}")
    return

  # 過濾資料
  filtered = []
  removed = 0

  for item in data:
    if isinstance(item, dict) and 'output' in item:
      output = item['output']
      if isinstance(output, str) and len(output.strip().split()) >= min_words:
        filtered.append(item)
      else:
        removed += 1
    else:
      filtered.append(item)

  # 生成輸出檔名
  input_path = Path(input_file)
  output_file = input_path.parent / f"{input_path.stem}_filtered{input_path.suffix}"

  # 儲存結果
  try:
    with open(output_file, 'w', encoding='utf-8') as f:
      json.dump(filtered, f, ensure_ascii=False, indent=2)
  except Exception as e:
    print(f"❌ 儲存失敗: {e}")
    return

  # 顯示結果
  print(f"原始資料: {len(data)} 筆")
  print(f"移除資料: {removed} 筆")
  print(f"保留資料: {len(filtered)} 筆")
  print(f"輸出檔案: {output_file.name}")


if __name__ == "__main__":
  if len(sys.argv) != 2:
    print("用法: python filter.py <json檔案>")
    print("功能: 移除 output 少於 3 個詞的資料")
    sys.exit(1)

  input_file = sys.argv[1]

  if not Path(input_file).exists():
    print(f"❌ 找不到檔案: {input_file}")
    sys.exit(1)

  filter_json_data(input_file)