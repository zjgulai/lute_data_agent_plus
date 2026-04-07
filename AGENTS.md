# AGENTS.md - GMV智能归因系统项目

## 会话管理约定

### 日志保存规则
当本会话的上下文内容接近或超过系统容量限制（context compaction触发前），应将本次会话的关键决策、修正点和当前文档状态保存到项目目录的 `logs/` 文件夹下。

- **保存路径**：`/Users/pray/project/data_agent_plus/logs/progress_YYYY-MM-DD.md`
- **保存方式**：若当日文件已存在，则**增量追加**到文件末尾；若不存在则新建
- **保存内容**：应包含关键决策时间线、PRD修正点、用户明确的拍板结论、当前开发状态
- **触发提醒**：当检测到对话长度显著增长或系统提示context压力时，主动执行保存

---

## 项目核心上下文

### 当前阶段
Phase 1-5 基本完成。数据库持久化、部署文档、健康检查、日志、Error Boundary 均已补齐。仅剩 Docker 本地镜像存储层待修复后做最终容器验证。

### 开发进度
- **Task 1**: 指标树配置系统 ✅ 100% 完成
- **Task 2**: Excel 数据读取与切片服务 ✅ 100% 完成  
- **Task 3**: 算法引擎（熵减 + 贡献度 + 交叉维度）✅ 100% 完成
- **Task 4**: 状态机 + LLM Orchestrator ✅ 100% 完成
- **Task 5**: 前端三栏式布局 + 交叉维度展示 + 节点Tooltip + 时间轴-树联动 ✅ 100% 完成
- **Task 6**: 权限自适应 ✅ 100% 完成
- **Task 7**: D3.js 动态时间轴 ✅ 100% 完成
- **Task 8**: 结构化结论输入与保存 ✅ 100% 完成
- **Task 9**: 报告导出（Word / PDF）✅ 100% 完成
- **Task 11**: 外部文件上传与解析 ✅ 100% 完成

### 关键设计决策（已冻结）
1. **数据源**：BI只读副本为主，Excel仅用于离线测试
2. **算法**：归因决策树基于维度贡献集中度（熵减）
3. **LLM模式**：自动模式（3-5秒）+ 手动模式（每步解释）
4. **MVP边界**：砍掉RAG和审批流，结构化结论直接落库
5. **组织树**：预定义层级，不走熵减；经营节点配置`dimension_pool`
6. **下钻规则**：单路径下钻，遇相近份额按历史案例偏好选择
7. **交叉维度**：必须有，异步队列执行，单节点上限5个，超时3秒

### 关键文件
- **PRD**：`/Users/pray/project/data_agent_plus/docs/PRD.md`
- **开发计划**：`/Users/pray/.kimi/plans/sentry-hulkling-groot.md`
- **项目状态**：`/Users/pray/project/data_agent_plus/docs/PROJECT_STATUS.md`
- **进度日志**：`/Users/pray/project/data_agent_plus/logs/progress_2026-04-04.md`
- **后端权限**：`/Users/pray/project/data_agent_plus/backend/src/auth/`
- **前端归因链**：`/Users/pray/project/data_agent_plus/frontend/src/components/chain/AttributionChain.tsx`
- **前端 D3 时间轴**：`/Users/pray/project/data_agent_plus/frontend/src/components/timeline-d3/GMVTimeline.tsx`

### 快速启动
```bash
# 后端
cd /Users/pray/project/data_agent_plus/backend
PYTHONPATH=src python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 前端
cd /Users/pray/project/data_agent_plus/frontend
npm run dev

# 测试
cd /Users/pray/project/data_agent_plus/backend
PYTHONPATH=src python3 -m pytest tests/test_algorithm.py -v
```

---

## 代码规范

### Python 后端
- 使用类型注解
- 函数文档字符串使用 Google Style
- 异常类继承自自定义基类
- 测试覆盖率目标 80%+

### TypeScript 前端
- 严格模式开启
- 组件使用函数式 + Hooks
- 类型定义在 `types/index.ts`

---

*最后更新: 2026-04-04*
