import json
import argparse
from pathlib import Path


def filter_short_outputs(data, min_words=2):
  """過濾 output 詞數不足的資料"""
  if not isinstance(data, list):
    return data

  filtered = []
  removed_count = 0

  for item in data:
    if isinstance(item, dict) and 'output' in item:
      output = item['output']
      if isinstance(output, str):
        word_count = len(output.strip().split())
        if word_count >= min_words:
          filtered.append(item)
        else:
          removed_count += 1
      else:
        filtered.append(item)
    else:
      filtered.append(item)

  print(f"移除 {removed_count} 筆詞數不足的資料")
  return filtered


def process_file(input_file, output_file=None, min_words=2):
  """處理單個檔案"""
  input_path = Path(input_file)

  if output_file is None:
    output_file = input_path.parent / f"{input_path.stem}_filtered{input_path.suffix}"

  # 讀取資料
  try:
    with open(input_file, 'r', encoding='utf-8') as f:
      data = json.load(f)
  except Exception as e:
    print(f"❌ 讀取失敗: {e}")
    return False

  print(f"📂 處理檔案: {input_path.name}")
  print(f"📊 原始資料: {len(data)} 筆")

  # 過濾資料
  filtered_data = filter_short_outputs(data, min_words)

  # 儲存結果
  try:
    with open(output_file, 'w', encoding='utf-8') as f:
      json.dump(filtered_data, f, ensure_ascii=False, indent=2)
  except Exception as e:
    print(f"❌ 儲存失敗: {e}")
    return False

  print(f"✅ 保留資料: {len(filtered_data)} 筆")
  print(f"📁 輸出檔案: {Path(output_file).name}")
  return True


def main():
  """主函數"""
  parser = argparse.ArgumentParser(
      description='移除 output 詞數不足的訓練資料',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog='''
範例:
  python filter_words.py data.json                    # 過濾少於2詞的
  python filter_words.py data.json --min-words 3      # 過濾少於3詞的
  python filter_words.py data.json -o clean.json     # 指定輸出檔案
        '''
  )

  parser.add_argument('input_file', help='輸入 JSON 檔案路徑')
  parser.add_argument('-o', '--output', help='輸出檔案路徑')
  parser.add_argument('--min-words', type=int, default=2,
                      help='最小詞數要求 (預設: 2)')

  args = parser.parse_args()

  if not Path(args.input_file).exists():
    print(f"❌ 錯誤: 找不到檔案 {args.input_file}")
    return

  if args.min_words < 1:
    print(f"❌ 錯誤: 最小詞數必須大於等於 1")
    return

  success = process_file(args.input_file, args.output, args.min_words)

  if success:
    print("\n🎉 過濾完成！")

if __name__ == "__main__":
  main()