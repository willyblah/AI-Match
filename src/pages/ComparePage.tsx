import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { GitCompareArrows, X, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MainLayout } from '@/components/layouts/MainLayout';
import { CapabilityRadar, buildRadarData } from '@/components/CapabilityRadar';
import { AI_TOOLS } from '@/lib/data';
import { getTopsisProfile } from '@/lib/engine';
import { useApp } from '@/contexts/AppContext';
import { INDICATORS, DIMENSIONS, type DimensionKey } from '@/lib/types';

const COLORS = [
  'hsl(var(--chart-1))',
  'hsl(var(--chart-2))',
  'hsl(var(--chart-3))',
  'hsl(var(--chart-4))',
];

const ComparePage: React.FC = () => {
  const { compareIds, toggleCompare, clearCompare } = useApp();

  const selected = AI_TOOLS.filter((t) => compareIds.includes(t.id));
  const radarData = buildRadarData(
    selected.map((t, i) => ({ name: t.name, profile: getTopsisProfile(t.id), color: COLORS[i % COLORS.length] }))
  );

  const series = selected.map((t, i) => ({ key: t.name, name: t.name, color: COLORS[i % COLORS.length] }));
  const remaining = AI_TOOLS.filter((t) => !compareIds.includes(t.id));

  return (
    <MainLayout>
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 text-center">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-xs font-medium text-accent">
            <GitCompareArrows className="h-3.5 w-3.5" /> 工具横向对比
          </div>
          <h1 className="text-balance text-2xl font-bold text-foreground md:text-3xl">能力对比</h1>
          <p className="mt-2 text-sm text-muted-foreground">选择 2-4 个 AI 工具进行多维能力对比</p>
        </div>

        {/* 已选工具 */}
        <div className="mb-4 flex flex-wrap items-center gap-2">
          {selected.map((t) => (
            <Badge key={t.id} variant="secondary" className="gap-1 border border-primary/30 bg-primary/10 py-1 pl-3 pr-1 text-primary">
              {t.name}
              <button type="button" onClick={() => toggleCompare(t.id)} className="ml-1 rounded-full p-0.5 hover:bg-primary/20">
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          {compareIds.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clearCompare} className="h-7 text-xs text-muted-foreground">
              清空
            </Button>
          )}
        </div>

        {/* 添加工具 */}
        {compareIds.length < 4 && (
          <div className="mb-6 flex flex-wrap gap-2">
            {remaining.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => toggleCompare(t.id)}
                className="inline-flex items-center gap-1 rounded-lg border border-border bg-background/40 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
              >
                <Plus className="h-3 w-3" /> {t.name}
              </button>
            ))}
          </div>
        )}

        {selected.length < 2 ? (
          <Card className="glass-card p-12 text-center">
            <p className="text-sm text-muted-foreground">请至少选择 2 个工具进行对比</p>
          </Card>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {/* 雷达图对比 */}
            <Card className="glass-card p-5">
              <p className="mb-2 text-xs font-medium text-muted-foreground">七维能力对比</p>
              <CapabilityRadar data={radarData} series={series} height={360} />
            </Card>

            {/* 指标表格 */}
            <Card className="glass-card mt-4 overflow-hidden">
              <div className="w-full max-w-full overflow-x-auto bg-card">
                <table className="w-full min-w-max text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs text-muted-foreground">
                      <th className="whitespace-nowrap px-4 py-3">指标</th>
                      {selected.map((t) => (
                        <th key={t.id} className="whitespace-nowrap px-4 py-3 text-right">{t.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {/* 能力贴近度 */}
                    <tr className="bg-secondary/20">
                      <td colSpan={selected.length + 1} className="whitespace-nowrap px-4 py-2 text-xs font-semibold text-primary">
                        能力贴近度（TOPSIS）
                      </td>
                    </tr>
                    {DIMENSIONS.map((d) => (
                      <tr key={d.key} className="border-b border-border/50">
                        <td className="whitespace-nowrap px-4 py-2 text-muted-foreground">{d.label}</td>
                        {selected.map((t) => {
                          const v = getTopsisProfile(t.id)[d.key as DimensionKey] ?? 0;
                          return (
                            <td key={t.id} className="whitespace-nowrap px-4 py-2 text-right font-medium text-foreground">
                              {v.toFixed(2)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                    {/* 原始指标 */}
                    <tr className="bg-secondary/20">
                      <td colSpan={selected.length + 1} className="whitespace-nowrap px-4 py-2 text-xs font-semibold text-primary">
                        原始 Benchmark 指标
                      </td>
                    </tr>
                    {INDICATORS.map((ind) => (
                      <tr key={ind.key} className="border-b border-border/50">
                        <td className="whitespace-nowrap px-4 py-2 text-muted-foreground">{ind.label}</td>
                        {selected.map((t) => (
                          <td key={t.id} className="whitespace-nowrap px-4 py-2 text-right text-foreground">
                            {t.indicators[ind.key]}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* 详情链接 */}
            <div className="mt-4 flex flex-wrap gap-2">
              {selected.map((t) => (
                <Link key={t.id} to={`/tool/${t.id}`}>
                  <Button variant="secondary" size="sm">
                    {t.name} 详情
                  </Button>
                </Link>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </MainLayout>
  );
};

export default ComparePage;