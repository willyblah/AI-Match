// AI Match 核心类型定义

// 七个一级能力维度
export type DimensionKey =
  | 'coding'
  | 'agent'
  | 'longContext'
  | 'knowledge'
  | 'reasoning'
  | 'cost'
  | 'speed';

export const DIMENSIONS: { key: DimensionKey; label: string; shortLabel: string }[] = [
  { key: 'coding', label: '编程能力', shortLabel: '编程' },
  { key: 'agent', label: 'Agent 智能体能力', shortLabel: 'Agent' },
  { key: 'longContext', label: '长上下文处理', shortLabel: '长文本' },
  { key: 'knowledge', label: '知识与事实准确性', shortLabel: '知识' },
  { key: 'reasoning', label: '专业推理能力', shortLabel: '推理' },
  { key: 'cost', label: '成本价格', shortLabel: '成本' },
  { key: 'speed', label: '生成速度', shortLabel: '速度' },
];

export const DIMENSION_KEYS: DimensionKey[] = [
  'coding',
  'agent',
  'longContext',
  'knowledge',
  'reasoning',
  'cost',
  'speed',
];

// 二级 Benchmark 指标
export interface Indicator {
  key: string;
  label: string;
  dimension: DimensionKey;
  isCost: boolean; // 极小型指标（越小越优）
}

export const INDICATORS: Indicator[] = [
  { key: 'terminalBench', label: 'Terminal-Bench', dimension: 'coding', isCost: false },
  { key: 'sciCode', label: 'SciCode', dimension: 'coding', isCost: false },
  { key: 'liveBench', label: 'LiveBench', dimension: 'coding', isCost: false },
  { key: 'gdpvalAA', label: 'GDPval-AA v2', dimension: 'agent', isCost: false },
  { key: 'tau3Banking', label: 'τ3-Banking', dimension: 'agent', isCost: false },
  { key: 'aaLCR', label: 'AA-LCR', dimension: 'longContext', isCost: false },
  { key: 'omniAccuracy', label: 'AA-Omni Accuracy', dimension: 'knowledge', isCost: false },
  { key: 'omniNonHall', label: 'AA-Omni Non-Hall.', dimension: 'knowledge', isCost: false },
  { key: 'humanLastExam', label: "Humanity's Last Exam", dimension: 'knowledge', isCost: false },
  { key: 'gpqaDiamond', label: 'GPQA Diamond', dimension: 'reasoning', isCost: false },
  { key: 'critpt', label: 'Critpt', dimension: 'reasoning', isCost: false },
  { key: 'inputPrice', label: '输入价格 ($/1M)', dimension: 'cost', isCost: true },
  { key: 'outputPrice', label: '输出价格 ($/1M)', dimension: 'cost', isCost: true },
  { key: 'tokenForIndex', label: '完成 Index 所需 token 量 (M)', dimension: 'cost', isCost: true },
  { key: 'costPerTask', label: '单任务平均成本 ($)', dimension: 'cost', isCost: true },
  { key: 'apiSpeed', label: 'API 生成速度 (tokens/s)', dimension: 'speed', isCost: false },
];

// AI 工具类型
export type ToolCategory = 'llm' | 'image' | 'video';

// AI 工具数据
export interface AITool {
  id: string;
  name: string;
  version: string;
  company: string;
  category: ToolCategory;
  description: string;
  // 16 项原始指标
  indicators: Record<string, number>;
  // 输入/输出价格与 token 量（用于成本计算）
  inputPrice: number;
  outputPrice: number;
  tokenForIndex: number;
  costPerTask: number;
  apiSpeed: number;
  dataSource: string;
  updatedAt: string;
}

// TOPSIS 能力画像（7 维贴近度）
export type TopsisProfile = Record<DimensionKey, number>;

// 任务模板
export interface TaskTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  // 7 维需求向量 r_jk
  demands: Record<DimensionKey, number>;
  // 平均输入/输出 token 量（用于成本计算）
  avgInputTokens: number;
  avgOutputTokens: number;
}

// 用户偏好画像
export interface UserProfile {
  scenario: string;
  mainTask: string;
  budget: number;
  frequency: string;
  // 7 维偏好权重（用户拖动滑块设定后归一化，总和为 1）
  weights: Record<DimensionKey, number>;
  description: string;
}

// 推荐结果
export interface Recommendation {
  tool: AITool;
  topsis: TopsisProfile;
  matchScore: number; // 0-100
  cost: number; // 单次调用成本
  monthlyCost: number; // 月度成本
  affordable: boolean;
  advantages: string[];
  reason: string;
  dimensionContributions: { dimension: DimensionKey; contribution: number }[];
}

// 排行榜条目
export interface RankEntry {
  tool: AITool;
  topsis: TopsisProfile;
  overallScore: number;
  costPerTask: number;
}