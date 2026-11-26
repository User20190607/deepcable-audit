# V30 历史真实数据回放与 Beta2 缺陷审计报告

**工作包：** V30 Historical Replay Workbench  
**审计基线：** V30.0-beta2 / `V30-RULESET-2026-11-24.2`  
**回放日期：** 2026-11-25  
**结论：** beta2 可运行，但当前不具备生产发布可信度；不得用于无人工复核的正式采购发布。

## 1. 执行摘要

本轮从用户资料库取回并实际解压了 `V30_beta2_python_source.zip` 与 `V30_beta2_complete.zip`，以 beta2 源码为测试对象，而不是将 alpha1 当作当前基线。

- 原有 beta2 单元测试：`33 passed`。
- Rulebook 结构验证：`RULEBOOK PASS`，但6项标准登记的来源文本/现行状态未被程序独立核验。
- Runtime 冒烟测试：SQLite 持久化、Risk Router、旧版 `cable_lint.py` 路径均被执行；一条正常样例返回 `RELEASED`，旧版 lint 返回 PASS。
- 对抗探针：7项，其中5项发现缺陷/覆盖缺口，2项作为正向控制。
- 9月真实文本批次：53行；47行单位“米”，6行单位“百米”；44行 PASS、9行 HOLD；整批 HELD。
- 10月真实文本批次：67行；59行单位“米”、3行单位“m”、5行单位“卷”；64行 PASS、2行 WARN、1行 HOLD；整批 HELD。

注意：历史回放只覆盖本报告明确列出的两个可从文本中确定解析的批次，不代表两个月全部消息、图片和清单都已完整回放。

## 2. 来源数据盘点

### 9月

来源：`raw_sources/2026-09_chat_export_latest.json`；对话标题：`09月电线电缆清单标准化`。采用较新的导出快照：793条消息（385条用户消息、408条助手消息）。其中80条用户消息包含附件引用，共100个附件引用。图片原始字节未包含在该导出中，故图像型清单暂未进入自动回放。

提取结果：
- `datasets/september_messages.jsonl`：完整消息序列与附件元数据。
- `datasets/replay_candidates.jsonl`：包含型号/数量信号的候选记录。
- `datasets/historical_tsv_outputs_unadjudicated.jsonl`：历史助手TSV输出，全部标记为未裁定，不作为金标准。

### 10月

来源：`raw_sources/2026-10_chat_export.txt`，92,365字符；拆分为121个角色区块（54个用户区块、67个助手区块）。

提取结果：
- `datasets/october_messages.jsonl`
- `datasets/replay_candidates.jsonl`
- `datasets/historical_tsv_outputs_unadjudicated.jsonl`

合计提取220条回放候选记录和53个历史TSV块。历史助手输出必须与用户后续确认/纠错链配对后才能成为金标准。

## 3. Beta2 自动化测试与 Runtime 执行

### 3.1 原测试

命令：`python -m pytest -q`  
结果：`33 passed in 0.13s`。

### 3.2 Rulebook

命令：`python validate_rulebook.py v30core/rules/rulebook.json`  
结果：`RULEBOOK PASS`。验证器明确警告：GB/T 12706.1-2020、GB/T 9330-2020、GB/T 5023.3-2008、GB/T 19666-2019、GB 31247-2014、GB 50217-2018 的 `STANDARD_VERIFIED` 只是源文件声明；程序只检查声明结构，不代表已核验官方原文或现行版本。

### 3.3 Runtime 冒烟

通过 `V30Runtime` 执行一条正常 WDZB-YJY 记录，使用临时 SQLite 数据库。结果：`RELEASED`；旧版 `cable_lint.py` return code 0，输出 `rows=1 errors=0 warns=0`。这证明主 Runtime 路径可启动，不证明门禁足以发现所有业务错误。

## 4. 对抗探针结果

详细机器结果见 `beta2_adversarial_audit.json`。

| ID | 探针 | 实际观察 | 结论 |
|---|---|---|---|
| B2-ADV-001 | 无连字符前缀 | `WDZBNYJV`、`ZCYJV` 的 prefix 均为 None | 前缀识别缺口；未知 token 会HOLD，但不能准确触发前缀规则 |
| B2-ADV-002 | Patch 重验 | `patch_engine` 只返回 dirty_checks，行仍保留旧AST/PASS/findings | P0：没有执行局部重验，缺少失效状态 |
| B2-ADV-003 | 数量独立守恒 | 将5扎错误配置为10m/扎，结果50m仍 RELEASED | P0：门禁比较处理行与聚合行，未独立重算原始单位转换 |
| B2-ADV-004 | 缺失电压 | `YJV 3×50` 自动补成0.6/1kV并PASS | P0：规则库profile未阻断旧fallback；缺失证据被当作低压依据 |
| B2-ADV-005 | WD/PVC冲突 | `WDZ-YJV` 被规则库规范化为`WDZ-YJY`并留痕 | 正向控制：beta2相对alpha1已有真实改进 |
| B2-ADV-006 | 小数米 | `50.5m` 在单位为m时被门禁阻断 | 正向控制：门禁对规范单位m有效 |
| B2-ADV-007 | 连写前缀最终状态 | 当前样例进入HOLD/未知token路径，而非PASS | 缺口仍在，但不应夸大为已证明直接PASS绕过 |

## 5. 9月真实批次回放

来源消息时间：2026-09-02；原始消息ID与完整输入保存在 `replays/september_2026_09_02_beta2_replay.json`。

- 解析输入：53行。
- 单位：47行“米”、6行“百米”。
- 状态：44 PASS、9 HOLD。
- HOLD原因：9行 `UNKNOWN_PRODUCT`，主要集中在 `WDZB-YJLHY` 型号族。
- Release Gate：HELD。

### 关键发现：百米未换算

6行“百米”在 beta2 中仍保留原单位及原数量，例如：
- `WDZCN-BYJ-1×2.5`：661百米仍输出661百米；
- `WDZCN-RYJS-2×2.5`：380百米仍输出380百米；
- `WDZC-BYJ-1×2.5`：365百米仍输出365百米。

当前引擎只对“扎/捆”及提供 `pack_length_m` 的“卷/圈”执行换算，没有把“百米”转换成米，也没有对“米”做单位别名归一。

## 6. 10月真实批次回放

来源：10月TXT中首个完整制表符清单，原文及输出保存在 `replays/october_first_tabular_beta2_replay.json`。

- 解析输入：67行。
- 单位：59行“米”、3行“m”、5行“卷”。
- 状态：64 PASS、2 WARN、1 HOLD。
- Release Gate：HELD。

### 关键发现A：米单位别名绕过整米门禁

以下行单位为“米”，数量为小数，仍未触发 `unit == "m"` 的整米门禁：
- 45.6米：行状态PASS；
- 52.8米：行状态PASS；
- 27.6米：行状态WARN；
- 68.5米：因 `×2组` 未被完整语法识别而HOLD。

整批HELD是因为另一行未知token，不能把这误认为小数米门禁有效。

### 关键发现B：卷装缺少默认包装长度

5行BVR/BVV卷装记录没有携带 `pack_length_m`：BVR 1.5 22卷、BVR 2.5 33卷、BVR 4 22卷、BVR 6 33卷、BVV 10 2卷。它们均保留“卷”作为单位并通过行级状态检查。beta2虽对“扎”默认100m换算，但“卷”只有显式提供 `pack_length_m` 才换算，没有应用已确认的BVR默认100m/卷规则。

### 关键发现C：结构/主辅芯审查

`YJV 4×25+1×10` 与 `YJV 3×35+2×26` 被标记 `AUX_SECTION_NOT_ALLOWED`（WARN），需要业务规则进一步判断：应区分真正非标、历史设计笔误、用户后续确认更正，不能把WARN直接视为正确的工程结论。

## 7. 本轮已确认的缺陷优先级

### P0：阻止正式发布

1. 数量转换没有独立原始账本重算；错误换算系数可通过门禁。
2. Patch仅声明脏检查列表，没有实际重验执行器；数据可能处于新型号+旧AST+旧PASS状态。
3. 电压缺失时仍存在YJV默认0.6/1kV路径；没有足够证据时会PASS。
4. 单位别名“米”绕过整米检查；“百米”没有换算。
5. 卷装没有完整默认包装规则，导致卷数作为采购单位直接输出。

### P1：必须修复或明确HOLD

1. 无连字符前缀无法准确解析。
2. `×2组` 等数量/结构复合表达无法完整识别。
3. YJLHY产品族未纳入解析/映射字典，真实历史行被HOLD。
4. 历史来源和后续用户纠错尚未全部配对，不能据此计算完整历史准确率。

## 8. 当前限制与数据边界

- 9月导出中100个附件引用只有元数据，没有图片字节；图片清单未实跑。
- 9月选取的53行是一个可读文本批次，不代表全月完整回放。
- 10月首个完整表格是一个可读文本批次，不代表全月全部批次。
- 历史助手TSV输出尚未逐一与用户后续纠错、撤销、确认配对，不作为金标准。
- 当前只审计并回放beta2；alpha1探针结果不混入beta2缺陷统计。

## 9. 下一步工程顺序

1. 建立 Unit Registry：统一“米/m/百米/扎/捆/卷/圈”等单位语义和转换依据；转换系数必须进入原始数量账本。
2. 建立 Quantity Ledger：保存 raw quantity/unit、pack factor、demand、purchase、loss、rounding、authorization、final quantity；Release Gate 独立重算。
3. 建立 Patch Transaction Executor：Patch提交后重新解析AST、运行受影响规则、重算聚合并执行门禁；失败原子回滚，未验证状态不能保留PASS。
4. 删除无证据的低压默认推断；缺电压且上下文不能排除中压时HOLD。
5. 重构型号解析器，支持前缀无连字符的可识别形式，但无法唯一解析时HOLD。
6. 将本报告每个真实缺陷固化为永久回归测试，再扩大到全部9月、10月文本与图片批次。

**发布判断：V30.0-beta2 = 可运行原型 / 历史回放未通过 / 不可生产发布。**