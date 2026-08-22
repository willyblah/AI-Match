import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { Trophy, DollarSign } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MainLayout } from '@/components/layouts/MainLayout';
import { computeRankings, rankByDimension, rankByCostPerformance } from '@/lib/engine';
import { DIMENSIONS, type DimensionKey, type RankEntry } from '@/lib/types';

type RankMode = 'overall' | DimensionKey | 'cp';

const RankingPage: React.FC = () => {
  const [mode, setMode] = useState<RankMode>('overall');

  const getEntries = (): RankEntry[] => {
    if (mode === 'overall') return computeRankings().sort((a, b) => b.overallScore - a.overallScore);
    if (mode === 'cp') return rankByCostPerformance();
    return rankByDimension(mode);
  };

  const entries = getEntries();

  const getScore = (e: RankEntry): number => {
    if (mode === 'overall') return e.overallScore;
    if (mode === 'cp') return e.overallScore / (e.costPerTask || 0.01);
    return e.topsis[mode] ?? 0;
  };

  const modeLabel = () => {
    if (mode === 'overall') return '综合得分';
    if (mode === 'cp') return '性价比指数';
    return DIMENSIONS.find((d) => d.key === mode)?.label || '';
  };

  return (
    <MainLayout>
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 text-center">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary">
            <Trophy className="h-3.5 w-3.5" /> AI 工具排行榜
          </div>
          <h1 className="text-balance text-2xl font-bold text-foreground md:text-3xl">能力排行榜</h1>
          <p className="mt-2 text-sm text-muted-foreground">基于熵权-TOPSIS 多维能力评价，实时更新</p>
        </div>

        <Tabs value={mode} onValueChange={(v) => setMode(v as RankMode)}>
          <TabsList className="mb-4 flex h-auto flex-wrap gap-1 bg-secondary/50 p-1">
            <TabsTrigger value="overall" className="text-xs">综合</TabsTrigger>
            {DIMENSIONS.map((d) => (
              <TabsTrigger key={d.key} value={d.key} className="text-xs">
                {d.shortLabel}
              </TabsTrigger>
            ))}
            <TabsTrigger value="cp" className="text-xs">性价比</TabsTrigger>
          </TabsList>
        </Tabs>

        <Card className="glass-card overflow-hidden">
          <div className="w-full max-w-full overflow-x-auto bg-card">
            <table className="w-full min-w-max text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="whitespace-nowrap px-4 py-3">排名</th>
                  <th className="whitespace-nowrap px-4 py-3">AI 工具</th>
                  <th className="whitespace-nowrap px-4 py-3">公司</th>
                  <th className="whitespace-nowrap px-4 py-3 text-right">{modeLabel()}</th>
                  <th className="whitespace-nowrap px-4 py-3 text-right">
                    <span className="inline-flex items-center gap-1">
                      <DollarSign className="h-3 w-3" /> 单任务成本
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e, i) => (
                  <motion.tr
                    key={e.tool.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.04 }}
                    className="border-b border-border/50 transition-colors hover:bg-secondary/30"
                  >
                    <td className="whitespace-nowrap px-4 py-3">
                      <span
                        className={`inline-flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold ${
                          i === 0
                            ? 'bg-primary/20 text-primary'
                            : i === 1
                              ? 'bg-accent/20 text-accent'
                              : i === 2
                                ? 'bg-chart-4/20 text-chart-4'
                                : 'bg-secondary text-muted-foreground'
                        }`}
                      >
                        {i + 1}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <Link to={`/tool/${e.tool.id}`} className="font-medium text-foreground hover:text-primary">
                        {e.tool.name}
                      </Link>
                      <Badge variant="secondary" className="ml-2 text-[10px]">
                        {e.tool.category === 'llm' ? 'LLM' : e.tool.category === 'image' ? '图像' : '视频'}
                      </Badge>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">{e.tool.company}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-right font-semibold text-primary">
                      {getScore(e).toFixed(3)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right text-muted-foreground">
                      ${e.costPerTask.toFixed(2)}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </MainLayout>
  );
};

export default RankingPage;