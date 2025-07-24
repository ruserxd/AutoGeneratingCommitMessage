import json
import argparse
import sys
from pathlib import Path


class VerbNormalizer:
  """動詞標準化器 - 將 commit message 中的動詞轉換為標準形式"""

  def __init__(self):
    # 定義動詞變化規則
    self.verb_mappings = {
      # 過去式 → 現在式
      'added': 'add',
      'removed': 'remove',
      'deleted': 'delete',
      'fixed': 'fix',
      'updated': 'update',
      'changed': 'change',
      'moved': 'move',
      'renamed': 'rename',
      'created': 'create',
      'improved': 'improve',
      'optimized': 'optimize',
      'refactored': 'refactor',
      'cleaned': 'clean',
      'simplified': 'simplify',
      'enhanced': 'enhance',
      'modified': 'modify',
      'replaced': 'replace',
      'upgraded': 'upgrade',
      'downgraded': 'downgrade',
      'merged': 'merge',
      'split': 'split',
      'reverted': 'revert',
      'restored': 'restore',
      'corrected': 'correct',
      'adjusted': 'adjust',
      'implemented': 'implement',
      'introduced': 'introduce',
      'deprecated': 'deprecate',
      'disabled': 'disable',
      'enabled': 'enable',

      # 現在進行式 → 現在式
      'adding': 'add',
      'removing': 'remove',
      'deleting': 'delete',
      'fixing': 'fix',
      'updating': 'update',
      'changing': 'change',
      'moving': 'move',
      'renaming': 'rename',
      'creating': 'create',
      'improving': 'improve',
      'optimizing': 'optimize',
      'refactoring': 'refactor',
      'cleaning': 'clean',
      'simplifying': 'simplify',
      'enhancing': 'enhance',
      'modifying': 'modify',
      'replacing': 'replace',
      'upgrading': 'upgrade',
      'downgrading': 'downgrade',
      'merging': 'merge',
      'splitting': 'split',
      'reverting': 'revert',
      'restoring': 'restore',
      'correcting': 'correct',
      'adjusting': 'adjust',
      'implementing': 'implement',
      'introducing': 'introduce',
      'deprecating': 'deprecate',
      'disabling': 'disable',
      'enabling': 'enable',

      # 複數 → 單數
      'tests': 'test',
      'fixes': 'fix',
      'updates': 'update',
      'changes': 'change',
      'docs': 'doc',
      'dependencies': 'dependency',
      'configs': 'config',
      'settings': 'setting',
      'imports': 'import',
      'exports': 'export',
      'methods': 'method',
      'functions': 'function',
      'classes': 'class',
      'files': 'file',
      'logs': 'log',
      'errors': 'error',
      'warnings': 'warning',
      'features': 'feature',
      'issues': 'issue',
      'bugs': 'bug',
      'patches': 'patch',
      'scripts': 'script',
      'tools': 'tool',
      'utils': 'util',
      'helpers': 'helper',
      'components': 'component',
      'modules': 'module',
      'packages': 'package',
      'libraries': 'library',
      'resources': 'resource',
      'assets': 'asset',
      'images': 'image',
      'styles': 'style',
      'templates': 'template',

      # 第三人稱單數 → 現在式
      'adds': 'add',
      'removes': 'remove',
      'deletes': 'delete',
      'fixes': 'fix',
      'updates': 'update',
      'changes': 'change',
      'moves': 'move',
      'renames': 'rename',
      'creates': 'create',
      'improves': 'improve',
      'optimizes': 'optimize',
      'refactors': 'refactor',
      'cleans': 'clean',
      'simplifies': 'simplify',
      'enhances': 'enhance',
      'modifies': 'modify',
      'replaces': 'replace',
      'upgrades': 'upgrade',
      'downgrades': 'downgrade',
      'merges': 'merge',
      'splits': 'split',
      'reverts': 'revert',
      'restores': 'restore',
      'corrects': 'correct',
      'adjusts': 'adjust',
      'implements': 'implement',
      'introduces': 'introduce',
      'deprecates': 'deprecate',
      'disables': 'disable',
      'enables': 'enable',

      # 不規則動詞
      'ran': 'run',
      'built': 'build',
      'made': 'make',
      'did': 'do',
      'got': 'get',
      'went': 'go',
      'came': 'come',
      'took': 'take',
      'gave': 'give',
      'found': 'find',
      'thought': 'think',
      'brought': 'bring',
      'bought': 'buy',
      'caught': 'catch',
      'taught': 'teach',
      'fought': 'fight',
      'sought': 'seek',
      'wrote': 'write',
      'broke': 'break',
      'spoke': 'speak',
      'chose': 'choose',
      'drove': 'drive',
      'rode': 'ride',
      'rose': 'rise',
      'wore': 'wear',
      'tore': 'tear',
      'bore': 'bear',
      'swore': 'swear',
      'threw': 'throw',
      'grew': 'grow',
      'knew': 'know',
      'flew': 'fly',
      'drew': 'draw',
      'saw': 'see',
      'was': 'be',
      'were': 'be',
      'had': 'have',

      'update': 'upgrade'
    }

    # 統計資訊
    self.stats = {
      'total_processed': 0,
      'normalized': 0,
      'unchanged': 0,
      'normalization_types': {}
    }

  def normalize_first_word(self, text):
    """
    標準化文本中的第一個字

    Args:
        text (str): 原始文本

    Returns:
        tuple: (normalized_text, was_changed, change_type)
    """
    if not text or not text.strip():
      return text, False, None

    # 分割文本，取得第一個字和其餘內容
    words = text.strip().split()
    if not words:
      return text, False, None

    first_word = words[0].lower()
    rest_words = words[1:] if len(words) > 1 else []

    # 檢查是否需要標準化
    if first_word in self.verb_mappings:
      normalized_word = self.verb_mappings[first_word]

      # 保持原有的大小寫格式
      if words[0][0].isupper():
        normalized_word = normalized_word.capitalize()
      elif words[0].isupper():
        normalized_word = normalized_word.upper()

      # 重新組合文本
      normalized_text = ' '.join([normalized_word] + rest_words)

      # 決定變化類型
      change_type = self._get_change_type(first_word, normalized_word.lower())

      return normalized_text, True, change_type

    return text, False, None

  def _get_change_type(self, original, normalized):
    """判斷變化類型"""
    if original.endswith('ed'):
      return 'past_tense'
    elif original.endswith('ing'):
      return 'present_continuous'
    elif original.endswith('s') and original != normalized + 's':
      return 'plural'
    elif original.endswith('s'):
      return 'third_person'
    else:
      return 'irregular'

  def process_json_file(self, input_path, output_path=None, field='output',
      verbose=False):
    """
    處理 JSON 檔案

    Args:
        input_path (str): 輸入檔案路徑
        output_path (str): 輸出檔案路徑
        field (str): 要處理的欄位名
        verbose (bool): 詳細模式
    """

    # 載入資料
    with open(input_path, 'r', encoding='utf-8') as f:
      data = json.load(f)

    if not isinstance(data, list):
      data = [data]

    print(f"🔄 處理檔案: {input_path}")
    print(f"📝 處理欄位: {field}")
    print("=" * 60)

    # 重置統計
    self.stats = {
      'total_processed': 0,
      'normalized': 0,
      'unchanged': 0,
      'normalization_types': {}
    }

    # 處理每筆資料
    for i, item in enumerate(data):
      if not isinstance(item, dict) or field not in item:
        continue

      original_text = item[field]
      normalized_text, was_changed, change_type = self.normalize_first_word(
        original_text)

      self.stats['total_processed'] += 1

      if was_changed:
        self.stats['normalized'] += 1

        # 統計變化類型
        if change_type:
          self.stats['normalization_types'][change_type] = \
            self.stats['normalization_types'].get(change_type, 0) + 1

        if verbose:
          print(f"📝 記錄 #{i + 1} ({change_type})")
          print(f"   原始: {original_text}")
          print(f"   標準: {normalized_text}")
          print()

        # 更新資料
        item[field] = normalized_text
      else:
        self.stats['unchanged'] += 1

    # 顯示統計結果
    self._print_stats()

    # 儲存結果
    if output_path:
      with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
      print(f"💾 結果已儲存至: {output_path}")

    return data

  def _print_stats(self):
    """顯示統計結果"""
    print("📊 處理統計:")
    print(f"   總計: {self.stats['total_processed']} 筆")
    print(f"   已標準化: {self.stats['normalized']} 筆")
    print(f"   未變更: {self.stats['unchanged']} 筆")

    if self.stats['normalization_types']:
      print(f"\n📈 標準化類型分布:")
      for change_type, count in sorted(
          self.stats['normalization_types'].items()):
        percentage = (count / self.stats['normalized']) * 100 if self.stats[
                                                                   'normalized'] > 0 else 0
        print(f"   {change_type}: {count} 筆 ({percentage:.1f}%)")

  def test_normalization(self):
    """測試標準化功能"""
    test_cases = [
      "removed unused imports from main module",
      "added new feature for authentication",
      "fixed compiler warning in test file",
      "updated documentation for API changes",
      "tests should pass after this change",
      "fixes issue with null pointer exception",
      "changes made to improve performance",
      "docs updated with new examples",
      "dependencies upgraded to latest version",
      "configs modified for production environment",
      "adding support for new file format",
      "removing deprecated methods",
      "fixing memory leak in processing",
      "updating user interface components",
      "creates new database connection pool",
      "improves error handling mechanism",
      "optimizes query performance significantly",
      "refactors code for better maintainability",
      "built new deployment pipeline",
      "made changes to configuration files",
      "found issue in validation logic",
      "thought about better approach",
      "brought new features to production",
      "wrote comprehensive test cases",
      "broke compatibility with old version",
      "chose different implementation strategy",
      "Regular commit message without verb",
      "UPPERCASE COMMIT MESSAGE",
      "lowercase commit message",
    ]

    print("🧪 測試動詞標準化功能:")
    print("=" * 80)

    for i, test_case in enumerate(test_cases, 1):
      normalized, changed, change_type = self.normalize_first_word(test_case)
      status = "✅ 已標準化" if changed else "⚪ 無變更"
      type_info = f" ({change_type})" if change_type else ""

      print(f"{i:2d}. 原始: {test_case}")
      print(f"    標準: {normalized}")
      print(f"    狀態: {status}{type_info}")
      print()


def main():
  """主函數"""
  parser = argparse.ArgumentParser(
      description='動詞標準化工具 - 將 commit message 動詞轉換為標準形式',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog="""
使用範例:
  python verb_normalizer.py input.json
  python verb_normalizer.py data.json --field commit_message
  python verb_normalizer.py input.json --verbose
        """
  )

  parser.add_argument('input', help='要處理的 JSON 檔案路徑')
  parser.add_argument('-f', '--field', default='output',
                      help='要處理的欄位名 (預設: output)')
  parser.add_argument('-v', '--verbose', action='store_true',
                      help='顯示詳細資訊')

  args = parser.parse_args()

  # 檢查檔案存在性
  if not Path(args.input).exists():
    print(f"❌ 輸入檔案不存在: {args.input}")
    sys.exit(1)

  # 生成輸出檔案名
  input_path = Path(args.input)
  output_path = input_path.parent / f"{input_path.stem}_normalized{input_path.suffix}"

  # 處理檔案
  try:
    normalizer = VerbNormalizer()
    normalizer.process_json_file(
        str(input_path),
        str(output_path),
        args.field,
        args.verbose,
    )
  except Exception as e:
    print(f"❌ 處理失敗: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()