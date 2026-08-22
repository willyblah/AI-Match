import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';
import type { DimensionKey, UserProfile, TaskTemplate, Recommendation } from '@/lib/types';
import { computeRecommendations } from '@/lib/engine';
import { normalizeWeights, generateProfileDescription } from '@/lib/survey';
import { AI_TOOLS } from '@/lib/data';

interface AppState {
  profile: UserProfile | null;
  hasProfile: boolean;
  // 由用户拖动滑块设定的原始权重（0~100）计算偏好画像
  setProfileFromWeights: (raw: Record<DimensionKey, number>) => void;
  // 当前任务
  selectedTask: TaskTemplate | null;
  setSelectedTask: (task: TaskTemplate | null) => void;
  budget: number;
  setBudget: (n: number) => void;
  frequency: number;
  setFrequency: (n: number) => void;
  // 推荐结果
  recommendations: Recommendation[];
  runRecommendation: () => void;
  hasResult: boolean;
  // 对比
  compareIds: string[];
  toggleCompare: (id: string) => void;
  clearCompare: () => void;
}

const AppContext = createContext<AppState | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [selectedTask, setSelectedTask] = useState<TaskTemplate | null>(null);
  const [budget, setBudget] = useState(30);
  const [frequency, setFrequency] = useState(100);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [hasResult, setHasResult] = useState(false);
  const [compareIds, setCompareIds] = useState<string[]>([]);

  const setProfileFromWeights = useCallback(
    (raw: Record<DimensionKey, number>) => {
      const weights = normalizeWeights(raw);
      const description = generateProfileDescription(weights);
      setProfile({
        scenario: 'custom',
        mainTask: '自定义偏好',
        budget,
        frequency: String(frequency),
        weights,
        description,
      });
    },
    [budget, frequency]
  );

  const runRecommendation = useCallback(() => {
    if (!profile || !selectedTask) return;
    // 根据任务类型筛选候选工具
    const isMediaTask = selectedTask.id === 'image-generation' || selectedTask.id === 'video-generation';
    const candidates = isMediaTask
      ? AI_TOOLS.filter((t) => t.category === selectedTask.id.replace('-generation', ''))
      : AI_TOOLS.filter((t) => t.category === 'llm');

    const { recommendations: recs } = computeRecommendations({
      tools: candidates,
      weights: profile.weights,
      demands: selectedTask.demands,
      budget,
      frequency,
      avgInputTokens: selectedTask.avgInputTokens,
      avgOutputTokens: selectedTask.avgOutputTokens,
    });
    setRecommendations(recs);
    setHasResult(true);
  }, [profile, selectedTask, budget, frequency]);

  const toggleCompare = useCallback((id: string) => {
    setCompareIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 4) return prev;
      return [...prev, id];
    });
  }, []);

  const clearCompare = useCallback(() => setCompareIds([]), []);

  const value = useMemo<AppState>(
    () => ({
      profile,
      hasProfile: !!profile,
      setProfileFromWeights,
      selectedTask,
      setSelectedTask,
      budget,
      setBudget,
      frequency,
      setFrequency,
      recommendations,
      runRecommendation,
      hasResult,
      compareIds,
      toggleCompare,
      clearCompare,
    }),
    [
      profile,
      setProfileFromWeights,
      selectedTask,
      budget,
      frequency,
      recommendations,
      runRecommendation,
      hasResult,
      compareIds,
      toggleCompare,
      clearCompare,
    ]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export function useApp(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}

export type { DimensionKey };