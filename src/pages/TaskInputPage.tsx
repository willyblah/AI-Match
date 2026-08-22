import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'motion/react';
import * as Icons from 'lucide-react';
import { DollarSign, Repeat, ArrowRight, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { MainLayout } from '@/components/layouts/MainLayout';
import { TASK_TEMPLATES } from '@/lib/data';
import { useApp } from '@/contexts/AppContext';
import { cn } from '@/lib/utils';

const TaskInputPage: React.FC = () => {
  const navigate = useNavigate();
  const { profile, selectedTask, setSelectedTask, budget, setBudget, frequency, setFrequency } = useApp();

  if (!profile) {
    return (
      <MainLayout>
        <div className="mx-auto max-w-md py-20 text-center">
          <p className="text-muted-foreground">请先完成偏好问卷</p>
          <Button className="mt-4 bg-gradient-primary text-primary-foreground hover:opacity-90" onClick={() => navigate('/survey')}>
            去填写问卷
          </Button>
        </div>
      </MainLayout>
    );
  }

  const handleRun = () => {
    if (!selectedTask) return;
    navigate('/result');
  };

  return (
    <MainLayout>
      <div className="mx-auto max-w-4xl">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          <div className="mb-6 text-center">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-xs font-medium text-accent">
              <Sparkles className="h-3.5 w-3.5" /> 第 3 步：输入任务
            </div>
            <h1 className="text-balance text-2xl font-bold text-foreground md:text-3xl">选择你的任务</h1>
            <p className="mt-2 text-sm text-muted-foreground">选择任务类型，系统将根据其能力需求向量进行匹配</p>
          </div>

          {/* 任务模板 */}
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
            {TASK_TEMPLATES.map((task) => {
              const Icon = (Icons[task.icon as keyof typeof Icons] as React.FC<{ className?: string }>) || Icons.Box;
              const active = selectedTask?.id === task.id;
              return (
                <button
                  key={task.id}
                  type="button"
                  onClick={() => setSelectedTask(task)}
                  className={cn(
                    'flex h-full flex-col items-start gap-2 rounded-xl border p-4 text-left transition-all',
                    active
                      ? 'border-primary bg-primary/10 glow-primary'
                      : 'border-border bg-background/40 hover:border-primary/40 hover:bg-secondary/50'
                  )}
                >
                  <div
                    className={cn(
                      'flex h-10 w-10 items-center justify-center rounded-lg',
                      active ? 'bg-primary/20 text-primary' : 'bg-secondary text-muted-foreground'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className={cn('text-sm font-semibold', active ? 'text-foreground' : 'text-muted-foreground')}>
                    {task.name}
                  </span>
                  <span className="text-xs text-muted-foreground">{task.description}</span>
                </button>
              );
            })}
          </div>

          {/* 参数 */}
          {selectedTask && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 grid gap-4 md:grid-cols-2"
            >
              <Card className="glass-card p-5">
                <div className="mb-3 flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-accent" />
                  <span className="text-sm font-medium text-foreground">月度预算（美元）</span>
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
                  <span className="w-20 text-right text-lg font-bold gradient-text">${budget}</span>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">预算将作为硬约束参与推荐优化</p>
              </Card>

              <Card className="glass-card p-5">
                <div className="mb-3 flex items-center gap-2">
                  <Repeat className="h-4 w-4 text-accent" />
                  <span className="text-sm font-medium text-foreground">每月调用次数</span>
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
                  <span className="w-20 text-right text-lg font-bold gradient-text">{frequency}</span>
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
              disabled={!selectedTask}
              onClick={handleRun}
              className="bg-gradient-primary text-primary-foreground hover:opacity-90"
            >
              生成推荐 <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        </motion.div>
      </div>
    </MainLayout>
  );
};

export default TaskInputPage;