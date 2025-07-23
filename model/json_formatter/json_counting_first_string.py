import json
import re
import argparse
from collections import Counter
from typing import Dict, List, Any, Tuple


def extract_first_word(text: str) -> str:
  """
  提取文本的第一個單詞

  Args:
      text: 輸入文本

  Returns:
      第一個單詞（轉為小寫）
  """
  if not text:
    return ""

  # 移除開頭的空白字符
  text = text.strip()

  # 使用正則表達式提取第一個單詞
  # 支援英文單詞、中文字符、數字等
  match = re.match(r'[\w\u4e00-\u9fff]+', text)

  if match:
    return match.group().lower()
  else:
    # 如果沒有匹配到，返回第一個非空白字符
    for char in text:
      if not char.isspace():
        return char.lower()
    return ""


def analyze_first_words(file_path: str, show_examples: bool = True,
    min_count: int = 1) -> None:
  """
  分析 JSON 檔案中 output 欄位的第一個字

  Args:
      file_path: JSON 檔案路徑
      show_examples: 是否顯示範例
      min_count: 最小出現次數過濾
  """
  try:
    # 讀取 JSON 檔案
    with open(file_path, 'r', encoding='utf-8') as f:
      data = json.load(f)

    print(f"📂 分析檔案: {file_path}")
    print(f"📊 總資料筆數: {len(data)}")
    print("=" * 60)

    # 收集第一個字和對應的完整文本範例
    first_words = []
    word_examples = {}

    for i, item in enumerate(data):
      if 'output' in item and item['output']:
        output_text = item['output']
        first_word = extract_first_word(output_text)

        if first_word:
          first_words.append(first_word)

          # 儲存範例（每個字最多保存3個範例）
          if first_word not in word_examples:
            word_examples[first_word] = []

          if len(word_examples[first_word]) < 3:
            word_examples[first_word].append({
              'index': i + 1,
              'text': output_text
            })

    # 統計頻率
    word_counter = Counter(first_words)

    # 過濾最小出現次數
    filtered_words = {word: count for word, count in word_counter.items() if
                      count >= min_count}

    print(
      f"🔤 找到 {len(filtered_words)} 個不同的第一個字 (出現次數 >= {min_count})")
    print(f"📈 總計 {sum(filtered_words.values())} 筆有效資料")
    print()

    # 按頻率排序顯示
    sorted_words = sorted(filtered_words.items(), key=lambda x: (-x[1], x[0]))

    print("📋 第一個字統計 (按頻率排序):")
    print("-" * 60)
    print(f"{'第一個字':<15} {'次數':<8} {'百分比':<8} {'範例'}")
    print("-" * 60)

    total_count = sum(filtered_words.values())

    for word, count in sorted_words[:50]:  # 顯示前50個
      percentage = (count / total_count) * 100

      # 顯示第一個範例
      example = ""
      if word in word_examples and word_examples[word]:
        example_text = word_examples[word][0]['text']
        example = example_text[:40] + "..." if len(
          example_text) > 40 else example_text
        example = example.replace('\n', ' ')

      print(f"{word:<15} {count:<8} {percentage:<7.1f}% {example}")

    if len(sorted_words) > 50:
      print(f"\n... 還有 {len(sorted_words) - 50} 個第一個字")

    # 顯示詳細範例
    if show_examples:
      print("\n" + "=" * 60)
      print("📝 詳細範例 (前10個最常見的第一個字):")
      print("=" * 60)

      for word, count in sorted_words[:10]:
        print(f"\n🔤 '{word}' (出現 {count} 次):")

        if word in word_examples:
          for j, example in enumerate(word_examples[word], 1):
            print(f"  範例 {j}: {example['text']}")
        print("-" * 50)

    # 統計摘要
    print("\n" + "=" * 60)
    print("📊 統計摘要:")
    print(
      f"• 最常見的第一個字: '{sorted_words[0][0]}' ({sorted_words[0][1]} 次)")
    print(f"• 總共 {len(word_counter)} 個不同的第一個字")
    print(
      f"• 平均每個字出現 {sum(word_counter.values()) / len(word_counter):.1f} 次")

    # 顯示出現次數為1的字（可能是拼寫錯誤或特殊情況）
    singleton_words = [word for word, count in word_counter.items() if
                       count == 1]
    if singleton_words:
      print(f"• 只出現1次的字: {len(singleton_words)} 個")
      if len(singleton_words) <= 20:
        print(f"  → {', '.join(sorted(singleton_words))}")

  except FileNotFoundError:
    print(f"❌ 找不到檔案: {file_path}")
  except json.JSONDecodeError:
    print(f"❌ 檔案不是有效的 JSON: {file_path}")
  except Exception as e:
    print(f"❌ 發生錯誤: {str(e)}")


def export_results(file_path: str, output_file: str = None) -> None:
  """
  將第一個字統計結果匯出到 JSON 檔案

  Args:
      file_path: 輸入 JSON 檔案路徑
      output_file: 輸出檔案路徑
  """
  try:
    with open(file_path, 'r', encoding='utf-8') as f:
      data = json.load(f)

    # 收集資料
    first_words = []
    word_examples = {}

    for i, item in enumerate(data):
      if 'output' in item and item['output']:
        output_text = item['output']
        first_word = extract_first_word(output_text)

        if first_word:
          first_words.append(first_word)

          if first_word not in word_examples:
            word_examples[first_word] = []

          word_examples[first_word].append({
            'index': i + 1,
            'text': output_text
          })

    # 統計並格式化結果
    word_counter = Counter(first_words)

    results = {
      'summary': {
        'total_entries': len(data),
        'valid_entries': len(first_words),
        'unique_first_words': len(word_counter),
        'most_common': word_counter.most_common(1)[0] if word_counter else None
      },
      'word_statistics': []
    }

    for word, count in word_counter.most_common():
      word_stat = {
        'word': word,
        'count': count,
        'percentage': round((count / len(first_words)) * 100, 2),
        'examples': word_examples[word][:3]  # 最多3個範例
      }
      results['word_statistics'].append(word_stat)

    # 儲存結果
    if output_file is None:
      output_file = file_path.replace('.json', '_first_words_analysis.json')

    with open(output_file, 'w', encoding='utf-8') as f:
      json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ 分析結果已匯出至: {output_file}")

  except Exception as e:
    print(f"❌ 匯出失敗: {str(e)}")


def main():
  """主函數"""
  parser = argparse.ArgumentParser(
    description='統計 JSON 資料中 output 欄位的第一個字')
  parser.add_argument('input_file', help='輸入的 JSON 檔案路徑')
  parser.add_argument('--no-examples', action='store_true',
                      help='不顯示詳細範例')
  parser.add_argument('--min-count', type=int, default=1,
                      help='最小出現次數過濾 (預設: 1)')
  parser.add_argument('--export', help='匯出詳細結果到指定檔案')

  args = parser.parse_args()

  # 執行分析
  analyze_first_words(
      args.input_file,
      show_examples=not args.no_examples,
      min_count=args.min_count
  )

  # 匯出結果（如果指定）
  if args.export:
    export_results(args.input_file, args.export)


def quick_analysis(file_path: str) -> Dict[str, int]:
  """
  快速分析，返回第一個字的統計字典

  Args:
      file_path: JSON 檔案路徑

  Returns:
      {第一個字: 出現次數} 的字典
  """
  try:
    with open(file_path, 'r', encoding='utf-8') as f:
      data = json.load(f)

    first_words = []
    for item in data:
      if 'output' in item and item['output']:
        first_word = extract_first_word(item['output'])
        if first_word:
          first_words.append(first_word)

    return dict(Counter(first_words))

  except Exception as e:
    print(f"快速分析失敗: {str(e)}")
    return {}


if __name__ == "__main__":
  main()