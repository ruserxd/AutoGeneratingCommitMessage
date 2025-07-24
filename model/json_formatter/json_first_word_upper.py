import json
import argparse
from pathlib import Path


def capitalize_first_word(text):
  """將第一個字大寫"""
  if not text or not isinstance(text, str):
    return text, False

  words = text.strip().split()
  if not words:
    return text, False

  original_first = words[0]
  capitalized_first = original_first.capitalize()

  if original_first == capitalized_first:
    return text, False

  words[0] = capitalized_first
  return ' '.join(words), True


def process_file(input_file, output_file=None, field='output'):
  """處理檔案"""
  input_path = Path(input_file)

  if output_file is None:
    output_file = input_path.parent / f"{input_path.stem}_capitalized{input_path.suffix}"

  # 讀取資料
  with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

  print(f"📂 處理檔案: {input_path.name}")
  print(f"📊 總資料筆數: {len(data):,}")

  # 處理資料
  changed_count = 0
  for item in data:
    if isinstance(item, dict) and field in item:
      new_text, changed = capitalize_first_word(item[field])
      if changed:
        item[field] = new_text
        changed_count += 1

  # 儲存結果
  with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

  print(f"✅ 已變更: {changed_count:,} 筆")
  print(f"📁 輸出檔案: {Path(output_file).name}")


def main():
  """主函數"""
  parser = argparse.ArgumentParser(description='第一個字大寫工具')
  parser.add_argument('input_file', help='輸入的 JSON 檔案路徑')
  parser.add_argument('-o', '--output', help='輸出檔案路徑')
  parser.add_argument('-f', '--field', default='output',
                      help='要處理的欄位名 (預設: output)')

  args = parser.parse_args()

  if not Path(args.input_file).exists():
    print(f"❌ 錯誤: 找不到檔案 {args.input_file}")
    return

  try:
    process_file(args.input_file, args.output, args.field)
    print("🎉 處理完成！")
  except Exception as e:
    print(f"❌ 處理失敗: {e}")


if __name__ == "__main__":
  main()