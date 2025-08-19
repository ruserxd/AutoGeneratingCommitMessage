import json
import sys
import re


def remove_trailing_dots(text):
  """移除字串末尾的句點"""
  if not text:
    return text

  # 移除末尾的句點，支援中英文句點
  while text.endswith('.') or text.endswith('。'):
    text = text[:-1].rstrip()

  return text


def filter_multiple_newlines(text):
  """過濾多個連續的換行符，將多個\n合併為單個\n"""
  if not text:
    return text

  # 使用正規表達式將多個連續的換行符替換為單個換行符
  # \n{2,} 匹配兩個或更多連續的換行符
  filtered_text = re.sub(r'\n{2,}', '\n', str(text))

  return filtered_text


def remove_moe_header(text):
  """移除 MOE 標頭文字"""
  if not text:
    return text

  # 移除 MOE 相關的標頭文字
  # 處理以分隔線開始的格式：\n-------------\nCreated by MOE...
  pattern1 = r'\n-+\nCreated by MOE:.*?\nMOE_MIGRATED_REVID=.*?(?=\n|$)'
  filtered_text = re.sub(pattern1, '', str(text), flags=re.DOTALL)

  # 處理直接以 Created by MOE 開始的格式
  pattern2 = r'\nCreated by MOE:.*?\nMOE_MIGRATED_REVID=.*?(?=\n|$)'
  filtered_text = re.sub(pattern2, '', filtered_text, flags=re.DOTALL)

  # 處理老格式（空格開頭的）
  pattern3 = r' -+ Created by MOE: http://code\.google\.com/p/moe-java MOE_MIGRATED_REVID=.*?(?=\n|$)'
  filtered_text = re.sub(pattern3, '', filtered_text)

  # 移除可能殘留的空白分隔線
  pattern4 = r'\n-+\n*$'
  filtered_text = re.sub(pattern4, '', filtered_text)

  return filtered_text


def process_json_file(input_file, output_file=None):
  """處理JSON文件，移除output欄位末尾的句點、過濾多個換行符和移除MOE標頭"""

  # 讀取JSON文件
  with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

  modified_count = 0
  newline_filtered_count = 0
  moe_removed_count = 0

  # 處理每個項目
  for item in data:
    if isinstance(item, dict) and 'output' in item:
      original = item['output']

      # 先移除末尾句點
      modified = remove_trailing_dots(str(original))

      # 再過濾多個換行符
      filtered = filter_multiple_newlines(modified)

      # 最後移除 MOE 標頭
      final = remove_moe_header(filtered)

      # 檢查是否有變更
      if original != final:
        item['output'] = final
        modified_count += 1

        # 單獨統計各種處理的數量
        if modified != filtered:
          newline_filtered_count += 1
        if filtered != final:
          moe_removed_count += 1

  # 保存結果
  output_path = output_file if output_file else input_file
  with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

  print(f"✅ 處理完成!")
  print(f"   修改了 {modified_count}/{len(data)} 個項目")
  print(f"   其中 {newline_filtered_count} 個項目過濾了多個換行符")
  print(f"   其中 {moe_removed_count} 個項目移除了MOE標頭")

  return modified_count


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("使用方法: python remove_dots.py <input_file> [output_file]")
    print("範例: python remove_dots.py data.json")
    print("範例: python remove_dots.py data.json clean_data.json")
    sys.exit(1)

  input_file = sys.argv[1]
  output_file = sys.argv[2] if len(sys.argv) > 2 else None

  try:
    process_json_file(input_file, output_file)
  except Exception as e:
    print(f"❌ 錯誤: {e}")