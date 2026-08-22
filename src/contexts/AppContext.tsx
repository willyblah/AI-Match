import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';
import type { DimensionKey, UserProfile, TaskTemplate, Recommendation } from '@/lib/types';
import { computeAhpWeights, computeRecommendations } from '@/lib/engine';
import {
  buildPreferenceScores,
  buildJudgmentMatrix,
  generateProfileDescription,
} from '@/lib/survey';
import { AI_TOOLS } from '@/lib/data';

interface AppState {
  profile: UserProfile | null;
  hasProfile: boolean;
  setProfileFromAnswers: (answers: Record<string, string | string[]>) => void;
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

  const setProfileFromAnswers = useCallback((answers: Record<string, string | string[]>) => {
    const scores = buildPreferenceScores(answers);
    const matrix = buildJudgmentMatrix(scores);
    const ahp = computeAhpWeights(matrix);
    const description = generateProfileDescription(ahp.weights);

    const scenarioRaw = Array.isArray(answers.scenario) ? answers.scenario[0] : answers.scenario;
    const scenario = scenarioRaw || 'office';
    const mainTask = Array.isArray(answers.mainTask)
      ? answers.mainTask.join('、')
      : answers.mainTask || '';
    const budgetRaw = Array.isArray(answers.budget) ? answers.budget[0] : answers.budget;
    const freqRaw = Array.isArray(answers.frequency) ? answers.frequency[0] : answers.frequency;
    const budgetVal = Number(budgetRaw || '30');
    const freqVal = Number(freqRaw || '100');

    setProfile({
      scenario,
      mainTask,
      budget: budgetVal,
      frequency: String(freqVal),
      weights: ahp.weights,
      lambdaMax: ahp.lambdaMax,
      ci: ahp.ci,
      cr: ahp.cr,
      consistent: ahp.consistent,
      description,
    });
    setBudget(budgetVal);
    setFrequency(freqVal);
  }, []);

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
      setProfileFromAnswers,
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
      setProfileFromAnswers,
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