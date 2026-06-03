#!/usr/bin/env python3
"""
真实电缆清单数据测试
从实际工程清单中提取的电缆型号进行测试
"""

import sys
sys.path.insert(0, '/workspace')

from deepcable_normalize import normalize

# 从真实清单中提取的电缆型号数据
REAL_WORLD_CABLES = [
    # 基本 YJV 系列
    "YJV-1/3x35+1x16",
    "YJV-1/3x25+1x16",
    "YJV-1/4x10",
    "YJV-1/4x6",
    "YJV-1/4x4",
    "YJV-1/5x4",
    "YJV-1/4x50+1x25",
    "YJV-1/3x10",
    "YJV-1/3x50+1x25",
    "YJV-1/3x95+2x50",
    "YJV-1/5x35",
    "YJV-1/5x16",
    "YJV-1/5x10",
    "YJV-1/5x6",
    "YJV-1/3x6",
    "YJV-1/3x4",
    "YJV-1/3x2.5",
    "YJV-1/5x25",
    "YJV-1/3x185+2x95",
    "YJV-1/4x150+1x70",
    "YJV-1/4*50",  # 使用 * 号
    "YJV-1/3x185+1x95",
    "YJV-1/3x150+2x70",
    "YJV-1/3x120+2x70",
    "YJV-1/4x120+1x70",
    "YJV-1/3x70+2x35",
    "YJV-1/4x70+1x35",
    "YJV-1/3x35+2x16",
    "YJV-1/3x25+2x16",
    "YJV-1/4x25+1x16",
    "YJV-1/4x16",
    
    # 耐火电缆 NH-YJV
    "NH-YJV-5x10",
    "NH-YJV-5X4mm2",  # 大写 X + 单位
    "NH-YJV-3X4mm2",  # 大写 X + 单位
    "NH-YJV-1/3x4",
    "NH-YJV-1/5x6",
    
    # 阻燃电缆 ZA/ZR/ZRC
    "ZA-YJV-5*4",  # 使用 * 号
    "ZR-YJV-1/3x6",
    "ZR-YJV-1/4x4",
    "ZRYJV-1/5x4",  # 无分隔符
    "ZRC-YJV22-10kv-3x70",  # 10kV 高压
    "ZR-YJV-8.7/15-3x70",  # 8.7/15kV 高压
    "ZR-YJV-1/5x16",
    "ZR-YJV-1/4x150+1x70",
    "ZR-YJV-1/3x150+2x70",
    "ZR-YJV22-1/3×70+2×35",  # 使用 × 符号
    "ZR-YJV22-1/3×6",
    
    # 钢带铠装电缆 YJV22
    "YJV22-1/5x16",
    
    # 电缆头（从项目名称中提取规格）
    "4x50+1x25",
    "3x50+1x25",
    "3x35+1x16",
    "3x25+1x16",
    "16mm2以下",
    "3x95+2x50",
    "5x35",
    "3*150+2*70",  # 使用 * 号
    "4*50",  # 使用 * 号
    "3x185+1x95",
    "3x150+2x70",
    "4x150+1x70",
    "3x120+2x70",
    "4x120+1x70",
    "3x70+2x35",
    "4x70+1x35",
    "4x50+1x25",
    "3x35+2x16",
    "3x25+2x16",
    "5x25",
    "4x35+1x16",
]

def test_real_world_cables():
    """测试真实世界电缆数据"""
    print("=" * 80)
    print("真实电缆清单数据批量测试")
    print("=" * 80)
    print()
    
    success_count = 0
    fail_count = 0
    results = []
    
    for cable in REAL_WORLD_CABLES:
        try:
            result = normalize(cable)
            if result:
                success_count += 1
                status = "✓"
            else:
                fail_count += 1
                status = "✗"
            
            results.append({
                'original': cable,
                'status': status,
                'result': result
            })
        except Exception as e:
            fail_count += 1
            results.append({
                'original': cable,
                'status': '✗',
                'error': str(e)
            })
    
    # 打印结果
    print(f"总测试数：{len(REAL_WORLD_CABLES)}")
    print(f"成功：{success_count}")
    print(f"失败：{fail_count}")
    print(f"成功率：{success_count/len(REAL_WORLD_CABLES)*100:.1f}%")
    print()
    
    # 显示失败的案例（如果有）
    if fail_count > 0:
        print("-" * 80)
        print("失败的案例:")
        print("-" * 80)
        for r in results:
            if r['status'] == '✗':
                print(f"  原始：{r['original']}")
                if 'error' in r:
                    print(f"  错误：{r['error']}")
                else:
                    print(f"  结果：{r['result']}")
                print()
    
    # 显示部分成功案例
    print("-" * 80)
    print("部分成功案例展示:")
    print("-" * 80)
    display_count = 0
    for r in results:
        if r['status'] == '✓' and display_count < 20:
            standardized = r['result']
            print(f"  {r['original']:35s} → {standardized}")
            display_count += 1
    
    if success_count > 20:
        print(f"  ... 还有 {success_count - 20} 个成功案例")
    
    print()
    print("=" * 80)
    
    return success_count == len(REAL_WORLD_CABLES)

if __name__ == '__main__':
    import time
    start = time.time()
    success = test_real_world_cables()
    elapsed = (time.time() - start) * 1000
    print(f"总耗时：{elapsed:.2f}ms")
    print(f"平均耗时：{elapsed/len(REAL_WORLD_CABLES):.3f}ms/个")
    
    sys.exit(0 if success else 1)
