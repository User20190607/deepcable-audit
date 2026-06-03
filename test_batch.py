#!/usr/bin/env python3
"""批量测试电缆型号标准化"""

from deepcable_normalize import normalize, normalize_with_log
import time

# 真实场景测试清单
test_cases = [
    # 电力电缆
    "YJV22-8.7/15kV-3*240",
    "YJV22-8.7/15KV-3×240mm²",
    "yjv22-8.7/15kv-3x240",
    "YJV-0.6/1kV-4*185+1*95",
    "YJV-0.6/1KV-4×185+1×95mm²",
    "YJV22-10kV-3*300",
    "YJV22-10KV-3×300",
    "VV-1kV-3*50+2*25",
    "VV-0.6/1KV-3×50+2×25mm²",
    
    # 控制电缆
    "KVV-450/750V-10*1.5",
    "KVV-450/750v-10×1.5mm²",
    "KVVP-500V-12*2.5",
    "KVVP-500v-12×2.5",
    "KVV22-450/750V-20*1.0",
    
    # 计算机电缆
    "DJYPVP-300/500V-2*2*1.5",
    "DJYPVP-300/500v-2×2×1.5mm²",
    "DJYVPVR-250V-4*2*0.75",
    
    # 耐火/阻燃电缆
    "NH-YJV-0.6/1kV-3*120+2*70",
    "NH-YJV-0.6/1KV-3×120+2×70",
    "ZR-YJV22-8.7/15kV-3*95",
    "ZR-YJV22-8.7/15KV-3×95mm²",
    "WDZ-YJY-0.6/1kV-4*25",
    "WDZN-YJY-0.6/1kV-5*16",
    
    # 架空绝缘电缆
    "JKLYJ-10kV-1*150",
    "JKLYJ-10KV-1×150mm²",
    "JKLGYJ-10kV-1*120/20",
    
    # 矿物绝缘电缆
    "YTTW-750V-3*50+2*25",
    "BTLY-0.6/1kV-4*185",
    
    # 带铠装电缆
    "YJV32-8.7/15kV-3*240",
    "YJV42-10kV-3*300",
    "YJV62-35kV-1*400",
    
    # 特殊规格
    "YJV-8.7/10kV-3*400+2*200",
    "YJV22-26/35kV-1*630",
    "YJV22-64/110kV-1*800",
    
    # 各种格式变体
    "y j v 22 - 8.7/15 kv - 3 * 240",
    "YJV22  8.7/15KV  3×240",
    "YJV22_8.7/15kV_3*240",
    "YJV22—8.7/15kV—3×240",
    "YJV22～8.7/15kV～3*240",
    
    # 带空格和特殊字符
    " YJV22-8.7/15kV-3*240 ",
    "YJV22 - 8.7/15kV - 3*240",
    "YJV22- 8.7/15kV -3*240",
    
    # 小截面电缆
    "BV-450/750V-1*1.5",
    "BV-450/750V-1*2.5",
    "BVR-450/750V-1*6",
    
    # 多芯电缆
    "RVV-300/500V-3*0.75",
    "RVV-300/500V-4*1.0",
    "RVVP-300/500V-6*0.5",
    
    # 屏蔽电缆
    "ZR-RVVP-300/500V-2*1.5",
    "NH-RVVP-450/750V-4*2.5",
]

print("=" * 60)
print("电缆型号批量标准化测试")
print("=" * 60)

start_time = time.time()
success_count = 0
error_count = 0
results = []

for i, model in enumerate(test_cases, 1):
    try:
        result, changes = normalize_with_log(model)
        status = "✓" if result is not None else "!"
        results.append((model, result, changes, status))
        if result is not None:
            success_count += 1
        else:
            error_count += 1
    except Exception as e:
        results.append((model, None, [str(e)], "✗"))
        error_count += 1

end_time = time.time()

# 打印结果
print(f"\n总测试数：{len(test_cases)}")
print(f"成功标准化：{success_count}")
print(f"未标准化/错误：{error_count}")
print(f"成功率：{success_count/len(test_cases)*100:.1f}%")
print(f"总耗时：{(end_time-start_time)*1000:.2f}ms")
print(f"平均耗时：{(end_time-start_time)/len(test_cases)*1000:.2f}ms/个\n")

print("-" * 60)
print("详细结果:")
print("-" * 60)

for model, result, changes, status in results:
    print(f"\n{status} 输入：{model}")
    if status == "✗":
        print(f"  错误：{changes[0] if changes else 'Unknown'}")
    elif result is not None:
        print(f"  输出：{result}")
        if result != model:
            print(f"  原始：{model}")
        if changes:
            print(f"  变更：{', '.join(changes)}")
    else:
        print(f"  状态：未标准化")

print("\n" + "=" * 60)
