import json
import random
from collections import Counter


def quick_data_analysis(json_file):
  """快速分析訓練數據質量"""

  with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

  print(f"📊 數據概覽: {len(data)} 筆")

  # 抽樣檢查
  samples = random.sample(data, min(20, len(data)))

  print("\n🔍 隨機樣本檢查:")
  for i, item in enumerate(samples[:10], 1):
    if 'output' in item:
      output = item['output']
      print(f"  {i}. '{output}' (長度: {len(output)})")

  # 統計分析
  outputs = [item.get('output', '') for item in data]

  # 長度分析
  lengths = [len(output) for output in outputs if output]
  avg_length = sum(lengths) / len(lengths) if lengths else 0

  print(f"\n📏 長度統計:")
  print(f"  平均長度: {avg_length:.1f}")
  print(f"  最短: {min(lengths) if lengths else 0}")
  print(f"  最長: {max(lengths) if lengths else 0}")

  # 常見開頭詞
  first_words = []
  for output in outputs:
    if output:
      first_word = output.split()[0].lower() if output.split() else ''
      first_words.append(first_word)

  print(f"\n🔤 最常見的開頭詞:")
  word_counts = Counter(first_words)
  for word, count in word_counts.most_common(10):
    percentage = count / len(first_words) * 100
    print(f"  {word}: {count} ({percentage:.1f}%)")

  # 質量問題檢測
  quality_issues = {
    'too_short': sum(1 for l in lengths if l < 10),
    'too_long': sum(1 for l in lengths if l > 70),
    'has_period': sum(1 for o in outputs if o.endswith('.') or o.endswith('。')),
    'too_generic': sum(1 for o in outputs if any(
        word in o.lower() for word in ['some', 'basic', 'stuff', 'misc']))
  }

  print(f"\n⚠️ 質量問題:")
  total = len(outputs)
  for issue, count in quality_issues.items():
    percentage = count / total * 100
    print(f"  {issue}: {count}/{total} ({percentage:.1f}%)")

  return {
    'total': len(data),
    'avg_length': avg_length,
    'quality_issues': quality_issues,
    'first_words': dict(word_counts.most_common(20))
  }


if __name__ == "__main__":
  import sys

  if len(sys.argv) > 1:
    result = quick_data_analysis(sys.argv[1])

    # 給出建議
    print(f"\n💡 建議:")
    if result['quality_issues']['too_generic'] > result['total'] * 0.3:
      print("  - 訓練數據中有太多籠統描述，建議清理")
    if result['avg_length'] < 20:
      print("  - 平均長度過短，可能缺少詳細描述")
    if 'add' in result['first_words'] and result['first_words']['add'] > result[
      'total'] * 0.5:
      print("  - 'add'開頭過多，缺少多樣性")
  else:
    print("使用方法: python quick_check.py your_data.json")