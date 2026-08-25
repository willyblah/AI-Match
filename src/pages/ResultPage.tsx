import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'motion/react';
import * as Icons from 'lucide-react';
import {
  ArrowRight,
  RotateCcw,
  Target,
  Wallet,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  Layers,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { MainLayout } from '@/components/layouts/MainLayout';
import { StepIndicator } from '@/components/StepIndicator';
import { RecommendationCard } from '@/components/RecommendationCard';
import { useApp } from '@/contexts/AppContext';
import { cn } from '@/lib/utils';

const ResultPage: React.FC = () => {
  const navigate = useNavigate();
  const { profile, selectedTasks, budget, frequency, result, runRecommendation, hasResult } =
    useApp();
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    if (profile && selectedTasks.length > 0 && !hasResult) runRecommendation();
  }, [profile, selectedTasks, hasResult, runRecommendation]);

  if (!profile || selectedTasks.length === 0) {
    return (
      <MainLayout>
        <div className="mx-auto max-w-md py-20 text-center">
          <p className="text-muted-foreground">请先设定偏好并选择任务</p>
          <Button
            className="mt-4 bg-gradient-primary text-primary-foreground hover:opacity-90"
            onClick={() => navigate('/survey')}
          >
            重新开始
          </Button>
        </div>
      </MainLayout>
    );
  }

  if (!result) return null;

  const { taskResults, assignment, totalMonthlyCost, withinBudget, bestSingle, mixedGainPct } =
    result;
  const multi = taskResults.length > 1;
  const active = taskResults[Math.min(activeTab, taskResults.length - 1)];
  const distinctTools = new Set(assignment.map((a) => a.tool.id)).size;

  return (
    <MainLayout>
      <div className="relative mx-auto max-w-5xl">
        <div className="orb -left-32 top-10 h-72 w-72 bg-primary/15 animate-drift" />
        <div className="orb -right-32 top-40 h-72 w-72 bg-accent/15 animate-drift [animation-delay:3s]" />

        <div className="relative">
          <StepIndicator current={4} reachable={4} />

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <div className="mb-6 text-center">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary">
                <Target className="h-3.5 w-3.5" /> 推荐结果
              </div>
              <h1 className="text-balance text-2xl font-bold text-foreground md:text-3xl">
                你的 <span className="gradient-text-animated">AI 组合方案</span>
              </h1>
              <p className="mt-2 text-sm text-muted-foreground">
                {taskResults.length} 个任务 · 预算 ${budget}/月 · 每任务 {frequency} 次/月
              </p>
            </div>
          </motion.div>

          {/* ---------- 方案总览 ---------- */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
          >
            <Card className="glass-card relative overflow-hidden edge-top p-5 md:p-6">
              <div className="mb-4 flex items-center gap-2">
                <Layers className="h-4 w-4 text-primary" />
                <h2 className="text-sm font-semibold text-foreground">任务指派方案</h2>
              </div>

              {/* 指派列表 */}
              <div className="flex flex-col gap-2">
                {assignment.map((a, i) => {
                  const Icon =
                    (Icons[a.task.icon as keyof typeof Icons] as React.FC<{ className?: string }>) ||
                    Icons.Box;
                  return (
                    <motion.div
                      key={a.task.id}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 + i * 0.06 }}
                      className="flex flex-wrap items-center gap-3 rounded-xl border border-border/70 bg-background/50 px-3 py-2.5"
                    >
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary text-muted-foreground">
                        <Icon className="h-4 w-4" />
                      </div>
                      <span className="min-w-0 flex-1 truncate text-sm text-foreground">
                        {a.task.name}
                      </span>
                      <ArrowRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                      <Link
                        to={`/tool/${a.tool.id}`}
                        className="truncate text-sm font-semibold text-primary hover:underline"
                      >
                        {a.tool.name}
                      </Link>
                      <span className="num shrink-0 rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary">
                        {a.matchScore}%
                      </span>
                      <span className="num shrink-0 text-xs text-muted-foreground">
                        ${a.monthlyCost.toFixed(2)}/月
                      </span>
                    </motion.div>
                  );
                })}
              </div>

              {/* 汇总统计 */}
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <div className="rounded-xl border border-border/70 bg-background/50 p-3">
                  <p className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                    <Wallet className="h-3.5 w-3.5" /> 月度总成本
                  </p>
                  <p className="num mt-0.5 text-xl font-bold text-foreground">
                    ${totalMonthlyCost.toFixed(2)}
                  </p>
                </div>
                <div
                  className={cn(
                    'rounded-xl border p-3',
                    withinBudget
                      ? 'border-chart-5/30 bg-chart-5/10'
                      : 'border-destructive/30 bg-destructive/10'
                  )}
                >
                  <p className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                    {withinBudget ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-chart-5" />
                    ) : (
                      <AlertTriangle className="h-3.5 w-3.5 text-destructive" />
                    )}
                    预算 ${budget}
                  </p>
                  <p
                    className={cn(
                      'mt-0.5 text-sm font-semibold',
                      withinBudget ? 'text-chart-5' : 'text-destructive'
                    )}
                  >
                    {withinBudget
                      ? `剩余 $${(budget - totalMonthlyCost).toFixed(2)}`
                      : `超出 $${(totalMonthlyCost - budget).toFixed(2)}`}
                  </p>
                </div>
                <div className="rounded-xl border border-border/70 bg-background/50 p-3">
                  <p className="text-[11px] text-muted-foreground">调用模型数</p>
                  <p className="num mt-0.5 text-xl font-bold text-foreground">
                    {distinctTools}
                    <span className="ml-1 text-xs font-normal text-muted-foreground">款</span>
                  </p>
                </div>
              </div>

              {/* 混合 vs 单一模型：论文的核心结论 */}
              {multi && bestSingle && (
                <div className="mt-4 rounded-xl border border-accent/30 bg-accent/[0.07] p-3.5">
                  <p className="mb-1 flex items-center gap-1.5 text-xs font-medium text-accent">
                    <Sparkles className="h-3.5 w-3.5" /> 混合调用 vs 单一模型
                  </p>
                  <p className="text-xs leading-relaxed text-muted-foreground">
                    {distinctTools === 1 ? (
                      <>
                        在你的偏好与任务组合下，
                        <span className="font-medium text-foreground">{bestSingle.tool.name}</span>{' '}
                        在每个任务上都是预算内的最优解，本次无需混合调用。
                      </>
                    ) : mixedGainPct > 0.5 ? (
                      <>
                        当前方案用{' '}
                        <span className="font-medium text-foreground">{distinctTools}</span>{' '}
                        款模型分工协作。若全部改用单一模型（最优为{' '}
                        <span className="font-medium text-foreground">{bestSingle.tool.name}</span>
                        ），总适配效用将下降约{' '}
                        <span className="num font-semibold text-accent">
                          {mixedGainPct.toFixed(1)}%
                        </span>
                        —— 印证论文结论：多模型混合调用优于单一模型。
                      </>
                    ) : (
                      <>
                        当前方案用{' '}
                        <span className="font-medium text-foreground">{distinctTools}</span>{' '}
                        款模型分工，但与全部使用{' '}
                        <span className="font-medium text-foreground">{bestSingle.tool.name}</span>{' '}
                        相比效用几乎相同（差距 &lt; 0.5%）。此时用单一模型也是合理选择，还能省去多模型切换的管理成本。
                      </>
                    )}
                  </p>
                </div>
              )}
            </Card>
          </motion.div>

          {/* ---------- 分任务详情 ---------- */}
          <div className="mt-8">
            {multi && (
              <div className="mb-4 flex flex-wrap gap-2">
                {taskResults.map((r, i) => {
                  const on = i === Math.min(activeTab, taskResults.length - 1);
                  return (
                    <button
                      key={r.task.id}
                      type="button"
                      onClick={() => setActiveTab(i)}
                      className={cn(
                        'rounded-full border px-3.5 py-1.5 text-xs font-medium transition-all duration-200',
                        on
                          ? 'border-transparent bg-gradient-primary text-primary-foreground shadow-card'
                          : 'border-border bg-card/70 text-muted-foreground hover:border-primary/40 hover:text-foreground'
                      )}
                    >
                      {r.task.name}
                    </button>
                  );
                })}
              </div>
            )}

            <h2 className="mb-3 text-sm font-semibold text-foreground">
              「{active.task.name}」Top {active.recommendations.length} 推荐
            </h2>

            <div className="flex flex-col gap-5">
              {active.recommendations.map((rec, i) => (
                <motion.div
                  key={`${active.task.id}-${rec.tool.id}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 }}
                >
                  <RecommendationCard rec={rec} rank={i + 1} />
                </motion.div>
              ))}
            </div>
          </div>

          {/* 操作 */}
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button variant="secondary" onClick={() => navigate('/task')}>
              <RotateCcw className="mr-1 h-4 w-4" /> 换个任务组合
            </Button>
            <Button
              size="lg"
              className="bg-gradient-primary text-primary-foreground hover:opacity-90"
              onClick={() => navigate('/survey')}
            >
              重新测试偏好 <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default ResultPage;
