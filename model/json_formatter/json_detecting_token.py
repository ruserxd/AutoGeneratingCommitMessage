import json
import sys
import numpy as np
from pathlib import Path
from transformers import RobertaTokenizer


def analyze_length_distribution(json_file):
  """分析長度分佈並提供建議"""

  # 載入 tokenizer
  print("🔄 載入 tokenizer...")
  try:
    tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
  except Exception as e:
    print(f"❌ 無法載入 tokenizer: {e}")
    return None

  # 讀取資料
  print(f"📖 讀取檔案: {json_file}")
  with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

  if not isinstance(data, list):
    data = [data]

  # 計算長度
  input_lengths = []
  output_lengths = []

  print(f"📊 分析 {len(data):,} 筆記錄...")

  for item in data:
    if not isinstance(item,
                      dict) or 'input' not in item or 'output' not in item:
      continue

    input_len = len(tokenizer.encode(item['input'], add_special_tokens=True,
                                     truncation=False))
    output_len = len(tokenizer.encode(item['output'], add_special_tokens=True,
                                      truncation=False))

    input_lengths.append(input_len)
    output_lengths.append(output_len)

  # 計算統計
  def get_stats(lengths):
    return {
      'min': int(np.min(lengths)),
      'max': int(np.max(lengths)),
      'mean': int(np.mean(lengths)),
      'median': int(np.median(lengths)),
      'p90': int(np.percentile(lengths, 90)),
      'p95': int(np.percentile(lengths, 95))
    }

  input_stats = get_stats(input_lengths)
  output_stats = get_stats(output_lengths)

  # 顯示統計
  print(f"\n{'=' * 40}")
  print("📊 長度統計")
  print(f"{'=' * 40}")
  print(f"{'指標':<8} {'INPUT':<8} {'OUTPUT':<8}")
  print(f"{'-' * 24}")
  print(f"{'總數':<8} {len(input_lengths):<8} {len(output_lengths):<8}")
  print(f"{'最小':<8} {input_stats['min']:<8} {output_stats['min']:<8}")
  print(f"{'平均':<8} {input_stats['mean']:<8} {output_stats['mean']:<8}")
  print(f"{'中位數':<8} {input_stats['median']:<8} {output_stats['median']:<8}")
  print(f"{'90%':<8} {input_stats['p90']:<8} {output_stats['p90']:<8}")
  print(f"{'95%':<8} {input_stats['p95']:<8} {output_stats['p95']:<8}")
  print(f"{'最大':<8} {input_stats['max']:<8} {output_stats['max']:<8}")

  # 推薦設定
  print(f"\n💡 推薦設定:")

  # 計算不同設定的保留率
  settings = [
    ("快速", 1200, 32),
    ("平衡", 1600, 64),
    ("完整", 2400, 96)
  ]

  for name, input_limit, output_limit in settings:
    kept = sum(1 for i, o in zip(input_lengths, output_lengths)
               if i <= input_limit and o <= output_limit)
    ratio = kept / len(input_lengths) * 100

    print(
      f"  {name}: --max-input {input_limit} --max-output {output_limit} (保留 {ratio:.1f}%)")

  return input_stats, output_stats


def main():
  if len(sys.argv) != 2:
    print("使用方法: python analyze.py <json_file>")
    sys.exit(1)

  json_file = sys.argv[1]

  if not Path(json_file).exists():
    print(f"❌ 檔案不存在: {json_file}")
    sys.exit(1)

  result = analyze_length_distribution(json_file)

  if result:
    print(f"\n✅ 分析完成！")
  else:
    print(f"\n❌ 分析失敗！")
    sys.exit(1)


if __name__ == "__main__":
  main()