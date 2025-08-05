import json
import re
import argparse
from typing import Dict, List, Any
from pathlib import Path


def remove_issue_tags(commit_message: str) -> str:
  """
  移除 commit message 中的各種 Issue 標籤格式，保持結構

  Args:
      commit_message: 原始的 commit message

  Returns:
      移除標籤後的 commit message
  """
  # 擴展的 Issue 標籤模式
  patterns = [
    # GitHub style: #123, #761, fix #123
    r'\bfix\s+issue\s+#\d+:?\s*',
    r'\bfix\s+#\d+:?\s*',
    r'\bfixes\s+#\d+:?\s*',
    r'\bclose\s+#\d+:?\s*',
    r'\bcloses\s+#\d+:?\s*',
    r'\bresolve\s+#\d+:?\s*',
    r'\bresolves\s+#\d+:?\s*',
    r'\bissue\s+#\d+:?\s*',
    r'#\d+:?\s*',  # 單純的 #123:

    # JIRA style: PROJ-123, BS-157
    r'\b[A-Z]{2,10}-\d+:?\s*',

    # Issue: 格式 (原有的)
    r'\n\s*Issue:\s*[A-Z]*-?\w+\s*$',
    r'\s*Issue:\s*[A-Z]*-?\w+\s*$',
    r'\n\s*Issue:\s*[A-Z]*-?\w+',
    r'\s+Issue:\s*[A-Z]*-?\w+',

    # 數字開頭的編號: 1011:, 123:
    r'^\d+:\s*',  # 行首的數字編號
    r'\n\s*\*\s*\d+:\s*',  # 列表項目的數字編號

    # 常見的 issue 關鍵字
    r'\bticket\s+\d+:?\s*',
    r'\bbug\s+\d+:?\s*',
    r'\btask\s+\d+:?\s*',

    # 清理多餘的冒號和空格
    r':\s*$',  # 行末的冒號
  ]

  cleaned_message = commit_message

  # 依序套用各種模式
  for pattern in patterns:
    cleaned_message = re.sub(pattern, '', cleaned_message,
                             flags=re.IGNORECASE | re.MULTILINE)

  # 清理連續的空行，但保留正常的換行
  cleaned_message = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_message)  # 最多保留一個空行

  # 清理每行開頭和結尾的空白，但保留換行結構
  lines = cleaned_message.split('\n')
  cleaned_lines = [line.strip() for line in lines if
                   line.strip() or not line.strip()]
  cleaned_message = '\n'.join(cleaned_lines)

  # 只合併同一行內的多個空格，不影響換行
  cleaned_message = re.sub(r'[ \t]+', ' ', cleaned_message)

  # 清理整體開頭和結尾的空白
  cleaned_message = cleaned_message.strip()

  # 移除開頭的冒號（如果有的話）
  cleaned_message = re.sub(r'^:\s*', '', cleaned_message)

  # 如果結果為空或只有標點，返回通用消息
  if not cleaned_message or re.match(r'^[^\w]*$', cleaned_message):
    return "Update code"

  return cleaned_message


def analyze_issue_patterns(data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
  """分析資料中的各種 issue 模式"""
  patterns = {
    'github_hash': [],  # #123, fix #456
    'jira_style': [],  # PROJ-123, BS-157
    'issue_colon': [],  # Issue: BS-157
    'number_colon': [],  # 1011:, 123:
    'fix_issue': [],  # fix issue #123
    'other': []
  }

  for item in data:
    if 'output' not in item:
      continue

    output = item['output']

    # GitHub hash 格式
    if re.search(r'#\d+', output):
      patterns['github_hash'].append(output)

    # JIRA 格式
    elif re.search(r'\b[A-Z]{2,10}-\d+', output):
      patterns['jira_style'].append(output)

    # Issue: 格式
    elif re.search(r'Issue:\s*[A-Z]*-?\w+', output, re.IGNORECASE):
      patterns['issue_colon'].append(output)

    # 數字開頭
    elif re.search(r'^\d+:', output, re.MULTILINE):
      patterns['number_colon'].append(output)

    # fix issue 格式
    elif re.search(r'\bfix\s+issue\s+#?\d+', output, re.IGNORECASE):
      patterns['fix_issue'].append(output)

    # 其他可能包含 issue 相關字詞的
    elif re.search(r'\b(issue|bug|ticket|task)\s+\d+', output, re.IGNORECASE):
      patterns['other'].append(output)

  return patterns


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
    'patterns_found': {},
    'examples': []
  }

  # 先分析所有模式
  all_patterns = analyze_issue_patterns(data)

  for pattern_type, examples in all_patterns.items():
    if examples:
      stats['patterns_found'][pattern_type] = len(examples)

  for item in data:
    if 'output' in item:
      original = item['output']
      cleaned = remove_issue_tags(original)

      # 檢查是否包含任何 issue 相關內容
      has_issue = any([
        re.search(r'#\d+', original),
        re.search(r'\b[A-Z]{2,10}-\d+', original),
        re.search(r'Issue:\s*[A-Z]*-?\w+', original, re.IGNORECASE),
        re.search(r'^\d+:', original, re.MULTILINE),
        re.search(r'\b(fix|close|resolve)\s+(issue\s+)?#?\d+', original,
                  re.IGNORECASE),
        re.search(r'\b(issue|bug|ticket|task)\s+\d+', original, re.IGNORECASE)
      ])

      if has_issue:
        stats['issue_tags_found'] += 1

      # 保留原始資料結構，只修改 output 欄位
      processed_item = item.copy()
      processed_item['output'] = cleaned
      processed_data.append(processed_item)

      # 統計修改的項目並收集範例
      if original != cleaned:
        stats['modified'] += 1
        if len(stats['examples']) < 10:  # 只收集前10個範例
          stats['examples'].append({
            'original': original,
            'cleaned': cleaned
          })
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

    # 分析 issue 模式
    patterns = analyze_issue_patterns(data)
    total_issues = sum(len(examples) for examples in patterns.values())

    print(f"🏷️  發現的 Issue 模式分布:")
    for pattern_type, examples in patterns.items():
      if examples:
        print(f"   {pattern_type}: {len(examples):,} 筆")

    if total_issues == 0:
      print("✅ 沒有發現 Issue 標籤，無需處理")
      return

    # 處理資料
    processed_data, stats = process_json_data(data)

    # 儲存處理後的資料
    with open(output_file, 'w', encoding='utf-8') as f:
      json.dump(processed_data, f, ensure_ascii=False, indent=2)

    print(f"\n📋 處理結果:")
    print(f"   發現 Issue 相關: {stats['issue_tags_found']:,} 筆")
    print(f"   實際修改: {stats['modified']:,} 筆")
    print(f"✅ 處理完成，已儲存至: {Path(output_file).name}")

    # 顯示處理範例
    if stats['examples']:
      print(f"\n📝 處理範例:")
      for i, example in enumerate(stats['examples'][:5], 1):
        print(f"\n範例 {i}:")
        print(f"原始: {example['original']}")
        print(f"清理: {example['cleaned']}")
        print("-" * 60)

  except FileNotFoundError:
    print(f"❌ 錯誤: 找不到檔案 {input_file}")
  except json.JSONDecodeError:
    print(f"❌ 錯誤: {input_file} 不是有效的 JSON 檔案")
  except Exception as e:
    print(f"❌ 處理過程中發生錯誤: {str(e)}")


def test_patterns():
  """測試不同的 Issue 模式"""
  test_cases = [
    "Fix issue #761: ThreadSafeDoubleCheckLocking.java: Instantiating by Reflection call will be successful if you do that firstly",
    "1011: Fixed all of the SonarCloud blocking errors\n* 1011: Added the method to the RequestMapping annotation\n* 1011: Changed all of the a href blank targets to include rel=\"noopener noreferrer\"",
    "Add MultipartAutoConfigure to spring.factories\nUpdate META-INF/spring.factories to include MultipartAutoConfigure.\nAlso tweaked the class @Conditionals and Javadoc.\nIssue: BS-157",
    "Fix authentication bug\nIssue: JIRA-123",
    "Refactor database connection\nIssue:#456",
    "Update documentation Issue: DOC-789",
    "Simple commit without issue tag",
    "fix #123: Update user service",
    "closes #456 and resolves #789",
    "PROJ-123: Implement new feature",
    "feat: Java 21 update\n* update pom.xml and github actions scripts\n* disable failing tests, for now",
  ]

  print("🧪 測試 Issue 標籤移除:")
  print("=" * 80)

  for i, test_case in enumerate(test_cases, 1):
    print(f"\n測試 {i}:")
    print(f"原始: {test_case}")
    cleaned = remove_issue_tags(test_case)
    print(f"清理: {cleaned}")
    print(f"變化: {'✅ 有變化' if test_case != cleaned else '❌ 無變化'}")


def main():
  """主函數"""
  parser = argparse.ArgumentParser(
      description='移除 Git commit message 中的各種 Issue 標籤格式',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog='''
範例:
  python remove_issues.py data.json                    # 基本用法
  python remove_issues.py data.json -o clean_data.json # 指定輸出檔案
  python remove_issues.py --test                       # 測試正規表達式

支援的標籤格式:
  GitHub: #123, fix #456, closes #789
  JIRA: PROJ-123, BS-157, TASK-456
  Issue: Issue: BS-157, Issue: JIRA-123
  數字: 1011:, 123:
  關鍵字: fix issue #123, bug 456, ticket 789

處理策略:
  - 移除各種格式的 Issue 標籤和編號
  - 保持 commit message 的核心內容
  - 清理多餘的空格和換行
        '''
  )

  parser.add_argument('input_file', nargs='?', help='輸入的 JSON 檔案路徑')
  parser.add_argument('-o', '--output',
                      help='輸出檔案路徑 (預設: 原檔名_no_issues.json)')
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

  process_file(args.input_file, args.output)


if __name__ == "__main__":
  main()