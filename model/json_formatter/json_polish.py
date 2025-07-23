import json
import re
import argparse
import sys
from pathlib import Path


def clean_commit_message(message):
  """
  清理 commit message，移除不必要的格式和修飾詞
  """
  if not message:
    return message

  # 移除首尾的引號
  message = message.strip('"\'')

  # 移除常見的修飾詞（不區分大小寫）
  polish_patterns = [
    r'^Polish\s+"?([^"]+)"?$',  # Polish "xxx"
    r'^Polish\s+(.+)$',  # Polish xxx
    r'^Fix\s+"?([^"]+)"?$',  # Fix "xxx"
    r'^Update\s+"?([^"]+)"?$',  # Update "xxx"
    r'^Refactor\s+"?([^"]+)"?$',  # Refactor "xxx"
  ]

  for pattern in polish_patterns:
    match = re.match(pattern, message, re.IGNORECASE)
    if match:
      # 提取括號內的內容
      cleaned = match.group(1).strip()
      # 確保首字母大寫
      if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:] if len(
          cleaned) > 1 else cleaned.upper()
      return cleaned

  # 移除多餘的引號包圍
  if message.startswith('"') and message.endswith('"'):
    message = message[1:-1]

  # 確保首字母大寫
  if message:
    message = message[0].upper() + message[1:] if len(
      message) > 1 else message.upper()

  return message


def main():
  """主函數，處理命令行參數"""
  parser = argparse.ArgumentParser(
      description='清理 commit message 中的多餘格式和修飾詞',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog="""
使用範例:
  python commit_cleaner.py input.json output.json
  python commit_cleaner.py data.jsonl cleaned.jsonl --field commit_message
  python commit_cleaner.py --input data.json --output cleaned.json --field output
        """
  )

  parser.add_argument('input', nargs='?', help='輸入文件路徑')
  parser.add_argument('output', nargs='?', help='輸出文件路徑')
  parser.add_argument('-i', '--input', dest='input_file',
                      help='輸入文件路徑（替代位置參數）')
  parser.add_argument('-o', '--output', dest='output_file',
                      help='輸出文件路徑（替代位置參數）')
  parser.add_argument('-f', '--field', default='output',
                      help='要處理的字段名（默認: output）')
  parser.add_argument('--dry-run', action='store_true',
                      help='僅顯示會被修改的記錄，不實際寫入文件')
  parser.add_argument('-v', '--verbose', action='store_true',
                      help='顯示詳細信息')

  args = parser.parse_args()

  # 確定輸入輸出文件
  input_file = args.input or args.input_file
  output_file = args.output or args.output_file

  if not input_file:
    print("錯誤：請指定輸入文件")
    parser.print_help()
    sys.exit(1)

  if not output_file and not args.dry_run:
    print("錯誤：請指定輸出文件或使用 --dry-run 選項")
    parser.print_help()
    sys.exit(1)

  # 檢查輸入文件是否存在
  if not Path(input_file).exists():
    print(f"錯誤：輸入文件 '{input_file}' 不存在")
    sys.exit(1)

  # 處理文件
  if args.dry_run:
    dry_run_process(input_file, args.field, args.verbose)
  else:
    process_json_file(input_file, output_file, args.field, args.verbose)


def dry_run_process(input_file, output_key='output', verbose=False):
  """乾運行模式，只顯示會被修改的記錄"""
  try:
    data = load_json_data(input_file)

    print(f"乾運行模式 - 檢查文件: {input_file}")
    print(f"處理字段: {output_key}")
    print("=" * 60)

    processed_count = 0
    total_count = 0

    for item in data:
      total_count += 1
      if isinstance(item, dict) and output_key in item:
        original = item[output_key]
        cleaned = clean_commit_message(original)
        if original != cleaned:
          processed_count += 1
          print(f"記錄 #{total_count}")
          print(f"原始: {original}")
          print(f"清理: {cleaned}")
          if verbose and 'input' in item:
            print(f"輸入: {item['input'][:100]}...")
          print("-" * 50)

    print(f"\n總共 {total_count} 條記錄，其中 {processed_count} 條需要清理")

  except Exception as e:
    print(f"處理過程中發生錯誤: {str(e)}")
    sys.exit(1)


def load_json_data(input_file):
  """載入 JSON 資料，支援多種格式"""
  with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read().strip()

    # 檢查是否為 JSONL 格式
    if content.count('\n') > 0 and not content.startswith('['):
      data = []
      for line_num, line in enumerate(content.split('\n'), 1):
        if line.strip():
          try:
            data.append(json.loads(line.strip()))
          except json.JSONDecodeError as e:
            print(f"錯誤：第 {line_num} 行不是有效的 JSON: {e}")
            raise
    else:
      # 標準 JSON 格式
      data = json.loads(content)
      if not isinstance(data, list):
        data = [data]

  return data


def process_json_file(input_file, output_file, output_key='output',
    verbose=False):
  """
  處理 JSON 文件中的 commit messages

  Args:
      input_file (str): 輸入 JSON 文件路徑
      output_file (str): 輸出 JSON 文件路徑
      output_key (str): JSON 中需要處理的字段名，默認為 'output'
      verbose (bool): 是否顯示詳細信息
  """
  try:
    data = load_json_data(input_file)

    if verbose:
      print(f"處理文件: {input_file}")
      print(f"輸出文件: {output_file}")
      print(f"處理字段: {output_key}")
      print("=" * 60)

    processed_count = 0

    # 處理每個記錄
    for item in data:
      if isinstance(item, dict) and output_key in item:
        original = item[output_key]
        cleaned = clean_commit_message(original)
        if original != cleaned:
          if verbose:
            print(f"原始: {original}")
            print(f"清理: {cleaned}")
            print("-" * 50)
          processed_count += 1
        item[output_key] = cleaned

    # 寫入處理後的文件
    write_json_data(data, output_file, input_file)

    print(f"處理完成！共處理了 {processed_count} 條記錄")
    print(f"結果已保存到: {output_file}")

  except Exception as e:
    print(f"處理過程中發生錯誤: {str(e)}")
    sys.exit(1)


def write_json_data(data, output_file, input_file):
  """寫入 JSON 資料，保持原格式"""
  with open(output_file, 'w', encoding='utf-8') as f:
    # 判斷原始格式
    is_jsonl = input_file.endswith('.jsonl')
    if not is_jsonl:
      # 檢查原始文件內容來判斷格式
      with open(input_file, 'r', encoding='utf-8') as input_f:
        content = input_f.read().strip()
        is_jsonl = content.count('\n') > 0 and not content.startswith('[')

    if is_jsonl:
      # JSONL 格式輸出
      for item in data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')
    else:
      # 標準 JSON 格式輸出
      json.dump(data, f, ensure_ascii=False, indent=2)


def batch_clean_messages(messages):
  """
  批量清理 commit messages

  Args:
      messages (list): commit message 列表

  Returns:
      list: 清理後的 commit message 列表
  """
  return [clean_commit_message(msg) for msg in messages]


# CLI 使用範例
if __name__ == "__main__":
  # 如果沒有命令行參數，顯示測試範例
  if len(sys.argv) == 1:
    print("Commit Message Cleaner - 測試模式")
    print("=" * 50)

    # 測試單個消息清理
    test_messages = [
      'Polish "Avoid using deprecated NCSARequestLog"',
      'Fix "Update documentation"',
      'Polish remove unused imports',
      '"Add new feature"',
      'Refactor "Code cleanup"',
      "Make it easier to determine each servlet filter's order"
    ]

    print("測試消息清理：")
    for msg in test_messages:
      cleaned = clean_commit_message(msg)
      print(f"原始: {msg}")
      print(f"清理: {cleaned}")
      print()

    print("\nCLI 使用方法：")
    print("python commit_cleaner.py input.json output.json")
    print("python commit_cleaner.py --input data.json --output cleaned.json")
    print(
      "python commit_cleaner.py data.jsonl cleaned.jsonl --field commit_message")
    print("python commit_cleaner.py input.json --dry-run  # 僅預覽，不修改文件")
    print(
      "python commit_cleaner.py input.json output.json --verbose  # 顯示詳細信息")
    print("\n使用 --help 查看完整選項")
  else:
    main()