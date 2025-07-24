import json
import re
import argparse
from typing import Dict, List, Any
from pathlib import Path


def remove_ticket_tags(commit_message: str) -> str:
  """
  移除 commit message 中的 [#數字] 票號標籤，並加入換行保持結構

  Args:
      commit_message: 原始的 commit message

  Returns:
      移除標籤後的 commit message
  """
  # 移除 [#數字] 格式的票號標籤，並替換為換行符
  pattern = r'\[#\d+\]\s*'
  cleaned_message = re.sub(pattern, '\n', commit_message, flags=re.IGNORECASE)

  # 清理多餘的換行符（超過2個連續換行變成1個）
  cleaned_message = re.sub(r'\n{3,}', '\n\n', cleaned_message)

  # 清理每行多餘的空白
  lines = cleaned_message.split('\n')
  cleaned_lines = [line.strip() for line in lines if line.strip()]

  # 重新組合，保持適當的結構
  if len(cleaned_lines) <= 1:
    return cleaned_lines[0] if cleaned_lines else ""
  else:
    return '\n'.join(cleaned_lines)


def process_json_data(data: List[Dict[str, Any]]) -> tuple[
  List[Dict[str, Any]], Dict[str, int]]:
  """
  處理 JSON 資料，移除所有 output 欄位中的票號標籤

  Args:
      data: 包含訓練資料的 JSON 陣列

  Returns:
      處理後的 JSON 資料和統計資訊
  """
  processed_data = []
  stats = {
    'total': len(data),
    'ticket_tags_found': 0,
    'modified': 0
  }

  for item in data:
    if 'output' in item:
      original = item['output']
      cleaned = remove_ticket_tags(original)

      # 統計票號標籤
      if re.search(r'\[#\d+\]', original, re.IGNORECASE):
        stats['ticket_tags_found'] += 1

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
    output_file = input_path.parent / f"{input_path.stem}_no_tickets{input_path.suffix}"

  try:
    # 讀取 JSON 檔案
    with open(input_file, 'r', encoding='utf-8') as f:
      data = json.load(f)

    print(f"📂 載入檔案: {input_path.name}")
    print(f"📊 總資料筆數: {len(data):,}")

    # 預先統計包含票號標籤的資料
    ticket_count = 0
    for item in data:
      if 'output' in item and re.search(r'\[#\d+\]', item['output'],
                                        re.IGNORECASE):
        ticket_count += 1

    print(f"🎫 包含 [#xxxx] 票號標籤的資料: {ticket_count:,} 筆")

    if ticket_count == 0:
      print("✅ 沒有發現票號標籤，無需處理")
      return

    # 處理資料
    processed_data, stats = process_json_data(data)

    # 儲存處理後的資料
    with open(output_file, 'w', encoding='utf-8') as f:
      json.dump(processed_data, f, ensure_ascii=False, indent=2)

    print(f"\n📋 處理結果:")
    print(f"   發現票號標籤: {stats['ticket_tags_found']:,} 筆")
    print(f"   實際修改: {stats['modified']:,} 筆")
    print(f"✅ 處理完成，已儲存至: {Path(output_file).name}")

    # 顯示處理範例
    if stats['modified'] > 0:
      print(f"\n📝 處理範例:")
      count = 0
      for original_item, processed_item in zip(data, processed_data):
        if ('output' in original_item and
            original_item['output'] != processed_item['output'] and
            re.search(r'\[#\d+\]', original_item['output'], re.IGNORECASE)):

          original = original_item['output']
          cleaned = processed_item['output']

          print(f"原始: {repr(original)}")  # 用 repr 顯示換行符
          print(f"清理: {repr(cleaned)}")
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

    # 找出包含票號標籤的項目
    ticket_items = []
    for i, item in enumerate(data):
      if 'output' in item and re.search(r'\[#\d+\]', item['output'],
                                        re.IGNORECASE):
        original = item['output']
        cleaned = remove_ticket_tags(original)
        if original != cleaned:
          ticket_items.append((i + 1, original, cleaned))

    print(f"包含票號標籤的資料: {len(ticket_items):,} 筆")

    if len(ticket_items) == 0:
      print("✅ 沒有發現需要清理的票號標籤")
      return

    # 顯示前5筆會被處理的資料
    print(f"\n📝 預覽前 5 筆會被修改的資料:")
    for i, (idx, original, cleaned) in enumerate(ticket_items[:5]):
      print(f"\n第 {idx} 筆:")
      print(f"原始: {repr(original)}")  # 用 repr 顯示換行符
      print(f"清理: {repr(cleaned)}")
      print(f"視覺化:")
      print(f"  原始: {original}")
      print(f"  清理: {cleaned}")
      print("-" * 40)

    if len(ticket_items) > 5:
      print(f"\n... 還有 {len(ticket_items) - 5:,} 筆類似資料")

    # 統計不同的票號格式
    ticket_patterns = {}
    for _, original, _ in ticket_items:
      matches = re.findall(r'\[#\d+\]', original, re.IGNORECASE)
      for match in matches:
        ticket_patterns[match] = ticket_patterns.get(match, 0) + 1

    if ticket_patterns:
      print(f"\n🎫 發現的票號標籤類型 (前10個):")
      sorted_patterns = sorted(ticket_patterns.items(), key=lambda x: x[1],
                               reverse=True)
      for pattern, count in sorted_patterns[:10]:
        print(f"   {pattern}: {count} 次")

  except Exception as e:
    print(f"❌ 預覽失敗: {str(e)}")


def main():
  """主函數"""
  parser = argparse.ArgumentParser(
      description='移除 Git commit message 中的票號標籤 [#數字]，保持結構',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog='''
範例:
  python remove_tickets.py data.json                    # 基本用法
  python remove_tickets.py data.json -o clean_data.json # 指定輸出檔案
  python remove_tickets.py data.json --preview          # 預覽模式

會處理的標籤格式:
  [#48127729] → 替換為換行符，保持結構
  [#12345]    → 替換為換行符，保持結構
  [#999999]   → 替換為換行符，保持結構

修改策略:
  - 用換行符替換票號標籤
  - 保持 commit message 的多行結構
  - 避免把有意義的分段合併成一行
        '''
  )

  parser.add_argument('input_file', help='輸入的 JSON 檔案路徑')
  parser.add_argument('-o', '--output',
                      help='輸出檔案路徑 (預設: 原檔名_no_tickets.json)')
  parser.add_argument('--preview', action='store_true',
                      help='預覽模式，只顯示會被處理的資料')

  args = parser.parse_args()

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