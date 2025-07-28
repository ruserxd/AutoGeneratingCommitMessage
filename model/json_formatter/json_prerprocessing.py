import json
import argparse
from pathlib import Path
from transformers import RobertaTokenizer


def count_tokens(text, tokenizer):
  """計算文本的 token 數量"""
  if not text or not isinstance(text, str):
    return 0

  try:
    tokens = tokenizer.encode(text, add_special_tokens=True, truncation=False)
    return len(tokens)
  except Exception:
    return len(text.split()) * 1.3  # 粗略估算


def filter_json_by_length(input_file, max_input_length=1600,
    max_output_length=64):
  """過濾 JSON 檔案，移除超長的記錄"""

  # 載入 tokenizer
  print("🔄 載入 tokenizer...")
  try:
    tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
    print("✅ Tokenizer 載入成功")
  except Exception as e:
    print(f"❌ 無法載入 tokenizer: {e}")
    return False

  # 讀取檔案
  input_path = Path(input_file)
  if not input_path.exists():
    print(f"❌ 檔案不存在: {input_file}")
    return False

  print(f"📖 讀取檔案: {input_path.name}")
  try:
    with open(input_path, 'r', encoding='utf-8') as f:
      data = json.load(f)
  except Exception as e:
    print(f"❌ 讀取檔案失敗: {e}")
    return False

  if not isinstance(data, list):
    print("❌ JSON 檔案必須包含列表格式")
    return False

  # 過濾資料
  filtered_data = []
  removed_count = 0

  print(f"🔍 開始過濾 {len(data):,} 筆記錄...")

  for i, item in enumerate(data):
    # 檢查格式
    if not isinstance(item,
                      dict) or 'input' not in item or 'output' not in item:
      removed_count += 1
      continue

    # 計算長度
    input_length = count_tokens(item['input'], tokenizer)
    output_length = count_tokens(item['output'], tokenizer)

    # 檢查是否超長
    if input_length <= max_input_length and output_length <= max_output_length:
      filtered_data.append(item)
    else:
      removed_count += 1

  # 儲存結果
  output_path = input_path.parent / f"{input_path.stem}_filtered{input_path.suffix}"

  try:
    with open(output_path, 'w', encoding='utf-8') as f:
      json.dump(filtered_data, f, ensure_ascii=False, indent=2)
  except Exception as e:
    print(f"❌ 儲存失敗: {e}")
    return False

  # 顯示結果
  total = len(data)
  kept = len(filtered_data)
  keep_ratio = kept / total * 100

  print(f"\n{'=' * 40}")
  print("🎉 過濾完成！")
  print(f"{'=' * 40}")
  print(f"📊 總記錄:   {total:,}")
  print(f"✅ 保留:     {kept:,} ({keep_ratio:.1f}%)")
  print(f"❌ 移除:     {removed_count:,} ({100 - keep_ratio:.1f}%)")
  print(f"📂 輸出:     {output_path.name}")

  # 建議
  if keep_ratio >= 90:
    print("💡 保留率很高，可以直接訓練")
  elif keep_ratio >= 70:
    print("💡 保留率中等，建議檢查資料")
  else:
    print("💡 保留率較低，考慮調整長度限制")

  return True


def main():
  """主函式"""
  parser = argparse.ArgumentParser(description="過濾 JSON 訓練資料")
  parser.add_argument('json_file', help='JSON 檔案路徑')
  parser.add_argument('--max-input', type=int, default=1600,
                      help='最大 input 長度 (預設: 1600)')
  parser.add_argument('--max-output', type=int, default=64,
                      help='最大 output 長度 (預設: 64)')

  args = parser.parse_args()

  # 驗證參數
  if args.max_input <= 0 or args.max_output <= 0:
    print("❌ 長度限制必須大於 0")
    return

  # 執行過濾
  success = filter_json_by_length(
      args.json_file,
      max_input_length=args.max_input,
      max_output_length=args.max_output
  )

  if success:
    print("\n🎉 處理成功！可以開始訓練了！")
  else:
    print("\n❌ 處理失敗")


if __name__ == "__main__":
  main()