import json
import argparse
import re
from pathlib import Path


def remove_test_prefix(json_file):
  """移除 JSON 中 output 欄位的所有 [TEST]/[TESTS]/[Test]/[Tests] 等"""

  try:
    # 讀取 JSON 檔案
    with open(json_file, 'r', encoding='utf-8') as f:
      data = json.load(f)

    print(f"📖 讀取檔案: {json_file}")
    print(f"📊 總記錄: {len(data):,}")

    # 處理資料
    modified_count = 0

    for item in data:
      if isinstance(item, dict) and 'output' in item:
        original = item['output']
        # 移除所有 [TEST]/[Test]/[TESTS]/[Tests] 等（忽略大小寫，包含前後空格和換行）
        modified = re.sub(r'\s*\[tests?\]\s*', ' ', original,
                          flags=re.IGNORECASE)
        # 清理多餘的空格和換行
        modified = re.sub(r'\s+', ' ', modified).strip()

        if modified != original:
          item['output'] = modified
          modified_count += 1

    # 產生輸出檔名
    input_path = Path(json_file)
    output_path = input_path.parent / f"{input_path.stem}_no_test{input_path.suffix}"

    # 儲存結果
    with open(output_path, 'w', encoding='utf-8') as f:
      json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 處理完成!")
    print(f"🔧 修改記錄: {modified_count:,}")
    print(f"📂 輸出檔案: {output_path.name}")

    return True

  except Exception as e:
    print(f"❌ 處理失敗: {e}")
    return False


def main():
  parser = argparse.ArgumentParser(
    description="移除 JSON 中 output 的所有 [TEST]")
  parser.add_argument('json_file', help='JSON 檔案路徑')

  args = parser.parse_args()

  # 檢查檔案是否存在
  if not Path(args.json_file).exists():
    print(f"❌ 檔案不存在: {args.json_file}")
    return

  success = remove_test_prefix(args.json_file)

  if success:
    print("🎉 處理成功！")
  else:
    print("💥 處理失敗")


if __name__ == "__main__":
  main()