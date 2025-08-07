import json
import re
import argparse
import glob
import os
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple
from pathlib import Path


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


def analyze_single_file(file_path: str) -> Dict[str, Any]:
  """
  分析單個檔案，返回統計結果

  Args:
      file_path: JSON 檔案路徑

  Returns:
      包含統計資料的字典
  """
  try:
    with open(file_path, 'r', encoding='utf-8') as f:
      data = json.load(f)

    # 收集第一個字和對應的完整文本範例
    first_words = []
    word_examples = defaultdict(list)

    for i, item in enumerate(data):
      if 'output' in item and item['output']:
        output_text = item['output']
        first_word = extract_first_word(output_text)

        if first_word:
          first_words.append(first_word)

          # 儲存範例（每個字最多保存3個範例）
          if len(word_examples[first_word]) < 3:
            word_examples[first_word].append({
              'index': i + 1,
              'text': output_text
            })

    # 統計頻率
    word_counter = Counter(first_words)

    return {
      'file_path': file_path,
      'total_entries': len(data),
      'valid_entries': len(first_words),
      'word_counter': word_counter,
      'word_examples': dict(word_examples),
      'success': True,
      'error': None
    }

  except Exception as e:
    return {
      'file_path': file_path,
      'success': False,
      'error': str(e),
      'word_counter': Counter(),
      'word_examples': {}
    }


def analyze_multiple_files(file_patterns: List[str], show_examples: bool = True,
    min_count: int = 1, show_per_file: bool = True) -> None:
  """
  分析多個檔案中 output 欄位的第一個字

  Args:
      file_patterns: 檔案路徑或模式列表
      show_examples: 是否顯示範例
      min_count: 最小出現次數過濾
      show_per_file: 是否顯示每個檔案的分析
  """
  # 收集所有檔案
  all_files = []
  for pattern in file_patterns:
    if os.path.isfile(pattern):
      all_files.append(pattern)
    else:
      # 支援萬用字符
      matched_files = glob.glob(pattern)
      all_files.extend(matched_files)

  if not all_files:
    print("❌ 沒有找到符合條件的檔案")
    return

  # 去重並排序
  all_files = sorted(list(set(all_files)))

  print(f"🔍 找到 {len(all_files)} 個檔案要分析")
  print("=" * 80)

  # 分析每個檔案
  file_results = []
  combined_counter = Counter()
  combined_examples = defaultdict(list)

  for file_path in all_files:
    print(f"📂 正在分析: {file_path}")
    result = analyze_single_file(file_path)
    file_results.append(result)

    if result['success']:
      combined_counter.update(result['word_counter'])

      # 合併範例
      for word, examples in result['word_examples'].items():
        for example in examples:
          if len(combined_examples[word]) < 5:  # 每個字最多保存5個範例
            example['file'] = os.path.basename(file_path)
            combined_examples[word].append(example)

      print(
        f"  ✅ 成功: {result['valid_entries']}/{result['total_entries']} 筆資料")
    else:
      print(f"  ❌ 失敗: {result['error']}")

  print("\n" + "=" * 80)

  # 顯示個別檔案統計
  if show_per_file:
    print("📊 個別檔案統計:")
    print("-" * 80)

    for result in file_results:
      if result['success']:
        file_name = os.path.basename(result['file_path'])
        word_count = len(result['word_counter'])
        top_word = result['word_counter'].most_common(1)
        top_word_info = f"{top_word[0][0]} ({top_word[0][1]}次)" if top_word else "無"

        print(f"📄 {file_name:<30} | "
              f"資料: {result['valid_entries']:>5} | "
              f"不同字: {word_count:>3} | "
              f"最常見: {top_word_info}")

    print("\n" + "=" * 80)

  # 顯示合併統計
  total_valid = sum(r['valid_entries'] for r in file_results if r['success'])
  total_entries = sum(r['total_entries'] for r in file_results if r['success'])

  print("🌐 合併統計結果:")
  print(
    f"📁 分析檔案數: {len([r for r in file_results if r['success']])}/{len(file_results)}")
  print(f"📊 總資料筆數: {total_entries}")
  print(f"📈 有效資料數: {total_valid}")
  print(f"🔤 不同第一字: {len(combined_counter)}")

  # 過濾最小出現次數
  filtered_words = {word: count for word, count in combined_counter.items()
                    if count >= min_count}

  if not filtered_words:
    print(f"❌ 沒有符合最小出現次數 ({min_count}) 的字")
    return

  print(f"🔍 符合條件的字: {len(filtered_words)} 個 (出現次數 >= {min_count})")
  print()

  # 按頻率排序顯示
  sorted_words = sorted(filtered_words.items(), key=lambda x: (-x[1], x[0]))

  print("📋 第一個字統計 (合併所有檔案，按頻率排序):")
  print("-" * 80)
  print(f"{'第一個字':<15} {'次數':<8} {'百分比':<8} {'檔案數':<8} {'範例'}")
  print("-" * 80)

  total_count = sum(filtered_words.values())

  for word, count in sorted_words[:50]:  # 顯示前50個
    percentage = (count / total_count) * 100

    # 計算出現在幾個檔案中
    files_with_word = set()
    for result in file_results:
      if result['success'] and word in result['word_counter']:
        files_with_word.add(result['file_path'])
    file_count = len(files_with_word)

    # 顯示第一個範例
    example = ""
    if word in combined_examples and combined_examples[word]:
      example_text = combined_examples[word][0]['text']
      example = example_text[:35] + "..." if len(
        example_text) > 35 else example_text
      example = example.replace('\n', ' ')

    print(
      f"{word:<15} {count:<8} {percentage:<7.1f}% {file_count:<8} {example}")

  if len(sorted_words) > 50:
    print(f"\n... 還有 {len(sorted_words) - 50} 個第一個字")

  # 顯示詳細範例
  if show_examples:
    print("\n" + "=" * 80)
    print("📝 詳細範例 (前10個最常見的第一個字):")
    print("=" * 80)

    for word, count in sorted_words[:10]:
      print(f"\n🔤 '{word}' (出現 {count} 次):")

      if word in combined_examples:
        for j, example in enumerate(combined_examples[word], 1):
          file_name = example.get('file', 'unknown')
          print(f"  範例 {j} ({file_name}): {example['text']}")
      print("-" * 60)


def export_multiple_results(file_patterns: List[str],
    output_file: str = None) -> None:
  """
  將多檔案第一個字統計結果匯出到 JSON 檔案

  Args:
      file_patterns: 檔案路徑或模式列表
      output_file: 輸出檔案路徑
  """
  try:
    # 收集所有檔案
    all_files = []
    for pattern in file_patterns:
      if os.path.isfile(pattern):
        all_files.append(pattern)
      else:
        matched_files = glob.glob(pattern)
        all_files.extend(matched_files)

    all_files = sorted(list(set(all_files)))

    # 分析每個檔案
    file_results = []
    combined_counter = Counter()
    combined_examples = defaultdict(list)

    for file_path in all_files:
      result = analyze_single_file(file_path)
      file_results.append(result)

      if result['success']:
        combined_counter.update(result['word_counter'])

        for word, examples in result['word_examples'].items():
          for example in examples:
            if len(combined_examples[word]) < 5:
              example['file'] = os.path.basename(file_path)
              combined_examples[word].append(example)

    # 格式化結果
    results = {
      'analysis_summary': {
        'total_files_analyzed': len([r for r in file_results if r['success']]),
        'total_files_attempted': len(file_results),
        'total_entries': sum(
            r['total_entries'] for r in file_results if r['success']),
        'total_valid_entries': sum(
            r['valid_entries'] for r in file_results if r['success']),
        'unique_first_words': len(combined_counter),
        'most_common': combined_counter.most_common(1)[
          0] if combined_counter else None
      },
      'file_details': [],
      'combined_word_statistics': []
    }

    # 個別檔案詳情
    for result in file_results:
      file_detail = {
        'file_path': result['file_path'],
        'file_name': os.path.basename(result['file_path']),
        'success': result['success'],
        'total_entries': result.get('total_entries', 0),
        'valid_entries': result.get('valid_entries', 0),
        'unique_words': len(result['word_counter']),
      }

      if result['success']:
        top_words = result['word_counter'].most_common(5)
        file_detail['top_words'] = [{'word': w, 'count': c} for w, c in
                                    top_words]
      else:
        file_detail['error'] = result.get('error', 'Unknown error')

      results['file_details'].append(file_detail)

    # 合併統計
    total_valid = sum(r['valid_entries'] for r in file_results if r['success'])
    for word, count in combined_counter.most_common():
      # 計算出現在幾個檔案中
      files_with_word = []
      for result in file_results:
        if result['success'] and word in result['word_counter']:
          files_with_word.append({
            'file': os.path.basename(result['file_path']),
            'count': result['word_counter'][word]
          })

      word_stat = {
        'word': word,
        'total_count': count,
        'percentage': round((count / total_valid) * 100,
                            2) if total_valid > 0 else 0,
        'appears_in_files': len(files_with_word),
        'file_distribution': files_with_word,
        'examples': combined_examples[word][:3]  # 最多3個範例
      }
      results['combined_word_statistics'].append(word_stat)

    # 儲存結果
    if output_file is None:
      output_file = 'multi_file_first_words_analysis.json'

    with open(output_file, 'w', encoding='utf-8') as f:
      json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ 多檔案分析結果已匯出至: {output_file}")

  except Exception as e:
    print(f"❌ 匯出失敗: {str(e)}")


def main():
  """主函數"""
  parser = argparse.ArgumentParser(
      description='統計多個 JSON 資料檔案中 output 欄位的第一個字',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog="""
範例用法:
  python script.py file1.json file2.json                    # 分析指定檔案
  python script.py "data/*.json"                           # 使用萬用字符
  python script.py file*.json --min-count 5                # 設定最小出現次數
  python script.py "*.json" --export results.json          # 匯出結果
  python script.py data1.json data2.json --no-per-file     # 不顯示個別檔案統計
        """)

  parser.add_argument('input_files', nargs='+',
                      help='輸入的 JSON 檔案路徑（支援萬用字符）')
  parser.add_argument('--no-examples', action='store_true',
                      help='不顯示詳細範例')
  parser.add_argument('--no-per-file', action='store_true',
                      help='不顯示個別檔案統計')
  parser.add_argument('--min-count', type=int, default=1,
                      help='最小出現次數過濾 (預設: 1)')
  parser.add_argument('--export', help='匯出詳細結果到指定檔案')

  args = parser.parse_args()

  # 執行分析
  analyze_multiple_files(
      args.input_files,
      show_examples=not args.no_examples,
      min_count=args.min_count,
      show_per_file=not args.no_per_file
  )

  # 匯出結果（如果指定）
  if args.export:
    export_multiple_results(args.input_files, args.export)


if __name__ == "__main__":
  main()