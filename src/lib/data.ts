import type { AITool, TaskTemplate } from './types';

import modelData from './model-data.json';

// AI 工具原始指标数据。
// 指标数值由 scripts/refresh-model-data.mjs 自动写入 model-data.json（勿手工编辑）；
// 下方 DESCRIPTIONS 为人工撰写的模型简介，自动更新流程不会覆盖。
// 数据来源见 model-data.json 的 meta.sources，更新方式见 docs/DATA_REFRESH.md。
const DESCRIPTIONS: Record<string, string> = {
  'claude-opus-5':
    '综合智能指数排名第一，长上下文推理与知识深度领先，适合高难度复杂任务，但价格与速度是短板。',
  'gpt-5-6-sol':
    '编程与物理推理维度最强，LiveBench 编程分项领先，综合能力全面，成本处于中高区间。',
  'gemini-3-7-flash':
    '生成速度 371 tokens/s 断层领先，价格极低且科学推理最强，但长上下文推理明显偏弱。',
  'glm-5-3':
    '国产模型代表，Agent 工具调用（τ³-Banking）与抗幻觉率两项排名第一，成本控制优秀。',
  'deepseek-v4-pro':
    '开源权重模型，单任务成本 $0.25 全场最低，性价比突出，但知识可靠性与长上下文较弱。',
  'kimi-k3':
    '2.8T 开源权重模型，SciCode 编程分项第一，Agent 与知识维度均衡，但生成速度最慢。',
};

/** 指标数据最后一次刷新的日期（展示于工具详情页）。 */
export const DATA_UPDATED_AT: string = modelData.meta.generatedAt;

/** 指标数据来源列表。 */
export const DATA_SOURCES: string[] = modelData.meta.sources;

export const AI_TOOLS: AITool[] = modelData.models.map((m): AITool => {
  const ind = m.indicators as Record<string, number>;
  return {
    id: m.id,
    name: m.name,
    version: m.version,
    company: m.company,
    category: m.category as AITool['category'],
    description: DESCRIPTIONS[m.id] ?? '',
    indicators: ind,
    inputPrice: ind.inputPrice,
    outputPrice: ind.outputPrice,
    tokenForIndex: ind.tokenForIndex,
    costPerTask: ind.costPerTask,
    apiSpeed: ind.apiSpeed,
    dataSource: m.provenance.external?.liveBench
      ? 'Artificial Analysis / LiveBench / 官方定价'
      : 'Artificial Analysis / 官方定价',
    updatedAt: modelData.meta.generatedAt,
  };
});

// 任务模板（含 7 维需求向量 r_jk 与平均 token 量）
export const TASK_TEMPLATES: TaskTemplate[] = [
  {
    id: 'paper-writing',
    name: '论文写作',
    description: '撰写学术论文、润色与结构优化',
    icon: 'FileText',
    demands: { coding: 0.2, agent: 0.2, longContext: 0.6, knowledge: 0.85, reasoning: 0.8, cost: 0.4, speed: 0.3 },
    avgInputTokens: 8000,
    avgOutputTokens: 3000,
  },
  {
    id: 'literature-analysis',
    name: '文献分析',
    description: '文献综述、要点提取与对比分析',
    icon: 'BookOpen',
    demands: { coding: 0.2, agent: 0.3, longContext: 0.95, knowledge: 0.8, reasoning: 0.75, cost: 0.5, speed: 0.4 },
    avgInputTokens: 50000,
    avgOutputTokens: 4000,
  },
  {
    id: 'data-analysis',
    name: '数据分析',
    description: '数据清洗、统计分析与可视化',
    icon: 'BarChart3',
    demands: { coding: 0.7, agent: 0.5, longContext: 0.4, knowledge: 0.6, reasoning: 0.8, cost: 0.4, speed: 0.5 },
    avgInputTokens: 6000,
    avgOutputTokens: 2000,
  },
  {
    id: 'python-coding',
    name: 'Python 编程',
    description: '代码生成、调试与工程实现',
    icon: 'Code2',
    demands: { coding: 0.95, agent: 0.35, longContext: 0.4, knowledge: 0.65, reasoning: 0.9, cost: 0.2, speed: 0.5 },
    avgInputTokens: 4000,
    avgOutputTokens: 2000,
  },
  {
    id: 'ppt-making',
    name: 'PPT 制作',
    description: '演示文稿大纲、内容与排版辅助',
    icon: 'Presentation',
    demands: { coding: 0.3, agent: 0.4, longContext: 0.5, knowledge: 0.7, reasoning: 0.6, cost: 0.4, speed: 0.6 },
    avgInputTokens: 5000,
    avgOutputTokens: 3000,
  },
  {
    id: 'information-retrieval',
    name: '信息检索',
    description: '实时搜索、事实核查与资料整理',
    icon: 'Search',
    demands: { coding: 0.2, agent: 0.5, longContext: 0.5, knowledge: 0.9, reasoning: 0.6, cost: 0.5, speed: 0.8 },
    avgInputTokens: 3000,
    avgOutputTokens: 1500,
  },
  {
    id: 'agent-automation',
    name: 'Agent 自动化',
    description: '多步任务编排、工具调用与自动化流程',
    icon: 'Workflow',
    demands: { coding: 0.5, agent: 0.9, longContext: 0.55, knowledge: 0.8, reasoning: 0.6, cost: 0.45, speed: 0.7 },
    avgInputTokens: 10000,
    avgOutputTokens: 4000,
  },
  {
    id: 'deep-reasoning-code',
    name: '深度推理与代码工程',
    description: '复杂逻辑推理与大型代码工程',
    icon: 'BrainCircuit',
    demands: { coding: 0.95, agent: 0.35, longContext: 0.4, knowledge: 0.65, reasoning: 0.9, cost: 0.2, speed: 0.5 },
    avgInputTokens: 6000,
    avgOutputTokens: 2500,
  },
  {
    id: 'long-text-doc',
    name: '长文本检索与文档解析',
    description: '超长文档解析、检索与摘要',
    icon: 'FileSearch',
    demands: { coding: 0.25, agent: 0.5, longContext: 0.95, knowledge: 0.5, reasoning: 0.45, cost: 0.8, speed: 0.6 },
    avgInputTokens: 100000,
    avgOutputTokens: 3000,
  },
  {
    id: 'daily-qa',
    name: '日常问答',
    description: '日常对话、搜索替代与偶发写作',
    icon: 'MessageCircle',
    demands: { coding: 0.3, agent: 0.3, longContext: 0.3, knowledge: 0.6, reasoning: 0.4, cost: 0.9, speed: 0.7 },
    avgInputTokens: 1500,
    avgOutputTokens: 800,
  },
];