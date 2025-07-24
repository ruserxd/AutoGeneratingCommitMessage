import json
import re
import argparse
from typing import Dict, List, Any
from pathlib import Path


def remove_issue_tags(commit_message: str) -> str:
  """
  移除 commit message 中的 Issue 標籤，保持結構

  Args:
      commit_message: 原始的 commit message

  Returns:
      移除標籤後的 commit message
  """
  # 移除 Issue: xxx 格式的標籤（通常在結尾）
  # 支援多種格式：Issue: BS-157, Issue:#123, Issue:PROJ-999
  patterns = [
    r'\n\s*Issue:\s*[A-Z]*-?\w+\s*$',  # 換行後的 Issue: BS-157
    r'\s*Issue:\s*[A-Z]*-?\w+\s*$',  # 行末的 Issue: BS-157
    r'\n\s*Issue:\s*[A-Z]*-?\w+',  # 換行後的 Issue (不在結尾)
    r'\s+Issue:\s*[A-Z]*-?\w+',  # 空格後的 Issue
  ]

  cleaned_message = commit_message

  # 依序套用各種模式
  for pattern in patterns:
    cleaned_message = re.sub(pattern, '', cleaned_message, flags=re.IGNORECASE)

  # 清理多餘的空白和換行
  lines = cleaned_message.split('\n')
  cleaned_lines = [line.strip() for line in lines if line.strip()]

  # 重新組合
  if len(cleaned_lines) <= 1:
    return cleaned_lines[0] if cleaned_lines else ""
  else:
    return '\n'.join(cleaned_lines)


def process_json_data(data: List[Dict[str, Any]]) -> tuple[
  List[Dict[str, Any]], Dict[str, int]]:
  """
  處理 JSON 資料，移除所有 output 欄位中的 Issue 標籤

  Args:
      data: 包含訓練資料的 JSON 陣列

  Returns:
      處理後的 JSON 資料和統計資訊
  """
  processed_data = []
  stats = {
    'total': len(data),
    'issue_tags_found': 0,
    'modified': 0,
    'issue_patterns': {}
  }

  for item in data:
    if 'output' in item:
      original = item['output']
      cleaned = remove_issue_tags(original)

      # 統計 Issue 標籤
      if re.search(r'Issue:\s*[A-Z]*-?\w+', original, re.IGNORECASE):
        stats['issue_tags_found'] += 1

        # 收集不同的 Issue 模式
        matches = re.findall(r'Issue:\s*([A-Z]*-?\w+)', original, re.IGNORECASE)
        for match in matches:
          stats['issue_patterns'][match] = stats['issue_patterns'].get(match,
                                                                       0) + 1

      # 保留原始資料結構，只修改 output 欄位
      processed_item = item.copy()
      processed_item['output'] = cleaned
      processed_data.append(processed_item)

      # 統計修改的項目
      if original != cleaned:
        stats['modified'] += 1
    else:
      # 如果沒有 output 欄位，保持原樣
      processed_data.append(item)

  return processed_data, stats


def process_file(input_file: str, output_file: str = None) -> None:
  """
  處理 JSON 檔案

  Args:
      input_file: 輸入檔案路徑
      output_file: 輸出檔案路徑（可選）
  """
  input_path = Path(input_file)

  # 設定輸出檔案路徑
  if output_file is None:
    output_file = input_path.parent / f"{input_path.stem}_no_issues{input_path.suffix}"

  try:
    # 讀取 JSON 檔案
    with open(input_file, 'r', encoding='utf-8') as f:
      data = json.load(f)

    print(f"📂 載入檔案: {input_path.name}")
    print(f"📊 總資料筆數: {len(data):,}")

    # 預先統計包含 Issue 標籤的資料
    issue_count = 0
    for item in data:
      if 'output' in item and re.search(r'Issue:\s*[A-Z]*-?\w+', item['output'],
                                        re.IGNORECASE):
        issue_count += 1

    print(f"🏷️  包含 Issue: 標籤的資料: {issue_count:,} 筆")

    if issue_count == 0:
      print("✅ 沒有發現 Issue 標籤，無需處理")
      return

    # 處理資料
    processed_data, stats = process_json_data(data)

    # 儲存處理後的資料
    with open(output_file, 'w', encoding='utf-8') as f:
      json.dump(processed_data, f, ensure_ascii=False, indent=2)

    print(f"\n📋 處理結果:")
    print(f"   發現 Issue 標籤: {stats['issue_tags_found']:,} 筆")
    print(f"   實際修改: {stats['modified']:,} 筆")
    print(f"✅ 處理完成，已儲存至: {Path(output_file).name}")

    # 顯示 Issue 模式統計
    if stats['issue_patterns']:
      print(f"\n📈 發現的 Issue 類型 (前10個):")
      sorted_patterns = sorted(stats['issue_patterns'].items(),
                               key=lambda x: x[1], reverse=True)
      for pattern, count in sorted_patterns[:10]:
        print(f"   Issue: {pattern} - {count} 次")

    # 顯示處理範例
    if stats['modified'] > 0:
      print(f"\n📝 處理範例:")
      count = 0
      for original_item, processed_item in zip(data, processed_data):
        if ('output' in original_item and
            original_item['output'] != processed_item['output'] and
            re.search(r'Issue:\s*[A-Z]*-?\w+', original_item['output'],
                      re.IGNORECASE)):

          original = original_item['output']
          cleaned = processed_item['output']

          print(f"原始: {repr(original)}")
          print(f"清理: {repr(cleaned)}")
          print(f"視覺化:")
          print(f"  原始: {original}")
          print(f"  清理: {cleaned}")
          print("-" * 60)

          count += 1
          if count >= 3:  # 只顯示前3個範例
            break

  except FileNotFoundError:
    print(f"❌ 錯誤: 找不到檔案 {input_file}")
  except json.JSONDecodeError:
    print(f"❌ 錯誤: {input_file} 不是有效的 JSON 檔案")
  except Exception as e:
    print(f"❌ 處理過程中發生錯誤: {str(e)}")


def preview_changes(input_file: str) -> None:
  """預覽會被修改的資料"""
  try:
    with open(input_file, 'r', encoding='utf-8') as f:
      data = json.load(f)

    print(f"📋 預覽模式 - {Path(input_file).name}")
    print(f"總資料筆數: {len(data):,}")

    # 找出包含 Issue 標籤的項目
    issue_items = []
    issue_patterns = {}

    for i, item in enumerate(data):
      if 'output' in item and re.search(r'Issue:\s*[A-Z]*-?\w+', item['output'],
                                        re.IGNORECASE):
        original = item['output']
        cleaned = remove_issue_tags(original)
        if original != cleaned:
          issue_items.append((i + 1, original, cleaned))

          # 收集 Issue 模式
          matches = re.findall(r'Issue:\s*([A-Z]*-?\w+)', original,
                               re.IGNORECASE)
          for match in matches:
            issue_patterns[match] = issue_patterns.get(match, 0) + 1

    print(f"包含 Issue 標籤的資料: {len(issue_items):,} 筆")

    if len(issue_items) == 0:
      print("✅ 沒有發現需要清理的 Issue 標籤")
      return

    # 顯示 Issue 模式統計
    if issue_patterns:
      print(f"\n🏷️  發現的 Issue 類型:")
      sorted_patterns = sorted(issue_patterns.items(), key=lambda x: x[1],
                               reverse=True)
      for pattern, count in sorted_patterns:
        print(f"   Issue: {pattern} - {count} 次")

    # 顯示前5筆會被處理的資料
    print(f"\n📝 預覽前 5 筆會被修改的資料:")
    for i, (idx, original, cleaned) in enumerate(issue_items[:5]):
      print(f"\n第 {idx} 筆:")
      print(f"原始: {repr(original)}")
      print(f"清理: {repr(cleaned)}")
      print(f"視覺化:")
      print(f"  原始: {original}")
      print(f"  清理: {cleaned}")
      print("-" * 40)

    if len(issue_items) > 5:
      print(f"\n... 還有 {len(issue_items) - 5:,} 筆類似資料")

  except Exception as e:
    print(f"❌ 預覽失敗: {str(e)}")


def test_patterns():
  """測試不同的 Issue 模式"""
  test_cases = [
    "Add MultipartAutoConfigure to spring.factories\nUpdate META-INF/spring.factories to include MultipartAutoConfigure.\nAlso tweaked the class @Conditionals and Javadoc.\nIssue: BS-157",
    "Fix authentication bug\nIssue: JIRA-123",
    "Refactor database connection\nIssue:#456",
    "Update documentation Issue: DOC-789",
    "Simple commit without issue tag"
  ]

  print("🧪 測試 Issue 標籤移除:")
  print("=" * 60)

  for i, test_case in enumerate(test_cases, 1):
    print(f"\n測試 {i}:")
    print(f"原始: {repr(test_case)}")
    cleaned = remove_issue_tags(test_case)
    print(f"清理: {repr(cleaned)}")
    print(f"視覺化:")
    print(f"  原始: {test_case}")
    print(f"  清理: {cleaned}")


def main():
  """主函數"""
  parser = argparse.ArgumentParser(
      description='移除 Git commit message 中的 Issue 標籤',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog='''
範例:
  python remove_issues.py data.json                    # 基本用法
  python remove_issues.py data.json -o clean_data.json # 指定輸出檔案
  python remove_issues.py data.json --preview          # 預覽模式
  python remove_issues.py --test                       # 測試正規表達式

會處理的標籤格式:
  Issue: BS-157    → 移除
  Issue: JIRA-123  → 移除
  Issue:#456       → 移除
  Issue: DOC-789   → 移除

處理策略:
  - 移除各種格式的 Issue 標籤
  - 保持 commit message 的多行結構
  - 通常移除最後一行的 Issue 標籤
        '''
  )

  parser.add_argument('input_file', nargs='?', help='輸入的 JSON 檔案路徑')
  parser.add_argument('-o', '--output',
                      help='輸出檔案路徑 (預設: 原檔名_no_issues.json)')
  parser.add_argument('--preview', action='store_true',
                      help='預覽模式，只顯示會被處理的資料')
  parser.add_argument('--test', action='store_true', help='測試正規表達式模式')

  args = parser.parse_args()

  if args.test:
    test_patterns()
    return

  if not args.input_file:
    print("❌ 錯誤: 請提供輸入檔案路徑")
    parser.print_help()
    return

  # 檢查檔案是否存在
  if not Path(args.input_file).exists():
    print(f"❌ 錯誤: 找不到檔案 {args.input_file}")
    return

  if args.preview:
    preview_changes(args.input_file)
  else:
    process_file(args.input_file, args.output)


if __name__ == "__main__":
  main()