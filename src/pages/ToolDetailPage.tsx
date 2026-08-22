import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { ArrowLeft, DollarSign, Zap, Database, GitCompareArrows } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MainLayout } from '@/components/layouts/MainLayout';
import { CapabilityRadar, buildRadarData } from '@/components/CapabilityRadar';
import { AI_TOOLS } from '@/lib/data';
import { getTopsisProfile } from '@/lib/engine';
import { INDICATORS, DIMENSIONS, type DimensionKey } from '@/lib/types';
import { useApp } from '@/contexts/AppContext';

const ToolDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toggleCompare, compareIds } = useApp();

  const tool = AI_TOOLS.find((t) => t.id === id);

  if (!tool) {
    return (
      <MainLayout>
        <div className="mx-auto max-w-md py-20 text-center">
          <p className="text-muted-foreground">未找到该 AI 工具</p>
          <Button className="mt-4" variant="secondary" onClick={() => navigate('/ranking')}>
            返回排行榜
          </Button>
        </div>
      </MainLayout>
    );
  }

  const topsis = getTopsisProfile(tool.id);
  const radarData = buildRadarData([{ name: '能力', profile: topsis, color: 'hsl(var(--chart-1))' }]);
  const inCompare = compareIds.includes(tool.id);

  const categoryLabel = tool.category === 'llm' ? '大语言模型' : tool.category === 'image' ? '图像生成' : '视频生成';

  return (
    <MainLayout>
      <div className="mx-auto max-w-5xl">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="mb-4">
          <ArrowLeft className="mr-1 h-4 w-4" /> 返回
        </Button>

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          {/* 头部 */}
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-balance text-2xl font-bold text-foreground md:text-3xl">{tool.name}</h1>
                <Badge variant="secondary" className="border border-primary/30 bg-primary/10 text-primary">
                  {categoryLabel}
                </Badge>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                {tool.company} · 版本 {tool.version}
              </p>
              <p className="mt-3 max-w-prose text-sm text-muted-foreground">{tool.description}</p>
            </div>
            <Button
              variant={inCompare ? 'secondary' : 'default'}
              onClick={() => toggleCompare(tool.id)}
              className={inCompare ? '' : 'bg-gradient-primary text-primary-foreground hover:opacity-90'}
            >
              <GitCompareArrows className="mr-1 h-4 w-4" />
              {inCompare ? '已加入对比' : '加入对比'}
            </Button>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {/* 雷达图 */}
            <Card className="glass-card p-5">
              <p className="mb-2 text-xs font-medium text-muted-foreground">七维能力画像（TOPSIS 贴近度）</p>
              <CapabilityRadar data={radarData} series={[{ key: '能力', name: tool.name, color: 'hsl(var(--chart-1))' }]} height={300} showLegend={false} />
            </Card>

            {/* 关键信息 */}
            <div className="flex flex-col gap-4">
              <Card className="glass-card p-5">
                <p className="mb-3 text-xs font-medium text-muted-foreground">价格与效率</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-lg bg-secondary/50 p-3">
                    <p className="flex items-center gap-1 text-[10px] text-muted-foreground">
                      <DollarSign className="h-3 w-3" /> 输入价格
                    </p>
                    <p className="text-base font-semibold text-foreground">${tool.inputPrice}/1M</p>
                  </div>
                  <div className="rounded-lg bg-secondary/50 p-3">
                    <p className="flex items-center gap-1 text-[10px] text-muted-foreground">
                      <DollarSign className="h-3 w-3" /> 输出价格
                    </p>
                    <p className="text-base font-semibold text-foreground">${tool.outputPrice}/1M</p>
                  </div>
                  <div className="rounded-lg bg-secondary/50 p-3">
                    <p className="flex items-center gap-1 text-[10px] text-muted-foreground">
                      <DollarSign className="h-3 w-3" /> 单任务成本
                    </p>
                    <p className="text-base font-semibold text-foreground">${tool.costPerTask}</p>
                  </div>
                  <div className="rounded-lg bg-secondary/50 p-3">
                    <p className="flex items-center gap-1 text-[10px] text-muted-foreground">
                      <Zap className="h-3 w-3" /> 生成速度
                    </p>
                    <p className="text-base font-semibold text-foreground">{tool.apiSpeed} t/s</p>
                  </div>
                </div>
              </Card>

              <Card className="glass-card p-5">
                <p className="mb-3 text-xs font-medium text-muted-foreground">能力贴近度明细</p>
                <div className="flex flex-col gap-2.5">
                  {DIMENSIONS.map((d) => {
                    const v = topsis[d.key as DimensionKey] ?? 0;
                    return (
                      <div key={d.key}>
                        <div className="mb-1 flex items-center justify-between text-xs">
                          <span className="text-foreground">{d.label}</span>
                          <span className="font-semibold text-primary">{v.toFixed(2)}</span>
                        </div>
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                          <div className="h-full rounded-full bg-gradient-primary" style={{ width: `${v * 100}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>
            </div>
          </div>

          {/* 全部指标 */}
          <Card className="glass-card mt-4 overflow-hidden">
            <p className="border-b border-border/50 px-5 py-3 text-xs font-medium text-muted-foreground">
              全部 16 项 Benchmark 指标
            </p>
            <div className="w-full max-w-full overflow-x-auto bg-card">
              <table className="w-full min-w-max text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="whitespace-nowrap px-5 py-2.5">维度</th>
                    <th className="whitespace-nowrap px-5 py-2.5">指标</th>
                    <th className="whitespace-nowrap px-5 py-2.5 text-right">数值</th>
                  </tr>
                </thead>
                <tbody>
                  {INDICATORS.map((ind) => (
                    <tr key={ind.key} className="border-b border-border/50">
                      <td className="whitespace-nowrap px-5 py-2.5 text-muted-foreground">
                        {DIMENSIONS.find((d) => d.key === ind.dimension)?.label}
                      </td>
                      <td className="whitespace-nowrap px-5 py-2.5 text-foreground">{ind.label}</td>
                      <td className="whitespace-nowrap px-5 py-2.5 text-right font-medium text-primary">
                        {tool.indicators[ind.key]}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* 数据来源 */}
          <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
            <Database className="h-3.5 w-3.5" />
            <span>数据来源：{tool.dataSource} · 更新于 {tool.updatedAt}</span>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/compare">
              <Button variant="secondary">前往对比</Button>
            </Link>
            <Link to="/ranking">
              <Button variant="secondary">查看排行榜</Button>
            </Link>
          </div>
        </motion.div>
      </div>
    </MainLayout>
  );
};

export default ToolDetailPage;