import json
import sys
import numpy as np
from pathlib import Path
from transformers import RobertaTokenizer


def analyze_length_distribution(json_file, input_field='input',
    output_field='output'):
  """分析長度分佈並提供實用建議"""

  # 載入 tokenizer
  print("載入 tokenizer...")
  try:
    tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
  except Exception as e:
    print(f"錯誤: 無法載入 tokenizer: {e}")
    return None

  # 讀取資料
  print(f"讀取檔案: {json_file}")
  with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

  if not isinstance(data, list):
    data = [data]

  # 計算長度
  input_lengths = []
  output_lengths = []

  print(f"分析 {len(data)} 筆記錄...")

  for i, item in enumerate(data):
    if not isinstance(item,
                      dict) or input_field not in item or output_field not in item:
      continue

    input_text = item[input_field]
    output_text = item[output_field]

    # 使用與訓練相同的 tokenization 方式
    input_len = len(tokenizer.encode(input_text, add_special_tokens=True,
                                     max_length=10000, truncation=False))
    output_len = len(tokenizer.encode(output_text, add_special_tokens=True,
                                      max_length=10000, truncation=False))

    input_lengths.append(input_len)
    output_lengths.append(output_len)

    # 簡化進度顯示
    if (i + 1) % 2000 == 0:
      print(f"  已處理 {i + 1} 筆...")

  # 核心統計
  input_stats = {
    'count': len(input_lengths),
    'min': int(np.min(input_lengths)),
    'max': int(np.max(input_lengths)),
    'mean': int(np.mean(input_lengths)),
    'median': int(np.median(input_lengths)),
    'p75': int(np.percentile(input_lengths, 75)),
    'p90': int(np.percentile(input_lengths, 90)),
    'p95': int(np.percentile(input_lengths, 95))
  }

  output_stats = {
    'count': len(output_lengths),
    'min': int(np.min(output_lengths)),
    'max': int(np.max(output_lengths)),
    'mean': int(np.mean(output_lengths)),
    'median': int(np.median(output_lengths)),
    'p75': int(np.percentile(output_lengths, 75)),
    'p90': int(np.percentile(output_lengths, 90)),
    'p95': int(np.percentile(output_lengths, 95))
  }

  # 顯示核心統計
  print(f"\n{'=' * 60}")
  print("📊 長度分佈統計")
  print(f"{'=' * 60}")
  print(f"{'指標':<12} {'INPUT':<8} {'OUTPUT':<8}")
  print(f"{'-' * 28}")
  print(f"{'記錄數':<12} {input_stats['count']:<8} {output_stats['count']:<8}")
  print(f"{'最小值':<12} {input_stats['min']:<8} {output_stats['min']:<8}")
  print(
    f"{'中位數':<12} {input_stats['median']:<8} {output_stats['median']:<8}")
  print(f"{'平均值':<12} {input_stats['mean']:<8} {output_stats['mean']:<8}")
  print(f"{'75%':<12} {input_stats['p75']:<8} {output_stats['p75']:<8}")
  print(f"{'90%':<12} {input_stats['p90']:<8} {output_stats['p90']:<8}")
  print(f"{'95%':<12} {input_stats['p95']:<8} {output_stats['p95']:<8}")
  print(f"{'最大值':<12} {input_stats['max']:<8} {output_stats['max']:<8}")

  # 實用建議 (基於Git diff的實際特性)
  print(f"\n{'=' * 60}")
  print("💡 推薦設定")
  print(f"{'=' * 60}")

  # 針對不同使用場景的建議
  scenarios = [
    {
      'name': '🎯 推薦設定 (最佳平衡)',
      'input_limit': 1600,  # 略低於75%百分位，平衡效果和效率
      'output_limit': 80,  # 略高於90%百分位，涵蓋大部分commit
      'description': '平衡資料保留和訓練效率'
    },
    {
      'name': '⚡ 高效設定 (快速訓練)',
      'input_limit': 1200,  # 接近中位數，訓練快速
      'output_limit': 50,  # 接近75%百分位
      'description': '犧牲部分資料換取訓練速度'
    },
    {
      'name': '🔧 完整設定 (最大覆蓋)',
      'input_limit': 2400,  # 接近90%百分位
      'output_limit': 120,  # 接近95%百分位
      'description': '保留最多資料，需要更多資源'
    }
  ]

  for scenario in scenarios:
    input_limit = scenario['input_limit']
    output_limit = scenario['output_limit']

    # 計算實際保留比例
    kept_both = sum(1 for i, o in zip(input_lengths, output_lengths)
                    if i <= input_limit and o <= output_limit)
    keep_ratio = kept_both / len(input_lengths) * 100

    print(f"\n{scenario['name']}:")
    print(f"  {scenario['description']}")
    print(f"  --max-input {input_limit} --max-output {output_limit}")
    print(
      f"  保留資料: {keep_ratio:.1f}% ({kept_both:,}/{len(input_lengths):,})")

  # 長度分佈概覽
  print(f"\n{'=' * 60}")
  print("📈 長度分佈概覽")
  print(f"{'=' * 60}")

  ranges = [
    (0, 500, "短diff"),
    (501, 1000, "中等diff"),
    (1001, 2000, "長diff"),
    (2001, float('inf'), "超長diff")
  ]

  print(f"{'範圍':<12} {'INPUT筆數':<10} {'比例':<8}")
  print(f"{'-' * 30}")

  for min_len, max_len, label in ranges:
    count = sum(1 for x in input_lengths if min_len <= x <= max_len)
    pct = count / len(input_lengths) * 100
    print(f"{label:<12} {count:<10,} {pct:>6.1f}%")

  return input_stats, output_stats


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("使用方法: python analyze_length.py <json_file>")
    print("範例: python analyze_length.py data.json")
    sys.exit(1)

  json_file = sys.argv[1]

  if not Path(json_file).exists():
    print(f"錯誤: 找不到檔案 {json_file}")
    sys.exit(1)

  result = analyze_length_distribution(json_file)

  if result:
    print(f"\n✅ 分析完成！")
    print(f"💡 建議先用推薦設定過濾資料，再根據訓練效果調整")
  else:
    print(f"\n❌ 分析失敗！")
    sys.exit(1)