import json
import re


def transform_bracket_prefix(text):
  """
  將 output 開頭的 [abc] 轉換成 Abc，或將小寫開頭轉換成大寫開頭

  Args:
      text (str): 原始文本

  Returns:
      str: 轉換後的文本
  """
  if not text:
    return text

  text = text.strip()

  # 先處理方括號前綴
  bracket_pattern = r'^\[([^\]]+)\]\s*(.*)'
  bracket_match = re.match(bracket_pattern, text)

  if bracket_match:
    prefix = bracket_match.group(1)  # 方括號內的內容
    rest = bracket_match.group(2)  # 後面的內容

    # 將前綴轉換為首字母大寫，其餘小寫
    transformed_prefix = prefix.capitalize()

    # 組合結果，確保有空格分隔
    if rest:
      return f"{transformed_prefix} {rest}"
    else:
      return transformed_prefix
  else:
    # 如果沒有方括號前綴，檢查是否需要首字母大寫
    if text and text[0].islower():
      return text[0].upper() + text[1:]
    else:
      return text


def process_json_file(input_path, output_path=None):
  """
  處理 JSON 檔案中的所有 output 欄位

  Args:
      input_path (str): 輸入檔案路徑
      output_path (str): 輸出檔案路徑，如果為 None 則覆蓋原檔案
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
    transformed = transform_bracket_prefix(original)

    if original != transformed:
      item['output'] = transformed
      stats['transformed'] += 1

      # 顯示轉換範例（前 10 個）
      if stats['transformed'] <= 10:
        print(f"🔄 範例 {stats['transformed']}:")
        print(f"   原始: {original}")
        print(f"   轉換: {transformed}")
    else:
      stats['unchanged'] += 1

  # 決定輸出檔案名
  if output_path is None:
    output_path = input_path.replace('.json', '_transformed.json')

  # 儲存結果
  with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

  # 顯示統計結果
  print(f"\n📊 處理完成！")
  print(f"📁 輸出檔案: {output_path}")
  print(f"📈 統計結果:")
  print(f"   總計: {stats['total']} 筆")
  print(f"   已轉換: {stats['transformed']} 筆")
  print(f"   未變更: {stats['unchanged']} 筆")

  return output_path


def test_transform_function():
  """測試轉換函數"""

  test_cases = [
    "[TEST] remove unused currentTypes variable from SearchSourceBuilderTests",
    "[FIX] handle null pointer exception in mapper",
    "[FEAT] add new authentication method",
    "[DOC] update installation guide",
    "[REFACTOR] simplify the validation logic",
    "regular commit message without prefix",
    "[STYLE] format code according to guidelines",
    "[PERF] optimize database query performance",
    "[BUILD] update maven dependencies",
    "[CI] add integration tests to pipeline",
    "[BREAKING] change API signature",
    "[ SPACE ] test with spaces",
    "[]",  # 空方括號
    # 新增小寫開頭的測試案例
    "fixed compiler warnining and removed unused imports",
    "add new feature for user authentication",
    "update documentation for API changes",
    "remove deprecated methods",
    "refactor validation logic",
    "Fix compiler warning",  # 已經大寫開頭
    "ADD new functionality",  # 全大寫
  ]

  print("🧪 測試轉換函數:")
  print("=" * 60)

  for i, test_case in enumerate(test_cases, 1):
    result = transform_bracket_prefix(test_case)
    print(f"{i:2d}. 原始: {test_case}")
    print(f"    轉換: {result}")
    print()


def batch_process_files(file_list):
  """批次處理多個檔案"""

  for file_path in file_list:
    try:
      print(f"\n{'=' * 60}")
      process_json_file(file_path)
    except Exception as e:
      print(f"❌ 處理檔案 {file_path} 時發生錯誤: {e}")


if __name__ == "__main__":
  import sys

  # 測試轉換函數
  test_transform_function()

  # 如果有命令行參數，處理指定檔案
  if len(sys.argv) > 1:
    input_file = sys.argv[1]
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
    print(f"   python {__file__} <輸入檔案> [輸出檔案]")
    print("\n範例:")
    print(f"   python {__file__} data.json")
    print(f"   python {__file__} data.json transformed_data.json")