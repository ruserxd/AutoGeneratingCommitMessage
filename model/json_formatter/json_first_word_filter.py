import json
import re
import argparse


def extract_first_word(text):
  """提取第一個單詞"""
  if not text:
    return ""

  text = text.strip()
  match = re.match(r'\w+', text)
  return match.group().lower() if match else ""


def filter_commits(input_file, output_file=None):
  """過濾提交訊息，只保留指定動詞開頭的條目"""

  # 允許的動詞
  ALLOWED_VERBS = {'fix', 'add', 'remove', 'upgrade', 'use', 'make', 'change',
                   'improve'}

  # 讀取數據
  with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

  # 過濾數據
  filtered_data = []
  verb_count = {}

  for item in data:
    if 'output' in item and item['output']:
      first_word = extract_first_word(item['output'])
      verb_count[first_word] = verb_count.get(first_word, 0) + 1

      if first_word in ALLOWED_VERBS:
        filtered_data.append(item)

  # 輸出統計
  total = len(data)
  kept = len(filtered_data)

  print(f"原始資料: {total} 條")
  print(f"保留資料: {kept} 條 ({kept / total * 100:.1f}%)")
  print(f"移除資料: {total - kept} 條")
  print()

  print("保留的動詞統計:")
  for verb in ALLOWED_VERBS:
    count = verb_count.get(verb, 0)
    if count > 0:
      print(f"  {verb}: {count} 條")

  # 保存結果
  if output_file is None:
    output_file = input_file.replace('.json', '_filtered.json')

  with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f, ensure_ascii=False, indent=2)

  print(f"\n✅ 結果已保存至: {output_file}")


def main():
  parser = argparse.ArgumentParser(
    description='過濾提交訊息 - 只保留8個核心動詞')
  parser.add_argument('input_file', help='輸入的 JSON 檔案')
  parser.add_argument('-o', '--output', help='輸出檔案路徑')

  args = parser.parse_args()
  filter_commits(args.input_file, args.output)


if __name__ == "__main__":
  main()