# PPS vs Y 转换规则验证 Spec

## Why
需要验证用户给出的 PPS 到 Y 的转换规则是否正确，并用多个测试用例验证。

## What Changes
- 验证基础规则：`pps_to_y(0) = y(1)`
- 验证后继规则：`pps_to_y(A, 0) = y(pps_to_y(A), 1)`
- 验证极限规则：`pps_to_y(A) = y(B)`，满足 `pps(A[n]) < pps(y_to_pps(B[m])) < pps(A[n+1])`
- 用多个测试用例验证规则的正确性

## Impact
- 影响的文档：MEMORY.md、ANALYSIS_TABLE.md
- 分析进度：小计划3（共8个小计划）

## ADDED Requirements
### Requirement: 转换规则基础验证
系统应验证 `pps_to_y(0) = y(1)` 对所有基础序列成立。

#### Scenario: 基础规则验证
- **WHEN** 验证基础规则
- **THEN** `0` → `1` 映射成立

### Requirement: 转换规则后继验证
系统应验证后继规则对所有后继序列成立。

#### Scenario: 后继规则验证
- **WHEN** 验证后继规则 `pps_to_y(A, 0) = y(pps_to_y(A), 1)`
- **THEN** 每一步后继展开都符合规则

### Requirement: 转换规则极限验证
系统应验证极限规则对所有极限类型序列成立。

#### Scenario: 极限规则验证
- **WHEN** 验证极限规则
- **THEN** 极限展开满足区间关系

## MODIFIED Requirements
无

## REMOVED Requirements
无