import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'motion/react';
import * as Icons from 'lucide-react';
import { DollarSign, Repeat, ArrowRight, Sparkles, Check, Layers, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { MainLayout } from '@/components/layouts/MainLayout';
import { StepIndicator } from '@/components/StepIndicator';
import { TASK_TEMPLATES } from '@/lib/data';
import { useApp, MAX_TASKS } from '@/contexts/AppContext';
import { cn } from '@/lib/utils';

/** 预算档位，对应论文表 4.1 的六类用户月度预算区间。 */
const BUDGET_PRESETS = [0, 30, 500, 5000];

const TaskInputPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    profile,
    selectedTasks,
    toggleTask,
    clearTasks,
    isTaskSelected,
    budget,
    setBudget,
    frequency,
    setFrequency,
    runRecommendation,
  } = useApp();

  if (!profile) {
    return (
      <MainLayout>
        <div className="mx-auto max-w-md py-20 text-center">
          <p className="text-muted-foreground">请先设定偏好权重</p>
          <Button
            className="mt-4 bg-primary text-primary-foreground hover:opacity-90"
            onClick={() => navigate('/survey')}
          >
            去设定偏好
          </Button>
        </div>
      </MainLayout>
    );
  }

  const count = selectedTasks.length;
  const atLimit = count >= MAX_TASKS;

  const handleRun = () => {
    if (count === 0) return;
    runRecommendation();
    navigate('/result');
  };

  return (
    <MainLayout>
      <div className="relative mx-auto max-w-4xl">
        <div className="orb -left-24 top-0 h-64 w-64 bg-primary/20 animate-drift" />
        <div className="orb -right-24 top-32 h-64 w-64 bg-accent/20 animate-drift [animation-delay:2s]" />

        <div className="relative">
          <StepIndicator current={3} reachable={4} />

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <div className="mb-6 text-center">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-xs font-medium text-accent">
                <Sparkles className="h-3.5 w-3.5" /> 第 3 步：选择任务
              </div>
              <h1 className="text-balance text-2xl font-bold text-foreground md:text-3xl">
                你想用 AI 做哪些事？
              </h1>
              <p className="mx-auto mt-2 max-w-prose text-pretty text-sm text-muted-foreground">
                可以<span className="font-medium text-foreground">多选</span>。系统会为每个任务
                单独匹配最合适的模型，并给出组合方案的总成本。
              </p>
            </div>

            {/* 已选计数 */}
            <div className="mb-4 flex items-center justify-between gap-3 rounded-xl border border-border bg-card/70 px-4 py-2.5 backdrop-blur">
              <div className="flex items-center gap-2 text-sm">
                <Layers className="h-4 w-4 text-primary" />
                <span className="text-muted-foreground">已选</span>
                <span className="num font-semibold text-foreground">{count}</span>
                <span className="text-muted-foreground">/ {MAX_TASKS} 个任务</span>
              </div>
              {count > 0 && (
                <Button variant="ghost" size="sm" onClick={clearTasks} className="h-8 text-xs">
                  <RotateCcw className="mr-1 h-3.5 w-3.5" /> 清空
                </Button>
              )}
            </div>

            {/* 任务多选 */}
            <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
              {TASK_TEMPLATES.map((task, i) => {
                const Icon =
                  (Icons[task.icon as keyof typeof Icons] as React.FC<{ className?: string }>) ||
                  Icons.Box;
                const active = isTaskSelected(task.id);
                const disabled = !active && atLimit;

                return (
                  <motion.button
                    key={task.id}
                    type="button"
                    role="checkbox"
                    aria-checked={active}
                    aria-label={task.name}
                    disabled={disabled}
                    onClick={() => toggleTask(task)}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: Math.min(i * 0.03, 0.3), duration: 0.3 }}
                    className={cn(
                      'card-interactive relative flex h-full flex-col items-start gap-2 overflow-hidden rounded-xl border p-4 text-left',
                      active
                        ? 'edge-top border-primary/50 bg-primary/[0.07] shadow-card'
                        : 'border-border bg-card/70 backdrop-blur hover:border-primary/40',
                      disabled && 'cursor-not-allowed opacity-40 hover:transform-none'
                    )}
                  >
                    {/* 选中标记 */}
                    <span
                      className={cn(
                        'absolute right-3 top-3 flex h-5 w-5 items-center justify-center rounded-md border transition-all duration-200',
                        active
                          ? 'border-transparent bg-primary text-primary-foreground'
                          : 'border-border bg-background'
                      )}
                    >
                      {active && <Check className="h-3.5 w-3.5" />}
                    </span>

                    <div
                      className={cn(
                        'flex h-10 w-10 items-center justify-center rounded-lg transition-colors',
                        active ? 'bg-primary/20 text-primary' : 'bg-secondary text-muted-foreground'
                      )}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <span
                      className={cn(
                        'pr-6 text-sm font-semibold',
                        active ? 'text-foreground' : 'text-muted-foreground'
                      )}
                    >
                      {task.name}
                    </span>
                    <span className="text-xs leading-relaxed text-muted-foreground">
                      {task.description}
                    </span>
                  </motion.button>
                );
              })}
            </div>

            {/* 参数 */}
            {count > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 grid gap-4 md:grid-cols-2"
              >
                <Card className="glass-card p-5">
                  <div className="mb-3 flex items-center gap-2">
                    <DollarSign className="h-4 w-4 text-accent" />
                    <span className="text-sm font-medium text-foreground">月度总预算（美元）</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Slider
                      value={[budget]}
                      onValueChange={(v) => setBudget(v[0])}
                      min={0}
                      max={5000}
                      step={5}
                      className="flex-1"
                    />
                    <span className="num w-20 shrink-0 text-right text-lg font-bold gradient-text">
                      ${budget}
                    </span>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {BUDGET_PRESETS.map((b) => (
                      <button
                        key={b}
                        type="button"
                        onClick={() => setBudget(b)}
                        className={cn(
                          'num rounded-full border px-2.5 py-1 text-[11px] transition-colors',
                          budget === b
                            ? 'border-primary/50 bg-primary/10 text-primary'
                            : 'border-border text-muted-foreground hover:border-primary/40 hover:text-foreground'
                        )}
                      >
                        {b === 0 ? '免费' : `$${b}`}
                      </button>
                    ))}
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">所有已选任务的月度成本合计上限</p>
                </Card>

                <Card className="glass-card p-5">
                  <div className="mb-3 flex items-center gap-2">
                    <Repeat className="h-4 w-4 text-accent" />
                    <span className="text-sm font-medium text-foreground">每个任务每月调用次数</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Slider
                      value={[frequency]}
                      onValueChange={(v) => setFrequency(v[0])}
                      min={1}
                      max={5000}
                      step={1}
                      className="flex-1"
                    />
                    <span className="num w-20 shrink-0 text-right text-lg font-bold gradient-text">
                      {frequency}
                    </span>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">用于估算月度总成本</p>
                </Card>
              </motion.div>
            )}

            {/* 操作 */}
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Button variant="secondary" onClick={() => navigate('/profile')}>
                返回画像
              </Button>
              <Button
                size="lg"
                disabled={count === 0}
                onClick={handleRun}
                className="bg-primary text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-40"
              >
                {count === 0 ? '请至少选择一个任务' : `生成 ${count} 个任务的推荐`}
                <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </div>
          </motion.div>
        </div>
      </div>
    </MainLayout>
  );
};

export default TaskInputPage;
