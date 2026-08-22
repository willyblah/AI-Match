import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'motion/react';
import { ArrowRight, ShieldCheck, AlertTriangle, Sparkles } from 'lucide-react';
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
          <p className="text-muted-foreground">请先完成偏好问卷</p>
          <Button className="mt-4 bg-gradient-primary text-primary-foreground hover:opacity-90" onClick={() => navigate('/survey')}>
            去填写问卷
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

          {/* 一致性检验 */}
          <Card className="glass-card mt-4 p-5">
            <div className="flex flex-wrap items-center gap-4">
              <div
                className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                  profile.consistent ? 'bg-chart-5/15 text-chart-5' : 'bg-destructive/15 text-destructive'
                }`}
              >
                {profile.consistent ? <ShieldCheck className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                <span>{profile.consistent ? '一致性检验通过' : '一致性未通过，建议调整问卷'}</span>
              </div>
              <div className="grid flex-1 grid-cols-3 gap-3 text-center">
                <div className="rounded-lg bg-secondary/50 p-2.5">
                  <p className="text-[10px] text-muted-foreground">最大特征值 λmax</p>
                  <p className="text-sm font-semibold text-foreground">{profile.lambdaMax.toFixed(4)}</p>
                </div>
                <div className="rounded-lg bg-secondary/50 p-2.5">
                  <p className="text-[10px] text-muted-foreground">一致性指标 CI</p>
                  <p className="text-sm font-semibold text-foreground">{profile.ci.toFixed(4)}</p>
                </div>
                <div className="rounded-lg bg-secondary/50 p-2.5">
                  <p className="text-[10px] text-muted-foreground">一致性比例 CR</p>
                  <p className="text-sm font-semibold text-foreground">{profile.cr.toFixed(4)}</p>
                </div>
              </div>
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              采用特征值法计算判断矩阵最大特征值与特征向量，CR &lt; 0.1 视为一致性可接受（n=7 时 RI=1.32）。
            </p>
          </Card>

          {/* 操作 */}
          <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button variant="secondary" onClick={() => navigate('/survey')}>
              重新测试
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