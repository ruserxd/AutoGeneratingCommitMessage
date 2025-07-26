import json
import sys
import argparse
from pathlib import Path
from transformers import RobertaTokenizer


def count_tokens(text, tokenizer):
  """計算文本的 token 數量"""
  if not text or not isinstance(text, str):
    return 0

  try:
    tokens = tokenizer.encode(text, add_special_tokens=True,
                              max_length=10000, truncation=False)
    return len(tokens)
  except Exception:
    # 如果文本太長導致錯誤，估算長度
    return len(text.split()) * 1.3  # 粗略的 token 估算


def filter_json_by_length(input_file, max_input_length=2400,
    max_output_length=120):
  """
  過濾 JSON 檔案，移除超長的記錄
  預設使用完整設定以保留最多資料
  """

  # 初始化 tokenizer
  print("🔄 載入 tokenizer...")
  try:
    tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
    print("✅ Tokenizer 載入成功")
  except Exception as e:
    print(f"❌ 錯誤: 無法載入 tokenizer: {e}")
    return False

  # 讀取檔案
  input_path = Path(input_file)
  if not input_path.exists():
    print(f"❌ 錯誤: 檔案不存在 - {input_file}")
    return False

  print(f"📖 讀取檔案: {input_path.name}")
  try:
    with open(input_path, 'r', encoding='utf-8') as f:
      data = json.load(f)
  except json.JSONDecodeError as e:
    print(f"❌ 錯誤: JSON 格式錯誤 - {e}")
    return False
  except Exception as e:
    print(f"❌ 錯誤: 無法讀取檔案 - {e}")
    return False

  # 確保資料是列表格式
  if not isinstance(data, list):
    if isinstance(data, dict):
      data = [data]
    else:
      print("❌ 錯誤: JSON 檔案必須包含列表或字典")
      return False

  # 統計資訊
  stats = {
    'total': len(data),
    'kept': 0,
    'removed_input': 0,
    'removed_output': 0,
    'removed_both': 0,
    'removed_invalid': 0
  }

  # 過濾資料
  filtered_data = []
  removed_examples = []

  print(f"🔍 開始過濾 {stats['total']:,} 筆記錄...")
  print(f"📏 長度限制: INPUT ≤ {max_input_length}, OUTPUT ≤ {max_output_length}")

  for i, item in enumerate(data):
    # 進度顯示
    if (i + 1) % 1000 == 0:
      print(f"  已處理 {i + 1:,} 筆...")

    # 檢查資料格式
    if not isinstance(item,
                      dict) or 'input' not in item or 'output' not in item:
      stats['removed_invalid'] += 1
      continue

    input_text = item['input']
    output_text = item['output']

    # 計算長度
    input_length = count_tokens(input_text, tokenizer)
    output_length = count_tokens(output_text, tokenizer)

    # 判斷是否超長
    input_too_long = input_length > max_input_length
    output_too_long = output_length > max_output_length

    if input_too_long and output_too_long:
      stats['removed_both'] += 1
      if len(removed_examples) < 3:
        removed_examples.append(
          f"記錄 {i + 1}: input({input_length}) + output({output_length}) 都超長")
    elif input_too_long:
      stats['removed_input'] += 1
      if len(removed_examples) < 3:
        removed_examples.append(f"記錄 {i + 1}: input({input_length}) 超長")
    elif output_too_long:
      stats['removed_output'] += 1
      if len(removed_examples) < 3:
        removed_examples.append(f"記錄 {i + 1}: output({output_length}) 超長")
    else:
      # 保留這筆記錄
      filtered_data.append(item)
      stats['kept'] += 1

  # 生成輸出檔案名
  output_path = input_path.parent / f"{input_path.stem}_filtered{input_path.suffix}"

  # 儲存結果
  print(f"💾 儲存過濾結果...")
  try:
    with open(output_path, 'w', encoding='utf-8') as f:
      json.dump(filtered_data, f, ensure_ascii=False, indent=2)
  except Exception as e:
    print(f"❌ 錯誤: 無法儲存檔案 - {e}")
    return False

  # 計算統計數據
  total_removed = stats['total'] - stats['kept']
  keep_ratio = stats['kept'] / stats['total'] * 100

  # 顯示結果報告
  print(f"\n{'=' * 50}")
  print("🎉 過濾完成！")
  print(f"{'=' * 50}")
  print(f"📊 總記錄數:     {stats['total']:,}")
  print(f"✅ 保留記錄:     {stats['kept']:,} ({keep_ratio:.1f}%)")
  print(f"❌ 移除記錄:     {total_removed:,} ({100 - keep_ratio:.1f}%)")

  if total_removed > 0:
    print(f"\n📋 移除原因分析:")
    print(f"   🔴 INPUT 超長:     {stats['removed_input']:,}")
    print(f"   🔴 OUTPUT 超長:    {stats['removed_output']:,}")
    print(f"   🔴 兩者都超長:     {stats['removed_both']:,}")
    if stats['removed_invalid'] > 0:
      print(f"   🔴 格式不正確:     {stats['removed_invalid']:,}")

  print(f"\n📂 檔案輸出:")
  print(f"   輸入: {input_path.name}")
  print(f"   輸出: {output_path.name}")

  if removed_examples:
    print(f"\n🔍 移除範例:")
    for example in removed_examples:
      print(f"   {example}")

  # 建議下一步
  print(f"\n💡 下一步建議:")
  if keep_ratio >= 90:
    print("   ✅ 保留率很高，可以直接用於訓練")
  elif keep_ratio >= 80:
    print("   ⚠️  保留率中等，建議檢查移除的記錄是否重要")
  else:
    print("   🚨 保留率較低，考慮增加長度限制或檢查資料品質")

  print(f"   📝 更新 training.py 中的設定:")
  print(
    f"      max_input_length={max_input_length}, max_target_length={max_output_length}")

  return True


def main():
  """主函式"""
  parser = argparse.ArgumentParser(
      description="過濾 JSON 訓練資料，移除超出長度限制的記錄",
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog="""
🎯 預設設定 (完整設定，保留最多資料):
  --max-input 2400 --max-output 120

🔥 快速使用:
  python filter_json.py data.json                    # 使用預設設定
  python filter_json.py data.json --max-input 1600   # 自定義INPUT長度
  python filter_json.py *.json                       # 批量處理

📊 基於實際分析的建議設定:
  完整設定: --max-input 2400 --max-output 120  (保留90-95%資料)
  平衡設定: --max-input 1600 --max-output 80   (保留80-85%資料)  
  高效設定: --max-input 1200 --max-output 50   (保留65-70%資料)
        """
  )

  parser.add_argument('json_files', nargs='+',
                      help='JSON 檔案路徑 (支援多檔案)')
  parser.add_argument('--max-input', type=int, default=2400,
                      help='最大 input 長度 (tokens, 預設: 2400)')
  parser.add_argument('--max-output', type=int, default=120,
                      help='最大 output 長度 (tokens, 預設: 120)')

  args = parser.parse_args()

  # 驗證參數
  if args.max_input <= 0 or args.max_output <= 0:
    print("❌ 錯誤: 長度限制必須大於 0")
    sys.exit(1)

  # 處理多個檔案
  successful = 0
  failed = 0

  for json_file in args.json_files:
    print(f"\n{'🔄 處理檔案: ' + json_file:=^60}")

    success = filter_json_by_length(
        json_file,
        max_input_length=args.max_input,
        max_output_length=args.max_output
    )

    if success:
      successful += 1
    else:
      failed += 1

  # 總體結果
  total_files = len(args.json_files)
  print(f"\n{'🏁 處理完成':=^60}")
  print(f"✅ 成功處理: {successful}/{total_files} 個檔案")
  if failed > 0:
    print(f"❌ 處理失敗: {failed}/{total_files} 個檔案")

  if successful == total_files:
    print("\n🎉 所有檔案處理成功！可以開始訓練了！")
    sys.exit(0)
  else:
    sys.exit(1)


if __name__ == "__main__":
  main()