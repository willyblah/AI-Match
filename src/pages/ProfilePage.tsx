import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'motion/react';
import { ArrowRight, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { MainLayout } from '@/components/layouts/MainLayout';
import { CapabilityRadar, buildRadarData } from '@/components/CapabilityRadar';
import { useApp } from '@/contexts/AppContext';
import { DIMENSIONS } from '@/lib/types';

const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { profile } = useApp();

  if (!profile) {
    return (
      <MainLayout>
        <div className="mx-auto max-w-md py-20 text-center">
          <p className="text-muted-foreground">请先设定偏好权重</p>
          <Button className="mt-4 bg-gradient-primary text-primary-foreground hover:opacity-90" onClick={() => navigate('/survey')}>
            去设定偏好
          </Button>
        </div>
      </MainLayout>
    );
  }

  const radarData = buildRadarData([
    { name: '偏好权重', profile: profile.weights as never, color: 'hsl(var(--chart-1))' },
  ]);

  const weightEntries = DIMENSIONS.map((d) => ({ label: d.label, w: profile.weights[d.key] })).sort(
    (a, b) => b.w - a.w
  );

  return (
    <MainLayout>
      <div className="mx-auto max-w-4xl">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          <div className="mb-6 text-center">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary">
              <Sparkles className="h-3.5 w-3.5" /> 您的 AI 偏好画像已生成
            </div>
            <h1 className="text-balance text-2xl font-bold text-foreground md:text-3xl">偏好画像分析</h1>
            <p className="mt-2 text-sm text-muted-foreground">{profile.description}</p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {/* 雷达图 */}
            <Card className="glass-card p-5">
              <p className="mb-2 text-xs font-medium text-muted-foreground">七维偏好权重分布</p>
              <CapabilityRadar data={radarData} series={[{ key: '偏好权重', name: '偏好权重', color: 'hsl(var(--chart-1))' }]} height={300} showLegend={false} />
            </Card>

            {/* 权重明细 */}
            <Card className="glass-card p-5">
              <p className="mb-4 text-xs font-medium text-muted-foreground">各维度权重明细</p>
              <div className="flex flex-col gap-3">
                {weightEntries.map((e) => (
                  <div key={e.label}>
                    <div className="mb-1 flex items-center justify-between text-xs">
                      <span className="text-foreground">{e.label}</span>
                      <span className="font-semibold text-primary">{(e.w * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                      <motion.div
                        className="h-full rounded-full bg-gradient-primary"
                        initial={{ width: 0 }}
                        animate={{ width: `${e.w * 100}%` }}
                        transition={{ duration: 0.6 }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* 操作 */}
          <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button variant="secondary" onClick={() => navigate('/survey')}>
              重新设定
            </Button>
            <Button
              size="lg"
              className="bg-gradient-primary text-primary-foreground hover:opacity-90"
              onClick={() => navigate('/task')}
            >
              开始推荐 <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        </motion.div>
      </div>
    </MainLayout>
  );
};

export default ProfilePage;