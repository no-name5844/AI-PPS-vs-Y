# PPS vs BOCF 分析计划

## 背景
- 项目路径：`g:\4\ord\study\AI && PPS vs BOCF`
- 当前状态：已测试 PPS 和 Y 展开器，MEMORY.md 和 ANALYSIS_TABLE.md 已有记录
- 存在问题：文档标题为 "PPS vs BOCF"，但现有分析主要是 PPS vs Y

---

## 任务 1：理解 BOCF 记号系统

### 步骤
1. 搜索 `programs/` 目录，检查是否有 `bocf` 相关的执行器
2. 搜索项目中是否有 BOCF 相关的文档或说明
3. 如果找到 BOCF 执行器，测试并记录其行为
4. 如果未找到，调查 BOCF 是什么（可能需要网络搜索）

---

## 任务 2：系统对比 PPS vs BOCF

### 步骤（如果 BOCF 存在）
1. 获取 BOCF 的数学定义
2. 使用相同测试用例对比 PPS 和 BOCF 的展开结果
3. 分析两者的异同点
4. 更新 ANALYSIS_TABLE.md 添加 BOCF 相关记录

---

## 任务 3：更新文档记录

### 步骤
1. 将 BOCF 研究结果追加到 MEMORY.md
2. 在 ANALYSIS_TABLE.md 中添加 BOCF 定义和测试结果
3. 在 README.md 底部追加新的分析记号
4. 清理或标注 DAILY_LOG.md（如果不需要）

---

## 待确认
- BOCF 是否有对应的展开器程序？
- BOCF 的数学规则是什么？
