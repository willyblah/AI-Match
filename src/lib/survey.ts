import type { DimensionKey } from './types';
import { DIMENSION_KEYS } from './types';

// 将用户拖动设定的原始权重（0~100）归一化为偏好权重（总和为 1）
export function normalizeWeights(raw: Record<DimensionKey, number>): Record<DimensionKey, number> {
  const sum = DIMENSION_KEYS.reduce((acc, k) => acc + (raw[k] || 0), 0);
  if (sum <= 0) {
    // 全为 0 时退化为等权
    const even = 1 / DIMENSION_KEYS.length;
    return DIMENSION_KEYS.reduce(
      (acc, k) => {
        acc[k] = even;
        return acc;
      },
      {} as Record<DimensionKey, number>
    );
  }
  return DIMENSION_KEYS.reduce(
    (acc, k) => {
      acc[k] = (raw[k] || 0) / sum;
      return acc;
    },
    {} as Record<DimensionKey, number>
  );
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