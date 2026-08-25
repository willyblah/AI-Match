import { AI_TOOLS } from './data';
import { INDICATORS } from './types';
import type { AITool, DimensionKey, TopsisProfile } from './types';
import { DIMENSION_KEYS } from './types';

// ========== 矩阵运算工具 ==========

// 幂法求矩阵最大特征值及对应特征向量
function powerIteration(matrix: number[][]): { lambda: number; vector: number[] } {
  const n = matrix.length;
  let v = new Array(n).fill(1 / n);
  const maxIter = 1000;
  const eps = 1e-10;

  for (let iter = 0; iter < maxIter; iter++) {
    const w = matrix.map((row) => row.reduce((sum, val, j) => sum + val * v[j], 0));
    const norm = Math.sqrt(w.reduce((s, x) => s + x * x, 0));
    const next = w.map((x) => x / norm);
    const diff = next.reduce((s, x, i) => s + Math.abs(x - v[i]), 0);
    v = next;
    if (diff < eps) break;
  }

  // Rayleigh 商近似最大特征值
  const mv = matrix.map((row) => row.reduce((sum, val, j) => sum + val * v[j], 0));
  const lambda = mv.reduce((s, x, i) => s + x * v[i], 0) / v.reduce((s, x) => s + x * x, 0);
  return { lambda, vector: v };
}

// ========== 熵权-TOPSIS 能力画像 ==========

interface TopsisResult {
  profiles: Map<string, TopsisProfile>;
  weights: Record<string, number>; // 指标熵权
}

let cachedTopsis: TopsisResult | null = null;

export function computeTopsis(): TopsisResult {
  if (cachedTopsis) return cachedTopsis;

  const tools = AI_TOOLS.filter((t) => t.category === 'llm');
  const m = tools.length;
  const n = INDICATORS.length;

  // 原始矩阵
  const raw: number[][] = tools.map((t: AITool) =>
    INDICATORS.map((ind: { key: string }) => t.indicators[ind.key] ?? 0)
  );

  // 一致化：极小型指标取倒数
  const consistent: number[][] = raw.map((row: number[]) =>
    row.map((val: number, j: number) => {
      if (INDICATORS[j].isCost) {
        return val === 0 ? 0 : 1 / val;
      }
      return val;
    })
  );

  // Z-score 标准化
  const mean = new Array(n).fill(0);
  const std = new Array(n).fill(0);
  for (let j = 0; j < n; j++) {
    const col = consistent.map((r: number[]) => r[j]);
    mean[j] = col.reduce((s: number, x: number) => s + x, 0) / m;
    const variance = col.reduce((s: number, x: number) => s + (x - mean[j]) ** 2, 0) / m;
    std[j] = Math.sqrt(variance) || 1e-10;
  }
  const X: number[][] = consistent.map((row: number[]) =>
    row.map((val: number, j: number) => (val - mean[j]) / std[j])
  );

  // 熵权法
  // 比重 p_ij（需平移为正）
  const shift: number[][] = X.map((row: number[]) => row.map((v: number) => v + 5)); // 平移使全为正
  const colSum = new Array(n).fill(0);
  for (let j = 0; j < n; j++) {
    colSum[j] = shift.reduce((s: number, row: number[]) => s + row[j], 0) || 1;
  }
  const P: number[][] = shift.map((row: number[]) =>
    row.map((v: number, j: number) => v / colSum[j])
  );

  const e = new Array(n).fill(0);
  for (let j = 0; j < n; j++) {
    let sum = 0;
    for (let i = 0; i < m; i++) {
      const p = P[i][j];
      sum += p > 0 ? p * Math.log(p) : 0;
    }
    e[j] = -sum / Math.log(m);
  }
  const d = e.map((ej: number) => 1 - ej);
  const dSum = d.reduce((s: number, x: number) => s + x, 0) || 1;
  const weights: Record<string, number> = {};
  for (let j = 0; j < n; j++) {
    weights[INDICATORS[j].key] = d[j] / dSum;
  }

  // 分维度 TOPSIS
  const profiles = new Map<string, TopsisProfile>();

  for (const dim of DIMENSION_KEYS) {
    const dimIndices = INDICATORS.map((ind: { dimension: DimensionKey }, idx: number) => ({ ind, idx })).filter(
      (x: { ind: { dimension: DimensionKey }; idx: number }) => x.ind.dimension === dim
    );
    if (dimIndices.length === 0) continue;

    const dimCols = dimIndices.map((x: { idx: number }) => x.idx);
    // 加权矩阵
    const V: number[][] = X.map((row: number[]) =>
      dimCols.map((j: number) => weights[INDICATORS[j].key] * row[j])
    );

    const vPlus = dimCols.map((_unused: number, j: number) => Math.max(...V.map((r: number[]) => r[j])));
    const vMinus = dimCols.map((_unused: number, j: number) => Math.min(...V.map((r: number[]) => r[j])));

    tools.forEach((tool, i) => {
      let dPlus = 0;
      let dMinus = 0;
      for (let j = 0; j < dimCols.length; j++) {
        dPlus += (V[i][j] - vPlus[j]) ** 2;
        dMinus += (V[i][j] - vMinus[j]) ** 2;
      }
      dPlus = Math.sqrt(dPlus);
      dMinus = Math.sqrt(dMinus);
      const c = dPlus + dMinus === 0 ? 0 : dMinus / (dPlus + dMinus);
      const existing = profiles.get(tool.id) || ({} as TopsisProfile);
      existing[dim] = Math.max(0, Math.min(1, c));
      profiles.set(tool.id, existing);
    });
  }

  // 图片/视频工具：专业能力维度用其 critpt 值，其余置 0
  for (const tool of AI_TOOLS.filter((t) => t.category !== 'llm')) {
    const profile: TopsisProfile = {
      coding: 0,
      agent: 0,
      longContext: 0,
      knowledge: 0,
      reasoning: tool.indicators.critpt ?? 0,
      cost: 0,
      speed: 0,
    };
    profiles.set(tool.id, profile);
  }

  cachedTopsis = { profiles, weights };
  return cachedTopsis;
}

export function getTopsisProfile(toolId: string): TopsisProfile {
  const { profiles } = computeTopsis();
  return profiles.get(toolId) || ({} as TopsisProfile);
}

export function getIndicatorWeights(): Record<string, number> {
  return computeTopsis().weights;
}

// ========== AHP 偏好权重 ==========

const RI_TABLE: Record<number, number> = {
  1: 0,
  2: 0,
  3: 0.58,
  4: 0.9,
  5: 1.12,
  6: 1.24,
  7: 1.32,
  8: 1.41,
  9: 1.45,
  10: 1.49,
};

export interface AhpResult {
  weights: Record<DimensionKey, number>;
  lambdaMax: number;
  ci: number;
  cr: number;
  consistent: boolean;
}

export function computeAhpWeights(judgmentMatrix: number[][]): AhpResult {
  const n = judgmentMatrix.length;
  const { lambda, vector } = powerIteration(judgmentMatrix);

  const sum = vector.reduce((s, x) => s + x, 0) || 1;
  const normalized = vector.map((x) => x / sum);

  const weights = {} as Record<DimensionKey, number>;
  DIMENSION_KEYS.forEach((k, i) => {
    weights[k] = normalized[i];
  });

  const ci = (lambda - n) / (n - 1);
  const ri = RI_TABLE[n] ?? 1.32;
  const cr = ri === 0 ? 0 : ci / ri;

  return {
    weights,
    lambdaMax: lambda,
    ci,
    cr,
    consistent: cr < 0.1,
  };
}

// ========== 综合匹配推荐 ==========

export interface MatchInput {
  tools: AITool[];
  weights: Record<DimensionKey, number>;
  demands: Record<DimensionKey, number>;
  budget: number;
  frequency: number; // 每月调用次数
  avgInputTokens: number;
  avgOutputTokens: number;
}

export interface MatchOutput {
  recommendations: import('./types').Recommendation[];
}

export function computeRecommendations(input: MatchInput): MatchOutput {
  const { tools, weights, demands, budget, frequency, avgInputTokens, avgOutputTokens } = input;
  const { profiles } = computeTopsis();

  const results = tools.map((tool) => {
    const topsis = profiles.get(tool.id) || ({} as TopsisProfile);

    // 效用函数 U_ij = Σ w_k × r_jk × c_ik
    let utility = 0;
    const contributions: { dimension: DimensionKey; contribution: number }[] = [];
    for (const k of DIMENSION_KEYS) {
      const w = weights[k] ?? 0;
      const r = demands[k] ?? 0;
      const c = topsis[k] ?? 0;
      const contrib = w * r * c;
      utility += contrib;
      contributions.push({ dimension: k, contribution: contrib });
    }

    // 成本计算 C_ij = Pin×Tin + Pout×Tout
    const cost =
      tool.category === 'llm'
        ? (tool.inputPrice * avgInputTokens + tool.outputPrice * avgOutputTokens) / 1_000_000
        : tool.costPerTask;
    const monthlyCost = cost * frequency;
    const affordable = monthlyCost <= budget;

    // 匹配度归一化（基于效用最大值）
    return { tool, topsis, utility, cost, monthlyCost, affordable, contributions };
  });

  // 归一化匹配度
  const maxUtility = Math.max(...results.map((r) => r.utility), 1e-10);
  const normalized = results.map((r) => ({
    ...r,
    matchScore: Math.round((r.utility / maxUtility) * 100),
  }));

  // 排序：可负担优先，再按匹配度
  normalized.sort((a, b) => {
    if (a.affordable !== b.affordable) return a.affordable ? -1 : 1;
    return b.matchScore - a.matchScore;
  });

  const recommendations = normalized.slice(0, 3).map((r) => {
    const advantages = generateAdvantages(r);
    const reason = generateReason(r, weights, demands);
    return {
      tool: r.tool,
      topsis: r.topsis,
      matchScore: r.matchScore,
      cost: r.cost,
      monthlyCost: r.monthlyCost,
      affordable: r.affordable,
      advantages,
      reason,
      dimensionContributions: r.contributions,
    };
  });

  return { recommendations };
}

function generateAdvantages(r: { tool: AITool; topsis: TopsisProfile; cost: number; affordable: boolean }) {
  const advantages: string[] = [];
  const t = r.topsis;
  if (t.coding >= 0.8) advantages.push('编程能力强');
  if (t.agent >= 0.7) advantages.push('Agent 能力突出');
  if (t.longContext >= 0.8) advantages.push('长上下文处理优秀');
  if (t.knowledge >= 0.7) advantages.push('知识推理准确');
  if (t.reasoning >= 0.8) advantages.push('专业推理领先');
  if (t.speed >= 0.8) advantages.push('生成速度快');
  if (r.cost <= 0.1) advantages.push('成本极低');
  else if (r.cost <= 0.5) advantages.push('性价比高');
  if (r.tool.category === 'image') advantages.push('图像生成专业');
  if (r.tool.category === 'video') advantages.push('视频生成专业');
  return advantages.slice(0, 4);
}

function generateReason(
  r: { tool: AITool; matchScore: number; contributions: { dimension: DimensionKey; contribution: number }[]; affordable: boolean; monthlyCost: number },
  _weights: Record<DimensionKey, number>,
  _demands: Record<DimensionKey, number>
) {
  const topDims = [...r.contributions]
    .sort((a, b) => b.contribution - a.contribution)
    .slice(0, 2)
    .map((c) => DIMENSION_LABELS[c.dimension]);

  const budgetNote = r.affordable
    ? `月度成本约 $${r.monthlyCost.toFixed(2)}，在您的预算范围内。`
    : `月度成本约 $${r.monthlyCost.toFixed(2)}，略高于当前预算，建议提高预算或降低调用频率。`;

  return `综合匹配度 ${r.matchScore}%。${r.tool.name} 在${topDims.join('、')}维度上与您的任务需求高度契合，${budgetNote}`;
}

const DIMENSION_LABELS: Record<DimensionKey, string> = {
  coding: '编程能力',
  agent: 'Agent 能力',
  longContext: '长上下文处理',
  knowledge: '知识准确性',
  reasoning: '专业推理',
  cost: '成本控制',
  speed: '生成速度',
};

// ========== 多任务组合推荐 ==========
// 对应论文第 4 章：为每个任务分别指派最合适的模型，而非全局只选一个模型。

export interface MultiTaskInput {
  tools: AITool[];
  weights: Record<DimensionKey, number>;
  tasks: import('./types').TaskTemplate[];
  budget: number;
  /** 每个任务每月的调用次数 f_j */
  frequencyPerTask: number;
}

export interface TaskResult {
  task: import('./types').TaskTemplate;
  recommendations: import('./types').Recommendation[];
}

export interface AssignmentEntry {
  task: import('./types').TaskTemplate;
  tool: AITool;
  matchScore: number;
  monthlyCost: number;
}

export interface MultiTaskOutput {
  taskResults: TaskResult[];
  /** 每个任务的最优指派（论文 x_ij） */
  assignment: AssignmentEntry[];
  totalMonthlyCost: number;
  withinBudget: boolean;
  /** 混合调用的总效用 Z */
  mixedUtility: number;
  /** 若全部任务都用同一个模型，最优的那个模型及其总效用 */
  bestSingle: { tool: AITool; utility: number; monthlyCost: number } | null;
  /** 混合调用相对单一模型的效用提升（百分比，可能为 0） */
  mixedGainPct: number;
}

/** 单个工具在单个任务下的原始效用 U_ij = Σ w_k · r_jk · c_ik */
function rawUtility(
  topsis: TopsisProfile,
  weights: Record<DimensionKey, number>,
  demands: Record<DimensionKey, number>
): number {
  return DIMENSION_KEYS.reduce(
    (sum, k) => sum + (weights[k] ?? 0) * (demands[k] ?? 0) * (topsis[k] ?? 0),
    0
  );
}

/** 单次调用成本 C_ij = Pin·Tin + Pout·Tout */
function callCost(tool: AITool, task: import('./types').TaskTemplate): number {
  return tool.category === 'llm'
    ? (tool.inputPrice * task.avgInputTokens + tool.outputPrice * task.avgOutputTokens) / 1_000_000
    : tool.costPerTask;
}

export function computeMultiTaskRecommendations(input: MultiTaskInput): MultiTaskOutput {
  const { tools, weights, tasks, budget, frequencyPerTask } = input;
  const { profiles } = computeTopsis();

  const taskResults: TaskResult[] = tasks.map((task) => ({
    task,
    recommendations: computeRecommendations({
      tools,
      weights,
      demands: task.demands,
      budget,
      frequency: frequencyPerTask,
      avgInputTokens: task.avgInputTokens,
      avgOutputTokens: task.avgOutputTokens,
    }).recommendations,
  }));

  // 每个任务取排序后的第一名作为指派结果
  const assignment: AssignmentEntry[] = taskResults
    .filter((r) => r.recommendations.length > 0)
    .map((r) => {
      const top = r.recommendations[0];
      return {
        task: r.task,
        tool: top.tool,
        matchScore: top.matchScore,
        monthlyCost: top.monthlyCost,
      };
    });

  const totalMonthlyCost = assignment.reduce((s, a) => s + a.monthlyCost, 0);

  // 混合调用总效用：各任务最优模型的原始效用之和
  const mixedUtility = assignment.reduce((s, a) => {
    const p = profiles.get(a.tool.id) || ({} as TopsisProfile);
    return s + rawUtility(p, weights, a.task.demands);
  }, 0);

  // 单一模型基线：所有任务都用同一个模型时，效用最高的那个。
  // 注意必须同样受预算约束——指派方案是「可负担优先」排序出来的，
  // 若基线不设预算限制，就等于拿一个买不起的方案去比，比较本身没有意义。
  const singles = tools.map((tool) => {
    const p = profiles.get(tool.id) || ({} as TopsisProfile);
    return {
      tool,
      utility: tasks.reduce((s, t) => s + rawUtility(p, weights, t.demands), 0),
      monthlyCost: tasks.reduce((s, t) => s + callCost(tool, t) * frequencyPerTask, 0),
    };
  });
  const affordableSingles = singles.filter((s) => s.monthlyCost <= budget);
  // 预算内无可用模型时退回全集，至少给出一个参照
  const singlePool = affordableSingles.length > 0 ? affordableSingles : singles;
  const bestSingle: MultiTaskOutput['bestSingle'] = singlePool.reduce<
    MultiTaskOutput['bestSingle']
  >((best, s) => (!best || s.utility > best.utility ? s : best), null);

  const mixedGainPct =
    bestSingle && bestSingle.utility > 0
      ? Math.max(0, ((mixedUtility - bestSingle.utility) / bestSingle.utility) * 100)
      : 0;

  return {
    taskResults,
    assignment,
    totalMonthlyCost,
    withinBudget: totalMonthlyCost <= budget,
    mixedUtility,
    bestSingle,
    mixedGainPct,
  };
}

// ========== 排行榜 ==========

export function computeRankings(): import('./types').RankEntry[] {
  const { profiles } = computeTopsis();
  return AI_TOOLS.map((tool) => {
    const topsis = profiles.get(tool.id) || ({} as TopsisProfile);
    const overallScore = DIMENSION_KEYS.reduce((s, k) => s + (topsis[k] ?? 0), 0) / DIMENSION_KEYS.length;
    return { tool, topsis, overallScore, costPerTask: tool.costPerTask };
  });
}

export function rankByDimension(dim: DimensionKey): import('./types').RankEntry[] {
  return computeRankings()
    .sort((a, b) => (b.topsis[dim] ?? 0) - (a.topsis[dim] ?? 0));
}

export function rankByCostPerformance(): import('./types').RankEntry[] {
  return computeRankings().sort((a, b) => {
    const aScore = a.overallScore / (a.costPerTask || 0.01);
    const bScore = b.overallScore / (b.costPerTask || 0.01);
    return bScore - aScore;
  });
}