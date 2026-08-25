import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';
import type { DimensionKey, UserProfile, TaskTemplate } from '@/lib/types';
import { computeMultiTaskRecommendations } from '@/lib/engine';
import type { MultiTaskOutput } from '@/lib/engine';
import { normalizeWeights, generateProfileDescription } from '@/lib/survey';
import { AI_TOOLS } from '@/lib/data';

/** 一次可选择的最大任务数，避免结果页过长。 */
export const MAX_TASKS = 5;

/** 对比页最多可同时对比的工具数：允许一次看完库内全部模型。 */
export const MAX_COMPARE = AI_TOOLS.length;

interface AppState {
  profile: UserProfile | null;
  hasProfile: boolean;
  // 由用户拖动滑块设定的原始权重（0~100）计算偏好画像
  setProfileFromWeights: (raw: Record<DimensionKey, number>) => void;
  // 当前任务（多选）
  selectedTasks: TaskTemplate[];
  toggleTask: (task: TaskTemplate) => void;
  clearTasks: () => void;
  isTaskSelected: (id: string) => boolean;
  budget: number;
  setBudget: (n: number) => void;
  frequency: number;
  setFrequency: (n: number) => void;
  // 推荐结果
  result: MultiTaskOutput | null;
  runRecommendation: () => void;
  hasResult: boolean;
  // 对比
  compareIds: string[];
  toggleCompare: (id: string) => void;
  clearCompare: () => void;
  selectAllCompare: () => void;
}

const AppContext = createContext<AppState | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [selectedTasks, setSelectedTasks] = useState<TaskTemplate[]>([]);
  const [budget, setBudget] = useState(30);
  const [frequency, setFrequency] = useState(100);
  const [result, setResult] = useState<MultiTaskOutput | null>(null);
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
      // 偏好变了，旧结果作废
      setHasResult(false);
    },
    [budget, frequency]
  );

  const toggleTask = useCallback((task: TaskTemplate) => {
    setSelectedTasks((prev) => {
      const exists = prev.some((t) => t.id === task.id);
      if (exists) return prev.filter((t) => t.id !== task.id);
      if (prev.length >= MAX_TASKS) return prev;
      return [...prev, task];
    });
    setHasResult(false);
  }, []);

  const clearTasks = useCallback(() => {
    setSelectedTasks([]);
    setHasResult(false);
  }, []);

  const isTaskSelected = useCallback(
    (id: string) => selectedTasks.some((t) => t.id === id),
    [selectedTasks]
  );

  const runRecommendation = useCallback(() => {
    if (!profile || selectedTasks.length === 0) return;
    // 图片/视频类任务只在同类工具中匹配；其余用 LLM
    const mediaOnly = selectedTasks.every(
      (t) => t.id === 'image-generation' || t.id === 'video-generation'
    );
    const candidates = mediaOnly
      ? AI_TOOLS.filter((t) => t.category === selectedTasks[0].id.replace('-generation', ''))
      : AI_TOOLS.filter((t) => t.category === 'llm');

    setResult(
      computeMultiTaskRecommendations({
        tools: candidates,
        weights: profile.weights,
        tasks: selectedTasks,
        budget,
        frequencyPerTask: frequency,
      })
    );
    setHasResult(true);
  }, [profile, selectedTasks, budget, frequency]);

  const toggleCompare = useCallback((id: string) => {
    setCompareIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= MAX_COMPARE) return prev;
      return [...prev, id];
    });
  }, []);

  const clearCompare = useCallback(() => setCompareIds([]), []);

  const selectAllCompare = useCallback(
    () => setCompareIds(AI_TOOLS.slice(0, MAX_COMPARE).map((t) => t.id)),
    []
  );

  const value = useMemo<AppState>(
    () => ({
      profile,
      hasProfile: !!profile,
      setProfileFromWeights,
      selectedTasks,
      toggleTask,
      clearTasks,
      isTaskSelected,
      budget,
      setBudget,
      frequency,
      setFrequency,
      result,
      runRecommendation,
      hasResult,
      compareIds,
      toggleCompare,
      clearCompare,
      selectAllCompare,
    }),
    [
      profile,
      setProfileFromWeights,
      selectedTasks,
      toggleTask,
      clearTasks,
      isTaskSelected,
      budget,
      frequency,
      result,
      runRecommendation,
      hasResult,
      compareIds,
      toggleCompare,
      clearCompare,
      selectAllCompare,
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
