import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'motion/react';
import { ArrowRight, RotateCcw, Target } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MainLayout } from '@/components/layouts/MainLayout';
import { RecommendationCard } from '@/components/RecommendationCard';
import { useApp } from '@/contexts/AppContext';

const ResultPage: React.FC = () => {
  const navigate = useNavigate();
  const { profile, selectedTask, budget, frequency, recommendations, runRecommendation, hasResult } = useApp();

  useEffect(() => {
    if (profile && selectedTask && !hasResult) {
      runRecommendation();
    }
  }, [profile, selectedTask, hasResult, runRecommendation]);

  if (!profile || !selectedTask) {
    return (
      <MainLayout>
        <div className="mx-auto max-w-md py-20 text-center">
          <p className="text-muted-foreground">请先完成问卷并选择任务</p>
          <Button className="mt-4 bg-gradient-primary text-primary-foreground hover:opacity-90" onClick={() => navigate('/survey')}>
            去填写问卷
          </Button>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="mx-auto max-w-5xl">
        {/* 头部 */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          <div className="mb-6 text-center">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary">
              <Target className="h-3.5 w-3.5" /> 推荐结果
            </div>
            <h1 className="text-balance text-2xl font-bold text-foreground md:text-3xl">
              「{selectedTask.name}」Top {recommendations.length} 推荐
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              预算 ${budget}/月 · 频率 {frequency} 次/月 · 基于 {profile.description.replace('。', '')}
            </p>
          </div>
        </motion.div>

        {/* 推荐卡片 */}
        <div className="flex flex-col gap-5">
          {recommendations.map((rec, i) => (
            <motion.div
              key={rec.tool.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.12 }}
            >
              <RecommendationCard rec={rec} rank={i + 1} />
            </motion.div>
          ))}
        </div>

        {/* 操作 */}
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button variant="secondary" onClick={() => navigate('/task')}>
            <RotateCcw className="mr-1 h-4 w-4" /> 换个任务
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
    </MainLayout>
  );
};

export default ResultPage;