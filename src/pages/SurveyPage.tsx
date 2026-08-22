import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'motion/react';
import { ArrowRight, RotateCcw, SlidersHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { MainLayout } from '@/components/layouts/MainLayout';
import { useApp } from '@/contexts/AppContext';
import { DIMENSIONS, DIMENSION_KEYS } from '@/lib/types';
import type { DimensionKey } from '@/lib/types';

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
      <div className="mx-auto max-w-2xl">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          <div className="mb-6 text-center">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary">
              <SlidersHorizontal className="h-3.5 w-3.5" /> 拖动滑块设定偏好权重
            </div>
            <h1 className="text-balance text-2xl font-bold text-foreground md:text-3xl">设定您的偏好权重</h1>
            <p className="mx-auto mt-2 max-w-prose text-pretty text-sm text-muted-foreground">
              直接拖动每个维度的滑块即可表达您的偏好强度，系统会自动归一化为偏好权重，无需填写问卷。
            </p>
          </div>

          <Card className="glass-card p-6 md:p-8">
            <div className="flex flex-col gap-6">
              {DIMENSIONS.map((d) => (
                <div key={d.key}>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium text-foreground">{d.label}</span>
                    <span className="text-xs font-semibold text-primary">
                      权重 {(normalized[d.key] * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Slider
                      value={[raw[d.key]]}
                      min={0}
                      max={100}
                      step={1}
                      onValueChange={(v) => handleChange(d.key, v[0])}
                      className="flex-1"
                    />
                    <span className="w-8 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
                      {raw[d.key]}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <div className="mt-6 flex items-center justify-between">
            <Button variant="ghost" onClick={handleReset}>
              <RotateCcw className="mr-1 h-4 w-4" /> 重置
            </Button>
            <Button
              onClick={handleSubmit}
              className="bg-gradient-primary text-primary-foreground hover:opacity-90"
            >
              生成偏好画像 <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        </motion.div>
      </div>
    </MainLayout>
  );
};

export default SurveyPage;