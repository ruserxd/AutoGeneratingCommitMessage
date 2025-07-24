import json
import os
import sys
from collections import Counter
from datetime import datetime


def analyze_first_words(data_path):
  """分析每筆資料 output (commit message) 的第一個字串分佈"""
  print("🔍 分析 Commit Message 第一個字串分佈...")

  try:
    with open(data_path, 'r', encoding='utf-8') as f:
      data = json.load(f)

    if not isinstance(data, list):
      print("❌ 數據格式錯誤：應該是 list")
      return None, None

    first_words = []
    valid_data_count = 0

    for i, item in enumerate(data):
      if not isinstance(item, dict):
        continue

      if 'output' not in item:
        continue

      output_text = str(item['output']).strip()
      if not output_text:
        continue

      # 分割成字串並取第一個
      words = output_text.split()
      if not words:
        continue

      first_word = words[0]
      first_words.append(first_word)
      valid_data_count += 1

    if not first_words:
      print("❌ 沒有找到有效的數據")
      return None, None

    # 統計字串出現次數
    word_counter = Counter(first_words)
    total_count = len(first_words)

    print(f"📊 總共分析了 {total_count} 筆有效數據")
    print(f"📊 發現 {len(word_counter)} 個不同的首字串")
    print("\n📈 Commit Message 首字串分佈 (按出現次數排序):")

    # 計算比例並顯示
    word_stats = []
    for word, count in word_counter.most_common():
      ratio = count / total_count
      # 截斷過長的字串用於顯示
      word_display = word if len(word) <= 20 else word[:17] + "..."
      print(
        f"  '{word_display}': {count:4d} 次 ({ratio:.3f} = {ratio * 100:.1f}%)")
      word_stats.append((word, count, ratio))

    return word_stats, data

  except Exception as e:
    print(f"❌ 分析失敗: {e}")
    return None, None


def filter_by_first_word_ratio(data_path, threshold=0.003):
  """根據 commit message 第一個字串出現比例過濾數據"""
  print(f"\n🔧 開始過濾 Commit Message (閾值: {threshold})")

  # 分析字串分佈
  word_stats, data = analyze_first_words(data_path)
  if not word_stats or not data:
    return None

  total_count = sum(count for _, count, _ in word_stats)

  # 找出需要保留的字串 (比例 >= threshold)
  keep_words = set()
  remove_words = set()

  print(f"\n📋 過濾結果 (閾值 >= {threshold}):")
  for word, count, ratio in word_stats:
    word_display = word if len(word) <= 20 else word[:17] + "..."
    if ratio >= threshold:
      keep_words.add(word)
      print(f"  ✅ 保留 '{word_display}': {ratio:.3f} ({count} 筆)")
    else:
      remove_words.add(word)
      print(f"  ❌ 移除 '{word_display}': {ratio:.3f} ({count} 筆)")

  # 過濾數據
  filtered_data = []
  removed_count = 0
  removed_examples = []  # 記錄被移除的範例

  for item in data:
    if not isinstance(item, dict) or 'output' not in item:
      continue

    output_text = str(item['output']).strip()
    if not output_text:
      continue

    # 獲取第一個字串
    words = output_text.split()
    if not words:
      continue

    first_word = words[0]

    if first_word in keep_words:
      filtered_data.append(item)
    else:
      removed_count += 1
      # 記錄前幾個被移除的範例
      if len(removed_examples) < 5:
        removed_examples.append({
          'first_word': first_word,
          'output': output_text
        })

  # 生成輸出檔案名
  base_name = os.path.splitext(data_path)[0]
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  output_path = f"{base_name}_filtered_commit_{threshold}.json"

  # 保存過濾後的數據
  try:
    with open(output_path, 'w', encoding='utf-8') as f:
      json.dump(filtered_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 過濾完成!")
    print(f"📊 統計結果:")
    print(f"  原始數據: {len(data)} 筆")
    print(f"  保留數據: {len(filtered_data)} 筆")
    print(f"  移除數據: {removed_count} 筆")
    print(f"  保留比例: {len(filtered_data) / len(data) * 100:.1f}%")
    print(f"📁 輸出檔案: {output_path}")

    # 顯示保留的主要字串類型
    print(f"\n📋 保留的主要 Commit Message 開頭:")
    for word, count, ratio in word_stats:
      if word in keep_words:
        word_display = word if len(word) <= 30 else word[:27] + "..."
        print(f"  🎯 '{word_display}': {count} 筆")

    # 顯示被移除的範例
    if removed_examples:
      print(f"\n🗑️  被移除的範例:")
      for example in removed_examples:
        print(f"  ❌ '{example['first_word']}': {example['output']}")
        if len(removed_examples) >= 5:
          break

    return output_path

  except Exception as e:
    print(f"❌ 保存失敗: {e}")
    return None


def main():
  """主函數 - CLI 模式"""
  print("🚀 Commit Message 第一個字串過濾工具")
  print("=" * 50)

  # 檢查命令行參數
  if len(sys.argv) != 2:
    print("❌ 使用方法:")
    print(f"   python {sys.argv[0]} <數據檔案路徑>")
    print("\n範例:")
    print(f"   python {sys.argv[0]} sample_data/spring-boot-training.json")
    print("\n說明:")
    print("   - 分析每筆 output (commit message) 的第一個字串")
    print("   - 過濾掉出現比例低於 30% 的字串開頭的資料")
    print("   - 例如: 'Remove' 比例 < 30% → 所有 'Remove' 開頭的都會被刪除")
    return

  data_path = sys.argv[1]

  # 檢查檔案是否存在
  if not os.path.exists(data_path):
    print(f"❌ 檔案不存在: {data_path}")
    return

  print(f"📁 輸入檔案: {data_path}")

  # 執行過濾 (固定閾值 0.03)
  output_path = filter_by_first_word_ratio(data_path, 0.007)

  if output_path:
    print(f"\n🎉 過濾完成！")
    print(f"💡 在訓練程式中使用: data_path = \"{output_path}\"")


if __name__ == "__main__":
  main()