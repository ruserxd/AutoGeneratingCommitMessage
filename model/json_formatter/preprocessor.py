import json
import os
import sys
import re
from collections import Counter
from datetime import datetime
from typing import List, Dict, Tuple


class CommitDataPreprocessor:
  def __init__(self):
    self.stats = {
      'total_samples': 0,
      'valid_samples': 0,
      'removed_empty': 0,
      'removed_too_long': 0,
      'removed_invalid_diff': 0,
      'removed_invalid_message': 0,
      'removed_duplicates': 0,
      'removed_low_frequency': 0
    }

  def clean_diff_content(self, diff_text: str) -> str:
    """清理 diff 內容"""
    if not diff_text:
      return ""

    lines = diff_text.split('\n')
    cleaned_lines = []

    for line in lines:
      # 移除過長的行（可能是二進制檔案或壓縮檔案）
      if len(line) > 1000:
        continue

      # 保留重要的 diff 標記
      if any(line.startswith(marker) for marker in
             ['diff --git', '@@', '---', '+++', '+', '-', ' ']):
        cleaned_lines.append(line)
      # 保留 index 行
      elif line.startswith('index '):
        cleaned_lines.append(line)
      # 移除其他元數據
      else:
        continue

    return '\n'.join(cleaned_lines)

  def is_valid_diff(self, diff_text: str) -> bool:
    """檢查是否為有效的 diff"""
    if not diff_text or len(diff_text.strip()) < 10:
      return False

    # 必須包含 diff 標記
    required_markers = ['diff --git', '@@']
    has_required = any(marker in diff_text for marker in required_markers)

    # 必須有實際的程式碼變更
    change_lines = [
      line for line in diff_text.split('\n')
      if line.strip() and line.startswith(('+', '-')) and not line.startswith(
          ('+++', '---'))
    ]

    if not change_lines:
      return False

    # 過濾掉只有微小變更的 diff（如空行、註釋調整）
    meaningful_changes = []
    for line in change_lines:
      content = line[1:].strip()  # 移除 +/- 符號

      # 跳過空行或只有符號的行
      if not content or content in ['*', '//', '/*', '*/', '{', '}']:
        continue

      # 跳過只有空白字符調整的行
      if len(content.replace(' ', '').replace('\t', '')) == 0:
        continue

      meaningful_changes.append(line)

    # 至少要有 2 行有意義的變更
    return len(meaningful_changes) >= 2

  def clean_commit_message(self, message: str) -> str:
    """清理 commit message"""
    if not message:
      return ""

    # 基本清理
    message = message.strip()

    # 移除多餘的空行
    message = re.sub(r'\n\s*\n', '\n', message)

    # 移除特殊字符
    message = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', message)

    # 只保留第一行（通常是主要的 commit message）
    first_line = message.split('\n')[0].strip()

    return first_line

  def is_valid_commit_message(self, message: str) -> bool:
    """檢查是否為有效的 commit message"""
    if not message or len(message.strip()) < 3:
      return False

    # 長度檢查
    if len(message) > 200:
      return False

    # 檢查是否只有一個字串（新增的條件）
    words = message.strip().split()
    if len(words) <= 1:
      return False

    # 過濾常見的無意義詞彙
    meaningless_words = {
      'polish', 'cleanup', 'fix', 'update', 'change', 'modify',
      'refactor', 'improve', 'enhancement', 'tweaks', 'adjustments'
    }

    # 如果只有 2 個詞且第一個詞是無意義的，則過濾掉
    if len(words) == 2 and words[0].lower() in meaningless_words:
      return False

    # 不應該包含 diff 相關內容
    invalid_patterns = [
      r'diff --git',
      r'@@.*@@',
      r'^\+\+\+',
      r'^---',
      r'^index [a-f0-9]+',
    ]

    for pattern in invalid_patterns:
      if re.search(pattern, message, re.MULTILINE):
        return False

    # 應該包含英文字母
    if not re.search(r'[a-zA-Z]', message):
      return False

    return True

  def filter_by_commit_frequency(self, data: List[Dict],
      min_frequency: float = 0.01) -> List[Dict]:
    """根據 commit message 第一個詞的頻率過濾"""
    print(f"\n🔍 分析 commit message 第一個詞的頻率...")

    # 統計第一個詞的頻率
    first_words = []
    for item in data:
      message = item.get('output', '').strip()
      if message:
        words = message.split()
        if words:
          first_words.append(words[0].lower())

    word_counter = Counter(first_words)
    total_count = len(first_words)

    # 顯示統計
    print(f"📊 發現 {len(word_counter)} 個不同的開頭詞")
    print("🔝 前10個最常見的開頭詞:")
    for word, count in word_counter.most_common(10):
      ratio = count / total_count
      print(f"  '{word}': {count} 次 ({ratio:.3f} = {ratio * 100:.1f}%)")

    # 找出高頻詞
    keep_words = set()
    remove_words = set()

    for word, count in word_counter.items():
      ratio = count / total_count
      if ratio >= min_frequency:
        keep_words.add(word)
      else:
        remove_words.add(word)

    print(f"\n📋 過濾結果 (閾值 >= {min_frequency}):")
    print(f"  ✅ 保留 {len(keep_words)} 個高頻開頭詞")
    print(f"  ❌ 移除 {len(remove_words)} 個低頻開頭詞")

    # 過濾數據
    filtered_data = []
    removed_count = 0

    for item in data:
      message = item.get('output', '').strip()
      if message:
        words = message.split()
        if words and words[0].lower() in keep_words:
          filtered_data.append(item)
        else:
          removed_count += 1
      else:
        removed_count += 1

    self.stats['removed_low_frequency'] = removed_count
    print(
        f"📊 頻率過濾結果: 保留 {len(filtered_data)} 筆，移除 {removed_count} 筆")

    return filtered_data

  def remove_duplicates(self, data: List[Dict]) -> List[Dict]:
    """移除重複的資料"""
    print("\n🔍 移除重複資料...")

    seen_pairs = set()
    unique_data = []
    duplicate_count = 0

    for item in data:
      # 使用 input 和 output 的組合作為唯一標識
      input_text = item.get('input', '').strip()
      output_text = item.get('output', '').strip()

      # 創建簡化的指紋
      input_fingerprint = input_text[:100] if len(
          input_text) > 100 else input_text
      output_fingerprint = output_text

      pair_key = (input_fingerprint, output_fingerprint)

      if pair_key not in seen_pairs:
        seen_pairs.add(pair_key)
        unique_data.append(item)
      else:
        duplicate_count += 1

    self.stats['removed_duplicates'] = duplicate_count
    print(
        f"📊 重複檢查結果: 保留 {len(unique_data)} 筆，移除 {duplicate_count} 筆重複")

    return unique_data

  def preprocess_data(self, data_path: str, output_path: str = None,
      max_input_length: int = 2000, max_output_length: int = 100,
      min_frequency: float = 0.01) -> str:
    """完整的資料預處理流程"""

    print("🚀 開始 Commit Message 資料預處理")
    print("=" * 60)

    # 載入資料
    print(f"📁 載入資料: {data_path}")
    with open(data_path, 'r', encoding='utf-8') as f:
      data = json.load(f)

    self.stats['total_samples'] = len(data)
    print(f"📊 原始資料: {len(data)} 筆")

    # 步驟1: 基本清理和驗證
    print(f"\n🧹 步驟1: 基本清理和驗證")
    cleaned_data = []

    for i, item in enumerate(data):
      if not isinstance(item, dict):
        continue

      if 'input' not in item or 'output' not in item:
        continue

      # 清理 diff
      clean_input = self.clean_diff_content(str(item['input']))
      clean_output = self.clean_commit_message(str(item['output']))

      # 基本驗證
      if not clean_input or not clean_output:
        self.stats['removed_empty'] += 1
        continue

      # 長度檢查
      if len(clean_input) > max_input_length or len(
          clean_output) > max_output_length:
        self.stats['removed_too_long'] += 1
        continue

      # 格式驗證
      if not self.is_valid_diff(clean_input):
        self.stats['removed_invalid_diff'] += 1
        continue

      if not self.is_valid_commit_message(clean_output):
        self.stats['removed_invalid_message'] += 1
        continue

      cleaned_data.append({
        'input': clean_input,
        'output': clean_output
      })

    print(f"📊 基本清理結果: {len(cleaned_data)} 筆有效資料")

    # 步驟2: 移除重複
    print(f"\n🔍 步驟2: 移除重複資料")
    unique_data = self.remove_duplicates(cleaned_data)

    # 步驟3: 頻率過濾
    print(f"\n📊 步驟3: 根據 commit message 開頭詞頻率過濾")
    filtered_data = self.filter_by_commit_frequency(unique_data, min_frequency)

    self.stats['valid_samples'] = len(filtered_data)

    # 生成輸出檔案名
    if output_path is None:
      base_name = os.path.splitext(data_path)[0]
      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      output_path = f"{base_name}_preprocessed_{timestamp}.json"

    # 儲存結果
    with open(output_path, 'w', encoding='utf-8') as f:
      json.dump(filtered_data, f, ensure_ascii=False, indent=2)

    # 顯示統計報告
    self.print_report()
    print(f"\n💾 預處理完成！")
    print(f"📁 輸出檔案: {output_path}")
    print(f"📊 最終資料量: {len(filtered_data)} 筆")

    return output_path

  def print_report(self):
    """列印預處理報告"""
    print(f"\n📋 預處理統計報告")
    print("=" * 40)
    print(f"📊 原始資料:     {self.stats['total_samples']:>6} 筆")
    print(f"❌ 移除空值:     {self.stats['removed_empty']:>6} 筆")
    print(f"❌ 移除過長:     {self.stats['removed_too_long']:>6} 筆")
    print(f"❌ 無效 diff:    {self.stats['removed_invalid_diff']:>6} 筆")
    print(f"❌ 無效 message: {self.stats['removed_invalid_message']:>6} 筆")
    print(f"❌ 移除重複:     {self.stats['removed_duplicates']:>6} 筆")
    print(f"❌ 低頻過濾:     {self.stats['removed_low_frequency']:>6} 筆")
    print(f"✅ 最終保留:     {self.stats['valid_samples']:>6} 筆")

    if self.stats['total_samples'] > 0:
      retention_rate = self.stats['valid_samples'] / self.stats[
        'total_samples'] * 100
      print(f"📈 保留率:       {retention_rate:>5.1f}%")


def main():
  """主函數"""
  print("🛠️  CodeT5 Commit Message 資料預處理工具")
  print("=" * 60)

  if len(sys.argv) < 2:
    print("❌ 使用方法:")
    print(f"   python {sys.argv[0]} <輸入檔案路徑> [輸出檔案路徑]")
    print("\n範例:")
    print(f"   python {sys.argv[0]} spring-boot-training.json")
    print(f"   python {sys.argv[0]} data.json cleaned_data.json")
    return

  input_path = sys.argv[1]
  output_path = sys.argv[2] if len(sys.argv) > 2 else None

  if not os.path.exists(input_path):
    print(f"❌ 檔案不存在: {input_path}")
    return

  # 建立預處理器
  preprocessor = CommitDataPreprocessor()

  try:
    # 執行預處理
    result_path = preprocessor.preprocess_data(
        data_path=input_path,
        output_path=output_path,
        max_input_length=2000,  # diff 最大長度
        max_output_length=100,  # commit message 最大長度
        min_frequency=0.01  # 最小頻率閾值 1%
    )

    print(f"\n🎉 預處理完成！")
    print(f"💡 在訓練程式中使用:")
    print(f"   data_path = \"{result_path}\"")

  except Exception as e:
    print(f"❌ 預處理失敗: {e}")
    raise e


if __name__ == "__main__":
  main()