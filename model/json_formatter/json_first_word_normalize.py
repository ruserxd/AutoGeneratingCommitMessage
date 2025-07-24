import json
import sys
from pathlib import Path


def normalize_commit_message(text):
  """將 commit message 標準化為標準類型，修正文法錯誤"""

  # 標準類型
  standard_types = {'feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore'}

  def clean_duplicates(text):
    """移除重複的句子或短語"""
    if not text:
      return text

    # 移除明顯的重複（相同的句子出現兩次）
    sentences = text.split('. ')
    if len(sentences) >= 2:
      # 檢查是否有完全相同的句子
      seen = set()
      cleaned_sentences = []
      for sentence in sentences:
        sentence = sentence.strip()
        if sentence and sentence not in seen:
          seen.add(sentence)
          cleaned_sentences.append(sentence)
      if len(cleaned_sentences) < len(sentences):
        return '. '.join(cleaned_sentences)

    # 檢查簡單的詞語重複
    words = text.split()
    if len(words) > 4:
      # 尋找重複的短語模式
      half_point = len(words) // 2
      first_half = ' '.join(words[:half_point])
      second_half = ' '.join(words[half_point:])

      # 如果前半段和後半段相似度很高，保留前半段
      if first_half.lower() == second_half.lower():
        return first_half

    return text

  # 動詞映射規則 - 將關鍵詞映射到適當的動詞
  verb_mappings = {
    # feat - 新功能相關動詞
    'feature': 'Add', 'add': 'Add', 'added': 'Add', 'create': 'Create',
    'created': 'Create', 'implement': 'Implement', 'implemented': 'Implement',
    'introduce': 'Introduce', 'introduced': 'Introduce', 'new': 'Add',
    'enable': 'Enable', 'enabled': 'Enable', 'support': 'Add', 'allow': 'Allow',

    # fix - 修復相關動詞
    'fixed': 'Fix', 'fixes': 'Fix', 'repair': 'Fix', 'repaired': 'Fix',
    'correct': 'Fix', 'corrected': 'Fix', 'resolve': 'Fix', 'resolved': 'Fix',
    'handle': 'Handle', 'handled': 'Handle', 'prevent': 'Fix',
    'prevented': 'Fix',
    'avoid': 'Fix', 'avoided': 'Fix',

    # docs - 文檔相關動詞
    'doc': 'Update', 'document': 'Add', 'documented': 'Add',
    'documentation': 'Update', 'readme': 'Update', 'comment': 'Add',
    'commented': 'Add', 'comments': 'Update',

    # style - 格式相關動詞
    'format': 'Format', 'formatted': 'Format', 'polish': 'Polish',
    'polished': 'Polish', 'clean': 'Clean', 'cleaned': 'Clean',
    'cleanup': 'Clean up', 'indent': 'Fix', 'whitespace': 'Fix',
    'spacing': 'Fix',

    # refactor - 重構相關動詞
    'core': 'Refactor', 'refactored': 'Refactor', 'restructure': 'Restructure',
    'restructured': 'Restructure', 'reorganize': 'Reorganize',
    'reorganized': 'Reorganize', 'simplify': 'Simplify',
    'simplified': 'Simplify',
    'optimize': 'Optimize', 'optimized': 'Optimize', 'improve': 'Improve',
    'improved': 'Improve', 'enhance': 'Enhance', 'enhanced': 'Enhance',
    'rename': 'Rename', 'renamed': 'Rename', 'move': 'Move', 'moved': 'Move',
    'extract': 'Extract', 'extracted': 'Extract',

    # test - 測試相關動詞
    'tests': 'Add', 'tested': 'Add', 'testing': 'Add', 'spec': 'Add',
    'specs': 'Add', 'unit': 'Add', 'mock': 'Add', 'mocked': 'Add',
    'verify': 'Add', 'verified': 'Add', 'validate': 'Add', 'validated': 'Add',

    # chore - 雜項相關動詞
    'update': 'Update', 'updated': 'Update', 'upgrade': 'Upgrade',
    'upgraded': 'Upgrade', 'remove': 'Remove', 'removed': 'Remove',
    'delete': 'Delete', 'deleted': 'Delete', 'change': 'Change',
    'changed': 'Change', 'modify': 'Modify', 'modified': 'Modify',
    'replace': 'Replace', 'replaced': 'Replace', 'use': 'Use',
    'make': 'Make', 'made': 'Make', 'set': 'Set', 'configure': 'Configure',
    'configured': 'Configure', 'config': 'Update', 'build': 'Build',
    'built': 'Build', 'deploy': 'Deploy', 'deployed': 'Deploy',
    'merge': 'Merge', 'merged': 'Merge', 'revert': 'Revert',
    'reverted': 'Revert', 'bump': 'Bump', 'bumped': 'Bump',
    'version': 'Update', 'release': 'Release', 'disable': 'Disable',
    'disabled': 'Disable', 'ignore': 'Ignore', 'ignored': 'Ignore'
  }

  # 動詞到類型的映射
  verb_to_type = {
    # feat 類型
    'Add': 'feat', 'Create': 'feat', 'Implement': 'feat', 'Introduce': 'feat',
    'Enable': 'feat', 'Allow': 'feat',

    # fix 類型
    'Fix': 'fix', 'Handle': 'fix',

    # docs 類型 (當上下文是文檔時)

    # style 類型
    'Format': 'style', 'Polish': 'style', 'Clean': 'style', 'Clean up': 'style',

    # refactor 類型
    'Refactor': 'refactor', 'Restructure': 'refactor', 'Reorganize': 'refactor',
    'Simplify': 'refactor', 'Optimize': 'refactor', 'Improve': 'refactor',
    'Enhance': 'refactor', 'Rename': 'refactor', 'Move': 'refactor',
    'Extract': 'refactor',

    # chore 類型 (預設大部分維護性工作)
    'Update': 'chore', 'Upgrade': 'chore', 'Remove': 'chore', 'Delete': 'chore',
    'Change': 'chore', 'Modify': 'chore', 'Replace': 'chore', 'Use': 'chore',
    'Make': 'chore', 'Set': 'chore', 'Configure': 'chore', 'Build': 'chore',
    'Deploy': 'chore', 'Merge': 'chore', 'Revert': 'chore', 'Bump': 'chore',
    'Release': 'chore', 'Disable': 'chore', 'Ignore': 'chore'
  }

  if not text or not text.strip():
    return None

  # 先清理重複內容
  text = clean_duplicates(text.strip())
  words = text.split()
  if not words:
    return None

  first_word = words[0].lower()
  rest_text = ' '.join(words[1:]) if len(words) > 1 else ''

  # 特殊處理：如果第一個詞是 "chore" 但後面沒有動詞
  if first_word == 'chore':
    if len(words) < 2:
      return None

    second_word = words[1].lower()
    remaining_text = ' '.join(words[2:]) if len(words) > 2 else ''

    # 檢查第二個詞是否需要映射為動詞
    if second_word in verb_mappings:
      verb = verb_mappings[second_word]
      clean_remaining = clean_duplicates(
        remaining_text) if remaining_text else ''
      return f"chore: {verb} {clean_remaining}".strip()
    else:
      # 第二個詞不是需要映射的詞，可能已經是動詞
      # 檢查是否看起來像動詞（簡單檢查）
      clean_remaining = clean_duplicates(
        remaining_text) if remaining_text else ''
      if clean_remaining or second_word.endswith(('e', 'd', 's')):
        return f"chore: {second_word.capitalize()} {clean_remaining}".strip()
      else:
        # 可能是名詞，需要加動詞
        return f"chore: Update {second_word} {clean_remaining}".strip()

  # 檢查是否已經是標準格式 (type: message)
  if ':' in text:
    parts = text.split(':', 1)
    if len(parts) == 2:
      type_part = parts[0].strip().lower()
      message_part = parts[1].strip()

      if type_part in standard_types:
        clean_message = clean_duplicates(message_part)
        return f"{type_part}: {clean_message}"

  # 檢查第一個詞是否需要映射
  if first_word in verb_mappings:
    verb = verb_mappings[first_word]
    commit_type = verb_to_type.get(verb, 'chore')  # 預設為 chore

    # 特殊判斷：如果上下文暗示是文檔
    if any(doc_word in text.lower() for doc_word in
           ['readme', 'doc', 'comment', 'documentation']):
      commit_type = 'docs'
    # 特殊判斷：如果上下文暗示是測試
    elif any(test_word in text.lower() for test_word in
             ['test', 'spec', 'mock', 'unit']):
      commit_type = 'test'

    clean_rest = clean_duplicates(rest_text) if rest_text else ''
    return f"{commit_type}: {verb} {clean_rest}".strip()

  # 檢查是否已經是標準類型開頭
  if first_word in standard_types:
    if rest_text:
      clean_rest = clean_duplicates(rest_text)
      return f"{first_word}: {clean_rest}"
    else:
      return None  # 只有類型沒有內容

  # 無法處理的情況
  return None


def process_file(input_file, field='output'):
  """處理 JSON 檔案，只保留能標準化的 commit 類型記錄"""

  # 讀取檔案
  with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

  if not isinstance(data, list):
    data = [data]

  # 處理資料
  filtered_data = []
  stats = {'total': 0, 'kept': 0, 'removed': 0}
  examples = {'kept': [], 'removed': []}

  for item in data:
    if not isinstance(item, dict) or field not in item:
      continue

    stats['total'] += 1
    original_text = item[field]
    normalized_text = normalize_commit_message(original_text)

    if normalized_text:
      # 保留並更新
      item[field] = normalized_text
      filtered_data.append(item)
      stats['kept'] += 1

      # 收集範例
      if len(examples['kept']) < 5:
        examples['kept'].append(f"  '{original_text}' → '{normalized_text}'")
    else:
      # 移除
      stats['removed'] += 1

      # 收集範例
      if len(examples['removed']) < 5:
        examples['removed'].append(f"  '{original_text}'")

  # 生成輸出檔案名
  input_path = Path(input_file)
  output_file = input_path.parent / f"{input_path.stem}_normalized{input_path.suffix}"

  # 儲存結果
  with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f, ensure_ascii=False, indent=2)

  # 顯示統計和範例
  print(f"處理完成:")
  print(f"  輸入檔案: {input_file}")
  print(f"  輸出檔案: {output_file}")
  print(f"  總記錄數: {stats['total']}")
  print(f"  保留記錄: {stats['kept']}")
  print(f"  移除記錄: {stats['removed']}")

  if examples['kept']:
    print(f"\n保留範例:")
    for example in examples['kept']:
      print(example)

  if examples['removed']:
    print(f"\n移除範例:")
    for example in examples['removed']:
      print(example)


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("使用方法: python script.py <input_file> [field_name]")
    print("範例: python script.py data.json")
    print("範例: python script.py data.json commit_message")
    sys.exit(1)

  input_file = sys.argv[1]
  field = sys.argv[2] if len(sys.argv) > 2 else 'output'

  if not Path(input_file).exists():
    print(f"錯誤: 找不到檔案 {input_file}")
    sys.exit(1)

  process_file(input_file, field)