import json
import re


def remove_first_word_colon(text):
  """
  移除第一個字後面的冒號，保留字本身

  Args:
      text (str): 原始文本

  Returns:
      str: 處理後的文本
  """
  if not text:
    return text

  # 匹配第一個字後面的冒號和可能的空格
  # 模式：開頭的單詞 + 冒號 + 可選空格 + 其餘內容
  pattern = r'^(\w+):\s*(.*)'
  match = re.match(pattern, text.strip())

  if match:
    first_word = match.group(1)  # 第一個字
    rest_content = match.group(2)  # 後面的內容

    # 重新組合，在第一個字和後面內容之間加一個空格
    if rest_content:
      return f"{first_word} {rest_content}"
    else:
      return first_word
  else:
    # 如果沒有匹配的模式，返回原文
    return text


def process_json_file(input_path, output_path=None):
  """
  處理 JSON 檔案中的所有 output 欄位，移除第一個字後的冒號

  Args:
      input_path (str): 輸入檔案路徑
      output_path (str): 輸出檔案路徑，如果為 None 則自動生成
  """

  print(f"🔄 開始處理檔案: {input_path}")

  # 讀取 JSON 資料
  with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

  # 統計轉換情況
  stats = {
    'total': len(data),
    'transformed': 0,
    'unchanged': 0
  }

  # 處理每一筆資料
  for i, item in enumerate(data):
    if 'output' not in item:
      continue

    original = item['output']
    transformed = remove_first_word_colon(original)

    if original != transformed:
      item['output'] = transformed
      stats['transformed'] += 1

      # 顯示轉換範例（前 10 個）
      if stats['transformed'] <= 10:
        print(f"🔄 範例 {stats['transformed']}:")
        print(
          f"   原始: {original[:100]}{'...' if len(original) > 100 else ''}")
        print(
          f"   轉換: {transformed[:100]}{'...' if len(transformed) > 100 else ''}")
        print()
    else:
      stats['unchanged'] += 1

  # 決定輸出檔案名
  if output_path is None:
    output_path = input_path.replace('.json', '_no_colon.json')

  # 儲存結果
  with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

  # 顯示統計結果
  print(f"📊 處理完成！")
  print(f"📁 輸出檔案: {output_path}")
  print(f"📈 統計結果:")
  print(f"   總計: {stats['total']} 筆")
  print(f"   已轉換: {stats['transformed']} 筆")
  print(f"   未變更: {stats['unchanged']} 筆")

  return output_path


def test_remove_colon_function():
  """測試移除冒號函數"""

  test_cases = [
    "Security: simplify index audit trail stopping\nThe IndexAuditTrail had both a stop and close method",
    "Fix: handle null pointer exception in mapper",
    "Feature: add new authentication method",
    "Docs: update installation guide",
    "Refactor: simplify the validation logic",
    "Build: update maven dependencies",
    "Test: add integration tests",
    "Performance: optimize database queries",
    "Style: format code according to guidelines",
    "regular commit message without colon",
    "Multiple: words: with: colons",
    "OnlyColon:",
    "NoColon here at all",
    "123Number: starting with number",
    "UPPERCASE: message here",
    "lowercase: message here",
    ": starting with colon",
    "",  # 空字串
    "Word:NoSpace",  # 沒有空格
  ]

  print("🧪 測試移除冒號函數:")
  print("=" * 80)

  for i, test_case in enumerate(test_cases, 1):
    result = remove_first_word_colon(test_case)

    # 顯示較短的版本以便閱讀
    display_original = test_case[:60] + "..." if len(
      test_case) > 60 else test_case
    display_result = result[:60] + "..." if len(result) > 60 else result

    print(f"{i:2d}. 原始: {repr(display_original)}")
    print(f"    轉換: {repr(display_result)}")

    if test_case != result:
      print("    ✅ 已轉換")
    else:
      print("    ⚪ 無變更")
    print()


def batch_process_files(file_list):
  """批次處理多個檔案"""

  for file_path in file_list:
    try:
      print(f"\n{'=' * 80}")
      process_json_file(file_path)
    except Exception as e:
      print(f"❌ 處理檔案 {file_path} 時發生錯誤: {e}")


def find_colon_patterns(input_path):
  """分析檔案中有冒號的模式"""

  print(f"🔍 分析檔案中的冒號模式: {input_path}")

  with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

  colon_patterns = {}
  total_with_colon = 0

  for item in data:
    output = item.get('output', '')

    # 檢查是否符合 "字:..." 的模式
    match = re.match(r'^(\w+):\s*', output)
    if match:
      first_word = match.group(1).lower()
      colon_patterns[first_word] = colon_patterns.get(first_word, 0) + 1
      total_with_colon += 1

  print(f"\n📊 冒號模式統計 (總共 {total_with_colon} 筆):")
  print("-" * 40)

  # 按頻率排序顯示
  for word, count in sorted(colon_patterns.items(), key=lambda x: x[1],
                            reverse=True):
    percentage = (count / total_with_colon) * 100
    print(f"{word:15} : {count:4d} 次 ({percentage:5.1f}%)")

  return colon_patterns


if __name__ == "__main__":
  import sys

  # 測試移除冒號函數
  test_remove_colon_function()

  # 如果有命令行參數，處理指定檔案
  if len(sys.argv) > 1:
    input_file = sys.argv[1]

    # 檢查是否是分析模式
    if len(sys.argv) > 2 and sys.argv[2] == '--analyze':
      try:
        find_colon_patterns(input_file)
      except Exception as e:
        print(f"❌ 分析失敗: {e}")
    else:
      # 正常處理模式
      output_file = sys.argv[2] if len(sys.argv) > 2 else None

      try:
        process_json_file(input_file, output_file)
      except FileNotFoundError:
        print(f"❌ 檔案不存在: {input_file}")
      except json.JSONDecodeError:
        print(f"❌ JSON 格式錯誤: {input_file}")
      except Exception as e:
        print(f"❌ 處理失敗: {e}")
  else:
    print("\n💡 使用方法:")
    print(f"   python {sys.argv[0]} <輸入檔案> [輸出檔案]")
    print(f"   python {sys.argv[0]} <輸入檔案> --analyze  # 分析冒號模式")
    print("\n範例:")
    print(f"   python {sys.argv[0]} data.json")
    print(f"   python {sys.argv[0]} data.json cleaned_data.json")
    print(f"   python {sys.argv[0]} data.json --analyze")