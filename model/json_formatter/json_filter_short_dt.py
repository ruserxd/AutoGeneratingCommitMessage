#!/usr/bin/env python3
import json
import argparse
import sys
from pathlib import Path


def is_single_word(text):
  """判斷是否只有一個字串（單詞）"""
  if not isinstance(text, str):
    return False

  # 移除前後空白並分割
  words = text.strip().split()
  return len(words) == 1


def clean_json_data(data):
  """移除 output 只有一個字串的項目"""

  if isinstance(data, dict):
    # 如果是字典且有 output 欄位
    if 'output' in data and is_single_word(data['output']):
      print(f"移除單字 output: '{data['output']}'")
      return None  # 標記為要移除的項目

    # 遞迴處理字典中的其他值
    cleaned_dict = {}
    for key, value in data.items():
      cleaned_value = clean_json_data(value)
      if cleaned_value is not None:
        cleaned_dict[key] = cleaned_value
    return cleaned_dict

  elif isinstance(data, list):
    # 處理列表，過濾掉 None 值
    cleaned_list = []
    for item in data:
      cleaned_item = clean_json_data(item)
      if cleaned_item is not None:
        cleaned_list.append(cleaned_item)
    return cleaned_list

  else:
    # 其他類型直接返回
    return data


def process_json_file(input_path, output_path=None, in_place=False):
  """處理 JSON 檔案"""

  try:
    with open(input_path, 'r', encoding='utf-8') as file:
      data = json.load(file)
  except FileNotFoundError:
    print(f"錯誤: 找不到檔案 '{input_path}'", file=sys.stderr)
    return False
  except json.JSONDecodeError as e:
    print(f"錯誤: JSON 格式錯誤 - {e}", file=sys.stderr)
    return False

  print(f"處理檔案: {input_path}")

  # 清理資料
  cleaned_data = clean_json_data(data)

  # 決定輸出路徑
  if in_place:
    output_path = input_path
  elif output_path is None:
    input_file = Path(input_path)
    output_path = input_file.parent / f"{input_file.stem}_filtered{input_file.suffix}"

  # 寫入處理後的資料
  try:
    with open(output_path, 'w', encoding='utf-8') as file:
      json.dump(cleaned_data, file, ensure_ascii=False, indent=2)
    print(f"✅ 處理完成: {output_path}")
    return True
  except Exception as e:
    print(f"錯誤: 無法寫入檔案 - {e}", file=sys.stderr)
    return False


def batch_process_directory(directory_path, pattern="*.json", in_place=False):
  """批次處理目錄"""

  dir_path = Path(directory_path)
  if not dir_path.exists():
    print(f"錯誤: 目錄 '{directory_path}' 不存在", file=sys.stderr)
    return

  json_files = list(dir_path.glob(pattern))

  if not json_files:
    print(f"在 '{directory_path}' 中找不到符合 '{pattern}' 的檔案")
    return

  success_count = 0
  total_removed = 0

  for json_file in json_files:
    if process_json_file(json_file, in_place=in_place):
      success_count += 1

  print(f"批次處理完成！成功處理 {success_count}/{len(json_files)} 個檔案")


def main():
  parser = argparse.ArgumentParser(
      description='移除 JSON 檔案中 output 只有一個字串的資料',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog='''
使用範例:
  %(prog)s input.json                    # 產生 input_filtered.json
  %(prog)s input.json -o output.json     # 指定輸出檔案
  %(prog)s input.json --in-place         # 覆蓋原檔案
  %(prog)s -d ./folder                   # 批次處理目錄
  %(prog)s -d ./folder --in-place        # 批次處理並覆蓋原檔案

什麼會被移除:
  {"output": "hello"}           # 單個字串 → 被移除
  {"output": "test"}            # 單個字串 → 被移除
  {"output": "hello world"}     # 多個字串 → 保留
  {"output": ""}                # 空字串 → 保留
        '''
  )

  parser.add_argument('input', nargs='?', help='輸入 JSON 檔案路徑')
  parser.add_argument('-o', '--output', help='輸出檔案路徑')
  parser.add_argument('-d', '--directory', help='批次處理目錄')
  parser.add_argument('--in-place', action='store_true', help='直接覆蓋原檔案')
  parser.add_argument('--pattern', default='*.json',
                      help='檔案匹配模式 (預設: *.json)')

  args = parser.parse_args()

  if args.directory:
    batch_process_directory(args.directory, args.pattern, args.in_place)
  elif args.input:
    process_json_file(args.input, args.output, args.in_place)
  else:
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
  main()