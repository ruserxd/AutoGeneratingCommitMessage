import json
import re
import argparse
import sys
from pathlib import Path


def remove_polish_wrapper(data):
  """遞迴處理所有可能的 Polish 包裝"""

  if isinstance(data, dict):
    for key, value in data.items():
      if isinstance(value, str) and 'Polish "' in value:
        data[key] = re.sub(r'Polish\s+"([^"]*)"', r'\1', value)
      elif isinstance(value, (dict, list)):
        data[key] = remove_polish_wrapper(value)

  elif isinstance(data, list):
    for i, item in enumerate(data):
      if isinstance(item, str) and 'Polish "' in item:
        data[i] = re.sub(r'Polish\s+"([^"]*)"', r'\1', item)
      elif isinstance(item, (dict, list)):
        data[i] = remove_polish_wrapper(item)

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

  # 處理資料
  cleaned_data = remove_polish_wrapper(data)

  # 決定輸出路徑
  if in_place:
    output_path = input_path
  elif output_path is None:
    # 預設在原檔名後加上 _cleaned
    input_file = Path(input_path)
    output_path = input_file.parent / f"{input_file.stem}_cleaned{input_file.suffix}"

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
  for json_file in json_files:
    print(f"處理中: {json_file}")
    if process_json_file(json_file, in_place=in_place):
      success_count += 1

  print(f"批次處理完成！成功處理 {success_count}/{len(json_files)} 個檔案")


def main():
  parser = argparse.ArgumentParser(
      description='移除 JSON 檔案中被 Polish 包裝的內容',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog='''
使用範例:
  %(prog)s input.json                    # 產生 input_cleaned.json
  %(prog)s input.json -o output.json     # 指定輸出檔案
  %(prog)s input.json --in-place         # 覆蓋原檔案
  %(prog)s -d ./folder                   # 批次處理目錄
  %(prog)s -d ./folder --in-place        # 批次處理並覆蓋原檔案
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
    # 批次處理模式
    batch_process_directory(args.directory, args.pattern, args.in_place)
  elif args.input:
    # 單檔處理模式
    process_json_file(args.input, args.output, args.in_place)
  else:
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
  main()