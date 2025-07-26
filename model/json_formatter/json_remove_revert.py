import json
import re
import argparse
from pathlib import Path


def is_revert_commit(text):
  """檢查是否為 revert commit"""
  if not text or not isinstance(text, str):
    return False

  text_lower = text.lower().strip()

  # 檢查各種 revert 模式
  revert_patterns = [
    r'\brevert\b',  # 包含 revert 單詞
    r'\breverting\b',  # 包含 reverting 單詞
    r'this reverts',  # this reverts commit
    r'reverts commit',  # reverts commit
  ]

  for pattern in revert_patterns:
    if re.search(pattern, text_lower):
      return True

  return False


def remove_revert_commits(input_file, output_file=None):
  """移除所有 revert commit"""
  input_path = Path(input_file)

  if output_file is None:
    output_file = input_path.parent / f"{input_path.stem}_no_reverts{input_path.suffix}"

  # 讀取資料
  with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

  print(f"📂 處理檔案: {input_path.name}")
  print(f"📊 原始資料: {len(data):,} 筆")

  # 過濾資料
  filtered_data = []
  removed_count = 0

  for item in data:
    if isinstance(item, dict) and 'output' in item:
      if is_revert_commit(item['output']):
        removed_count += 1
      else:
        filtered_data.append(item)
    else:
      filtered_data.append(item)

  # 儲存結果
  with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f, ensure_ascii=False, indent=2)

  print(f"❌ 移除 revert: {removed_count:,} 筆")
  print(
    f"✅ 保留資料: {len(filtered_data):,} 筆 ({len(filtered_data) / len(data) * 100:.1f}%)")
  print(f"📁 輸出檔案: {Path(output_file).name}")


def preview_revert_commits(input_file, max_examples=5):
  """預覽會被移除的 revert commit"""
  with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

  print(f"📂 分析檔案: {Path(input_file).name}")
  print(f"📊 總資料筆數: {len(data):,}")

  revert_examples = []
  revert_count = 0

  for item in data:
    if isinstance(item, dict) and 'output' in item:
      if is_revert_commit(item['output']):
        revert_count += 1
        if len(revert_examples) < max_examples:
          revert_examples.append(item['output'])

  print(
    f"🔍 發現 revert: {revert_count:,} 筆 ({revert_count / len(data) * 100:.1f}%)")

  if revert_examples:
    print(f"\n📝 Revert 範例:")
    for i, example in enumerate(revert_examples, 1):
      print(f"{i}. {example}")
  else:
    print("✅ 沒有發現 revert commit")


def test_revert_detection():
  """測試 revert 偵測功能"""
  test_cases = [
    # 應該被移除的
    'Revert "Add text/plain error response support"',
    'revert: Add user authentication',
    'Reverting changes to database schema',
    'This reverts commit 23892e33d6ed73a130850d27342dba631b9fb8d7',
    'Fix bug\n\nThis reverts commit abc123',
    'Revert changes made in previous commit',
    'REVERT: Remove deprecated API',

    # 應該保留的
    'Fix authentication bug',
    'Add user service',
    'Remove deprecated methods',
    'Polish code formatting',
    'Prevent memory leaks',
    'Reverse order of elements',  # reverse 不是 revert
    'Convert string to integer',
  ]

  print("🧪 測試 Revert 偵測:")
  print("=" * 50)

  for i, test_case in enumerate(test_cases, 1):
    is_revert = is_revert_commit(test_case)
    status = "❌ 移除" if is_revert else "✅ 保留"
    print(f"{i:2d}. {status} - {test_case}")


def main():
  """主函數"""
  parser = argparse.ArgumentParser(
      description='移除所有 revert commit 訓練資料',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog='''
為什麼移除 revert？
- revert 不是基於 diff 生成的
- 對訓練 commit message 沒有幫助
- 會混淆模型的學習

範例:
  python remove_reverts.py data.json              # 移除 revert
  python remove_reverts.py data.json --preview    # 預覽會移除的
  python remove_reverts.py --test                 # 測試偵測功能
  python remove_reverts.py data.json -o clean.json # 指定輸出檔案

會被移除的格式:
  "Revert 'Add text/plain error response support'"
  "revert: Add user authentication"  
  "Reverting changes to database schema"
  "This reverts commit abc123"
        '''
  )

  parser.add_argument('input_file', nargs='?', help='輸入的 JSON 檔案路徑')
  parser.add_argument('-o', '--output', help='輸出檔案路徑')
  parser.add_argument('--preview', action='store_true',
                      help='預覽會被移除的 revert')
  parser.add_argument('--test', action='store_true', help='測試 revert 偵測')

  args = parser.parse_args()

  if args.test:
    test_revert_detection()
    return

  if not args.input_file:
    print("❌ 錯誤: 請提供輸入檔案路徑")
    parser.print_help()
    return

  if not Path(args.input_file).exists():
    print(f"❌ 錯誤: 找不到檔案 {args.input_file}")
    return

  try:
    if args.preview:
      preview_revert_commits(args.input_file)
    else:
      remove_revert_commits(args.input_file, args.output)
      print("🎉 處理完成！")
  except Exception as e:
    print(f"❌ 處理失敗: {e}")


if __name__ == "__main__":
  main()