import type { DimensionKey } from './types';
import { DIMENSION_KEYS } from './types';

// 问卷题目定义
export interface QuestionOption {
  label: string;
  value: string;
  // 该选项对各维度的偏好强度（用于构建判断矩阵）
  preferences: Partial<Record<DimensionKey, number>>;
}

export interface SurveyQuestion {
  id: string;
  title: string;
  subtitle: string;
  type: 'single' | 'multi';
  options: QuestionOption[];
}

export const SURVEY_QUESTIONS: SurveyQuestion[] = [
  {
    id: 'scenario',
    title: '您的主要使用场景是？',
    subtitle: '这决定了我们对各能力维度的初始权重倾向',
    type: 'single',
    options: [
      {
        label: '日常问答与搜索替代',
        value: 'light',
        preferences: { knowledge: 3, speed: 3, cost: 5, coding: 1, reasoning: 1 },
      },
      {
        label: '办公写作与文档处理',
        value: 'office',
        preferences: { knowledge: 4, reasoning: 3, longContext: 3, cost: 3, speed: 2 },
      },
      {
        label: '软件开发与编程',
        value: 'dev',
        preferences: { coding: 5, agent: 3, reasoning: 3, speed: 2, cost: 2 },
      },
      {
        label: '学术研究与文献分析',
        value: 'research',
        preferences: { reasoning: 5, knowledge: 4, longContext: 4, cost: 1 },
      },
      {
        label: '企业团队与自动化',
        value: 'enterprise',
        preferences: { agent: 5, longContext: 4, knowledge: 3, cost: 2 },
      },
      {
        label: 'AI 创业与大规模调用',
        value: 'startup',
        preferences: { agent: 5, speed: 4, coding: 3, cost: 2 },
      },
    ],
  },
  {
    id: 'mainTask',
    title: '您最常处理哪类任务？',
    subtitle: '可多选，系统将综合计算任务需求向量',
    type: 'multi',
    options: [
      { label: '编程与代码', value: 'coding', preferences: { coding: 5, reasoning: 3 } },
      { label: 'Agent 自动化', value: 'agent', preferences: { agent: 5, coding: 2 } },
      { label: '长文本处理', value: 'longContext', preferences: { longContext: 5 } },
      { label: '推理与分析', value: 'reasoning', preferences: { reasoning: 5, knowledge: 3 } },
      { label: '图片生成', value: 'image', preferences: { speed: 3, cost: 3 } },
      { label: '视频生成', value: 'video', preferences: { speed: 3, cost: 3 } },
    ],
  },
  {
    id: 'budget',
    title: '您的月度预算大概是？',
    subtitle: '预算将作为硬约束参与推荐优化',
    type: 'single',
    options: [
      { label: '免费 / $0', value: '0', preferences: { cost: 9 } },
      { label: '$1 - $30', value: '30', preferences: { cost: 5 } },
      { label: '$31 - $200', value: '200', preferences: { cost: 3 } },
      { label: '$201 - $2000', value: '2000', preferences: { cost: 2 } },
      { label: '$2000 以上', value: '10000', preferences: { cost: 1 } },
    ],
  },
  {
    id: 'frequency',
    title: '您的使用频率如何？',
    subtitle: '影响月度成本估算与速度权重',
    type: 'single',
    options: [
      { label: '偶尔使用（每月几次）', value: '10', preferences: { speed: 2 } },
      { label: '每天使用（每月几十次）', value: '100', preferences: { speed: 3 } },
      { label: '高频调用（每月数百次）', value: '500', preferences: { speed: 5, cost: 3 } },
      { label: '大规模自动化（每月数千次）', value: '5000', preferences: { speed: 5, cost: 4 } },
    ],
  },
  {
    id: 'priority1',
    title: '在能力上，您最看重哪一个？',
    subtitle: '请选择最重要的能力维度',
    type: 'single',
    options: [
      { label: '准确性（知识与事实）', value: 'knowledge', preferences: { knowledge: 7 } },
      { label: '推理能力', value: 'reasoning', preferences: { reasoning: 7 } },
      { label: '代码能力', value: 'coding', preferences: { coding: 7 } },
      { label: '长文本处理', value: 'longContext', preferences: { longContext: 7 } },
      { label: '生成速度', value: 'speed', preferences: { speed: 7 } },
      { label: '价格成本', value: 'cost', preferences: { cost: 7 } },
    ],
  },
  {
    id: 'priority2',
    title: '其次，您更看重哪一个？',
    subtitle: '作为第二优先级的能力维度',
    type: 'single',
    options: [
      { label: '准确性（知识与事实）', value: 'knowledge', preferences: { knowledge: 5 } },
      { label: '推理能力', value: 'reasoning', preferences: { reasoning: 5 } },
      { label: '代码能力', value: 'coding', preferences: { coding: 5 } },
      { label: '长文本处理', value: 'longContext', preferences: { longContext: 5 } },
      { label: '生成速度', value: 'speed', preferences: { speed: 5 } },
      { label: '价格成本', value: 'cost', preferences: { cost: 5 } },
    ],
  },
  {
    id: 'priority3',
    title: '第三，您更看重哪一个？',
    subtitle: '作为第三优先级的能力维度',
    type: 'single',
    options: [
      { label: '准确性（知识与事实）', value: 'knowledge', preferences: { knowledge: 3 } },
      { label: '推理能力', value: 'reasoning', preferences: { reasoning: 3 } },
      { label: '代码能力', value: 'coding', preferences: { coding: 3 } },
      { label: '长文本处理', value: 'longContext', preferences: { longContext: 3 } },
      { label: '生成速度', value: 'speed', preferences: { speed: 3 } },
      { label: '价格成本', value: 'cost', preferences: { cost: 3 } },
    ],
  },
];

// 将问卷答案转换为各维度的偏好强度分数
export function buildPreferenceScores(answers: Record<string, string | string[]>): Record<DimensionKey, number> {
  const scores: Record<DimensionKey, number> = {
    coding: 1,
    agent: 1,
    longContext: 1,
    knowledge: 1,
    reasoning: 1,
    cost: 1,
    speed: 1,
  };

  for (const q of SURVEY_QUESTIONS) {
    const ans = answers[q.id];
    if (!ans) continue;
    const selected = Array.isArray(ans) ? ans : [ans];
    for (const val of selected) {
      const opt = q.options.find((o) => o.value === val);
      if (!opt) continue;
      for (const k of DIMENSION_KEYS) {
        const p = opt.preferences[k];
        if (p) scores[k] += p;
      }
    }
  }

  return scores;
}

// 由偏好强度分数构建 AHP 判断矩阵（1-9 标度）
export function buildJudgmentMatrix(scores: Record<DimensionKey, number>): number[][] {
  const n = DIMENSION_KEYS.length;
  const matrix: number[][] = Array.from({ length: n }, () => new Array(n).fill(1));

  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      if (i === j) {
        matrix[i][j] = 1;
      } else {
        const ratio = scores[DIMENSION_KEYS[i]] / (scores[DIMENSION_KEYS[j]] || 1);
        // 映射到 1-9 标度
        let val: number;
        if (ratio >= 8) val = 9;
        else if (ratio >= 4) val = 7;
        else if (ratio >= 2.5) val = 5;
        else if (ratio >= 1.5) val = 3;
        else if (ratio > 1 / 1.5) val = 2;
        else if (ratio > 1 / 2.5) val = 1 / 2;
        else if (ratio > 1 / 4) val = 1 / 3;
        else if (ratio > 1 / 8) val = 1 / 5;
        else if (ratio > 1 / 16) val = 1 / 7;
        else val = 1 / 9;
        matrix[i][j] = val;
      }
    }
  }
  return matrix;
}

// 生成偏好画像描述
export function generateProfileDescription(weights: Record<DimensionKey, number>): string {
  const entries = DIMENSION_KEYS.map((k) => ({ key: k, w: weights[k] }));
  entries.sort((a, b) => b.w - a.w);
  const top = entries.slice(0, 2);
  const labels: Record<DimensionKey, string> = {
    coding: '编程能力',
    agent: 'Agent 能力',
    longContext: '长上下文处理',
    knowledge: '知识准确性',
    reasoning: '专业推理',
    cost: '成本控制',
    speed: '生成速度',
  };
  return `您最看重${labels[top[0].key]}与${labels[top[1].key]}，是典型的${getPersona(top[0].key)}用户。`;
}

function getPersona(key: DimensionKey): string {
  const map: Record<DimensionKey, string> = {
    coding: '技术开发',
    agent: '自动化驱动',
    longContext: '长文档处理',
    knowledge: '知识准确',
    reasoning: '深度推理',
    cost: '成本敏感',
    speed: '效率优先',
  };
  return map[key];
}