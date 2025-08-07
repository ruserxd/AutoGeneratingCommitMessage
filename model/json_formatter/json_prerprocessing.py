import json
import argparse
from pathlib import Path
from transformers import RobertaTokenizer


def load_config(config_file='../config.json'):
  """載入設定檔"""
  config_path = Path(config_file)
  print(f"🔍 尋找設定檔: {config_path.resolve()}")

  try:
    with open(config_path, 'r', encoding='utf-8') as f:
      config = json.load(f)
    print(f"✅ 載入設定檔: {config_file}")
    return config
  except FileNotFoundError:
    print(f"❌ 找不到設定檔: {config_path.resolve()}")
    print("使用預設設定")
    return {"max_input": 512, "max_output": 512}
  except Exception as e:
    print(f"❌ 載入設定檔失敗: {e}")
    return {"max_input": 512, "max_output": 512}


def count_tokens(text, tokenizer):
  """計算 token 數量"""
  if not text:
    return 0
  try:
    return len(tokenizer.encode(text, truncation=False))
  except:
    return len(text.split())


def filter_json_by_length(input_file, config_file='../config.json'):
  """過濾 JSON 檔案"""

  # 載入設定
  config = load_config(config_file)
  max_input = config.get('max_input', 512)
  max_output = config.get('max_output', 512)
  model_name = config.get('model_name', 'Salesforce/codet5-base')

  print(f"🔧 設定: input≤{max_input}, output≤{max_output}")

  # 載入 tokenizer
  print(f"🔄 載入 tokenizer...")
  try:
    tokenizer = RobertaTokenizer.from_pretrained(model_name)
    print("✅ 載入成功")
  except Exception as e:
    print(f"❌ 載入失敗: {e}")
    return False

  # 讀取資料
  try:
    with open(input_file, 'r', encoding='utf-8') as f:
      data = json.load(f)
    print(f"📖 讀取 {len(data):,} 筆記錄")
  except Exception as e:
    print(f"❌ 讀取失敗: {e}")
    return False

  # 過濾資料
  filtered_data = []

  for item in data:
    if not isinstance(item,
                      dict) or 'input' not in item or 'output' not in item:
      continue

    input_len = count_tokens(item['input'], tokenizer)
    output_len = count_tokens(item['output'], tokenizer)

    if input_len <= max_input and output_len <= max_output:
      filtered_data.append(item)

  # 儲存結果
  input_path = Path(input_file)
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
  keep_ratio = kept / total * 100 if total > 0 else 0

  print(f"\n🎉 完成！")
  print(f"📊 總計: {total:,} → 保留: {kept:,} ({keep_ratio:.1f}%)")
  print(f"📂 輸出: {output_path.name}")

  return True


def main():
  parser = argparse.ArgumentParser(description="過濾 JSON 訓練資料")
  parser.add_argument('json_file', help='JSON 檔案路徑')
  parser.add_argument('--config', default='../config.json', help='設定檔路徑')

  args = parser.parse_args()

  success = filter_json_by_length(args.json_file, args.config)

  if success:
    print("✅ 處理成功！")
  else:
    print("❌ 處理失敗")


if __name__ == "__main__":
  main()