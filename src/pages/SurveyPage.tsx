import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'motion/react';
import { ArrowRight, RotateCcw, SlidersHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { MainLayout } from '@/components/layouts/MainLayout';
import { StepIndicator } from '@/components/StepIndicator';
import { CapabilityRadar, buildRadarData } from '@/components/CapabilityRadar';
import { useApp } from '@/contexts/AppContext';
import { DIMENSIONS, DIMENSION_KEYS } from '@/lib/types';
import type { DimensionKey } from '@/lib/types';
import { cn } from '@/lib/utils';

const DEFAULT_RAW: Record<DimensionKey, number> = DIMENSION_KEYS.reduce(
  (acc, k) => {
    acc[k] = 50;
    return acc;
  },
  {} as Record<DimensionKey, number>
);

const SurveyPage: React.FC = () => {
  const navigate = useNavigate();
  const { setProfileFromWeights } = useApp();
  const [raw, setRaw] = useState<Record<DimensionKey, number>>({ ...DEFAULT_RAW });

  const total = useMemo(() => DIMENSION_KEYS.reduce((acc, k) => acc + raw[k], 0), [raw]);

  const normalized = useMemo<Record<DimensionKey, number>>(() => {
    const sum = total || 1;
    return DIMENSION_KEYS.reduce(
      (acc, k) => {
        acc[k] = raw[k] / sum;
        return acc;
      },
      {} as Record<DimensionKey, number>
    );
  }, [raw, total]);

  // 归一化后的最大权重，用于给条形做相对着色
  const maxW = useMemo(() => Math.max(...DIMENSION_KEYS.map((k) => normalized[k])), [normalized]);

  const radarData = useMemo(
    () =>
      buildRadarData([
        { name: '偏好', profile: normalized as never, color: 'hsl(var(--chart-1))' },
      ]),
    [normalized]
  );

  const handleChange = (key: DimensionKey, value: number) => {
    setRaw((prev) => ({ ...prev, [key]: value }));
  };

  const handleReset = () => setRaw({ ...DEFAULT_RAW });

  const handleSubmit = () => {
    setProfileFromWeights(raw);
    navigate('/profile');
  };

  return (
    <MainLayout>
      <div className="relative mx-auto max-w-5xl">
        <div className="orb -left-28 top-0 h-64 w-64 bg-primary/20 animate-drift" />
        <div className="orb -right-28 top-40 h-64 w-64 bg-accent/20 animate-drift [animation-delay:2.5s]" />

        <div className="relative">
          <StepIndicator current={1} />

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <div className="mb-6 text-center">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary">
                <SlidersHorizontal className="h-3.5 w-3.5" /> 第 1 步：设定偏好
              </div>
              <h1 className="text-balance text-2xl font-bold text-foreground md:text-3xl">
                你更看重 <span className="gradient-text-animated">哪些能力</span>？
              </h1>
              <p className="mx-auto mt-2 max-w-prose text-pretty text-sm text-muted-foreground">
                拖动滑块表达偏好强度，右侧雷达图会实时更新。系统自动归一化为权重 w
                <sub>k</sub>，总和为 1。
              </p>
            </div>

            <div className="grid gap-5 lg:grid-cols-[1.35fr_1fr]">
              {/* 滑块 */}
              <Card className="glass-card p-5 md:p-6">
                <div className="flex flex-col gap-5">
                  {DIMENSIONS.map((d, i) => {
                    const w = normalized[d.key];
                    const isTop = w >= maxW - 1e-9 && total > 0;
                    return (
                      <motion.div
                        key={d.key}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.04 }}
                      >
                        <div className="mb-2 flex items-center justify-between gap-2">
                          <span
                            className={cn(
                              'text-sm transition-colors',
                              isTop ? 'font-semibold text-foreground' : 'font-medium text-foreground/80'
                            )}
                          >
                            {d.label}
                          </span>
                          <span
                            className={cn(
                              'num rounded-full px-2 py-0.5 text-xs font-semibold transition-colors',
                              isTop ? 'bg-primary/15 text-primary' : 'text-muted-foreground'
                            )}
                          >
                            {(w * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <Slider
                            value={[raw[d.key]]}
                            min={0}
                            max={100}
                            step={1}
                            aria-label={d.label}
                            onValueChange={(v) => handleChange(d.key, v[0])}
                            className="flex-1"
                          />
                          <span className="num w-8 shrink-0 text-right text-xs text-muted-foreground">
                            {raw[d.key]}
                          </span>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>

                {total === 0 && (
                  <p className="mt-4 rounded-lg border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-foreground">
                    所有维度都是 0，将退化为等权重（每项 14.3%）。
                  </p>
                )}
              </Card>

              {/* 实时预览 */}
              <Card className="glass-card flex flex-col p-5 md:p-6">
                <p className="mb-1 text-sm font-semibold text-foreground">实时偏好画像</p>
                <p className="mb-2 text-xs text-muted-foreground">拖动左侧滑块即可看到变化</p>
                <div className="flex-1">
                  <CapabilityRadar
                    data={radarData}
                    series={[{ key: '偏好', name: '偏好权重', color: 'hsl(var(--chart-1))' }]}
                    height={260}
                    showLegend={false}
                  />
                </div>
              </Card>
            </div>

            <div className="mt-6 flex items-center justify-between">
              <Button variant="ghost" onClick={handleReset}>
                <RotateCcw className="mr-1 h-4 w-4" /> 重置
              </Button>
              <Button
                size="lg"
                onClick={handleSubmit}
                className="bg-gradient-primary text-primary-foreground hover:opacity-90"
              >
                生成偏好画像 <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </div>
          </motion.div>
        </div>
      </div>
    </MainLayout>
  );
};

export default SurveyPage;
