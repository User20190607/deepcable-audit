#!/usr/bin/env python3
"""
batch_normalize.py — 批量测试规范化引擎

用法：
    python tests/batch_normalize.py
    python tests/batch_normalize.py --json tests/normalize_cases.json
    python tests/batch_normalize.py --tag prefix  # 只跑 prefix 标签用例
    python tests/batch_normalize.py --verbose      # 显示详细结果

返回码：
    0 = 全部通过
    1 = 有失败
"""
import sys, json, argparse
from pathlib import Path

# 保证能找到 deepcable_normalize
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from deepcable_normalize import normalize


def load_cases(path: Path) -> list[dict]:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description='DeepCable 批量测试')
    ap.add_argument('--json', default=Path(__file__).parent / 'normalize_cases.json')
    ap.add_argument('--tag', help='只跑指定标签的用例')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    cases = load_cases(Path(args.json))
    if args.tag:
        cases = [c for c in cases if args.tag in c.get('tags', [])]
        print(f'筛选标签 "{args.tag}"：{len(cases)} 个用例\n')

    passed = failed = 0
    for c in cases:
        raw = c['raw']
        expected = c['expected']
        result = normalize(raw)
        tags = ' '.join(c.get('tags', []))
        if result == expected:
            passed += 1
            if args.verbose:
                print(f'  ✓ {raw:45s} → {result}  [{tags}]')
        else:
            failed += 1
            print(f'  ✗ {raw:45s} → {result!r}')
            print(f'    expected: {expected!r}')
            print(f'    tags: [{tags}]')

    total = passed + failed
    print(f'\n{"="*50}')
    print(f'  总计: {total}  通过: {passed}  失败: {failed}')
    if total:
        print(f'  通过率: {passed/total*100:.1f}%')
    print(f'{"="*50}')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
