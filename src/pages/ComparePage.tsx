import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { GitCompareArrows, Check, CheckCheck, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { MainLayout } from '@/components/layouts/MainLayout';
import { CapabilityRadar, buildRadarData } from '@/components/CapabilityRadar';
import { AI_TOOLS } from '@/lib/data';
import { getTopsisProfile } from '@/lib/engine';
import { useApp, MAX_COMPARE } from '@/contexts/AppContext';
import { INDICATORS, DIMENSIONS, type DimensionKey } from '@/lib/types';
import { cn } from '@/lib/utils';

/** 六条曲线的配色，需与库内模型数量对齐，保证同图可辨。 */
const COLORS = [
  'hsl(var(--chart-1))',
  'hsl(var(--chart-2))',
  'hsl(var(--chart-3))',
  'hsl(var(--chart-4))',
  'hsl(var(--chart-5))',
  'hsl(var(--chart-6))',
];

/** 取该行的最优值，用于在表格里高亮。isCost 表示越小越优。 */
function bestValue(values: number[], isCost: boolean): number {
  return isCost ? Math.min(...values) : Math.max(...values);
}

const ComparePage: React.FC = () => {
  const { compareIds, toggleCompare, clearCompare, selectAllCompare } = useApp();

  // 按 AI_TOOLS 的固定顺序渲染，保证颜色不会因选择顺序而跳动
  const selected = AI_TOOLS.filter((t) => compareIds.includes(t.id));
  const colorOf = (id: string) => COLORS[AI_TOOLS.findIndex((t) => t.id === id) % COLORS.length];

  const radarData = buildRadarData(
    selected.map((t) => ({ name: t.name, profile: getTopsisProfile(t.id), color: colorOf(t.id) }))
  );
  const series = selected.map((t) => ({ key: t.name, name: t.name, color: colorOf(t.id) }));

  const allSelected = compareIds.length >= Math.min(MAX_COMPARE, AI_TOOLS.length);

  return (
    <MainLayout>
      <div className="relative mx-auto max-w-6xl">
        <div className="orb -left-28 top-0 h-64 w-64 bg-primary/20 animate-drift" />
        <div className="orb -right-28 top-32 h-64 w-64 bg-accent/20 animate-drift [animation-delay:2.5s]" />

        <div className="relative">
          <div className="mb-6 text-center">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-xs font-medium text-accent">
              <GitCompareArrows className="h-3.5 w-3.5" /> 工具横向对比
            </div>
            <h1 className="text-balance text-2xl font-bold text-foreground md:text-3xl">
              <span className="gradient-text-animated">能力对比</span>
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              点选任意 2–{AI_TOOLS.length} 款模型进行多维能力对比，可一次对比全部
            </p>
          </div>

          {/* 模型选择器 */}
          <Card className="glass-card mb-4 p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <span className="text-xs text-muted-foreground">
                已选 <span className="num font-semibold text-foreground">{selected.length}</span> /{' '}
                {AI_TOOLS.length}
              </span>
              <div className="flex gap-1.5">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={selectAllCompare}
                  disabled={allSelected}
                  className="h-7 text-xs"
                >
                  <CheckCheck className="mr-1 h-3.5 w-3.5" /> 全选
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearCompare}
                  disabled={compareIds.length === 0}
                  className="h-7 text-xs"
                >
                  <RotateCcw className="mr-1 h-3.5 w-3.5" /> 清空
                </Button>
              </div>
            </div>

            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {AI_TOOLS.map((t) => {
                const on = compareIds.includes(t.id);
                const color = colorOf(t.id);
                return (
                  <button
                    key={t.id}
                    type="button"
                    role="checkbox"
                    aria-checked={on}
                    aria-label={t.name}
                    onClick={() => toggleCompare(t.id)}
                    className={cn(
                      'card-interactive flex items-center gap-2.5 rounded-xl border px-3 py-2.5 text-left',
                      on
                        ? 'border-primary/50 bg-primary/[0.07] shadow-card'
                        : 'border-border bg-card/70 hover:border-primary/40'
                    )}
                  >
                    {/* 色点：选中时填充，未选中时只描边，与雷达图曲线颜色一一对应 */}
                    <span
                      className="h-3 w-3 shrink-0 rounded-full border-2"
                      style={{
                        borderColor: color,
                        backgroundColor: on ? color : 'transparent',
                      }}
                    />
                    <span className="min-w-0 flex-1">
                      <span
                        className={cn(
                          'block truncate text-sm',
                          on ? 'font-semibold text-foreground' : 'text-muted-foreground'
                        )}
                      >
                        {t.name}
                      </span>
                      <span className="block truncate text-[11px] text-muted-foreground">
                        {t.company}
                      </span>
                    </span>
                    <span
                      className={cn(
                        'flex h-5 w-5 shrink-0 items-center justify-center rounded-md border transition-all',
                        on
                          ? 'border-transparent bg-gradient-primary text-primary-foreground'
                          : 'border-border bg-background'
                      )}
                    >
                      {on && <Check className="h-3.5 w-3.5" />}
                    </span>
                  </button>
                );
              })}
            </div>
          </Card>

          {selected.length < 2 ? (
            <Card className="glass-card p-12 text-center">
              <p className="text-sm text-muted-foreground">请至少选择 2 个工具进行对比</p>
              <Button
                className="mt-4 bg-gradient-primary text-primary-foreground hover:opacity-90"
                onClick={selectAllCompare}
              >
                <CheckCheck className="mr-1 h-4 w-4" /> 对比全部 {AI_TOOLS.length} 款
              </Button>
            </Card>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              {/* 雷达图对比 */}
              <Card className="glass-card p-5">
                <p className="mb-2 text-xs font-medium text-muted-foreground">七维能力对比</p>
                <CapabilityRadar data={radarData} series={series} height={400} />
              </Card>

              {/* 指标表格 */}
              <Card className="glass-card mt-4 overflow-hidden">
                <div className="w-full max-w-full overflow-x-auto bg-card">
                  <table className="w-full min-w-max text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-xs text-muted-foreground">
                        <th className="sticky left-0 z-10 whitespace-nowrap bg-card px-4 py-3">
                          指标
                        </th>
                        {selected.map((t) => (
                          <th key={t.id} className="whitespace-nowrap px-4 py-3 text-right">
                            <span className="inline-flex items-center gap-1.5">
                              <span
                                className="h-2 w-2 rounded-full"
                                style={{ backgroundColor: colorOf(t.id) }}
                              />
                              {t.name}
                            </span>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="bg-secondary/20">
                        <td
                          colSpan={selected.length + 1}
                          className="whitespace-nowrap px-4 py-2 text-xs font-semibold text-primary"
                        >
                          能力贴近度（TOPSIS）
                        </td>
                      </tr>
                      {DIMENSIONS.map((d) => {
                        const vals = selected.map(
                          (t) => getTopsisProfile(t.id)[d.key as DimensionKey] ?? 0
                        );
                        const best = bestValue(vals, false);
                        return (
                          <tr key={d.key} className="border-b border-border/50 hover:bg-primary/[0.03]">
                            <td className="sticky left-0 z-10 whitespace-nowrap bg-card px-4 py-2 text-muted-foreground">
                              {d.label}
                            </td>
                            {selected.map((t, i) => (
                              <td
                                key={t.id}
                                className={cn(
                                  'num whitespace-nowrap px-4 py-2 text-right',
                                  vals[i] === best
                                    ? 'font-bold text-primary'
                                    : 'font-medium text-foreground'
                                )}
                              >
                                {vals[i].toFixed(2)}
                              </td>
                            ))}
                          </tr>
                        );
                      })}

                      <tr className="bg-secondary/20">
                        <td
                          colSpan={selected.length + 1}
                          className="whitespace-nowrap px-4 py-2 text-xs font-semibold text-primary"
                        >
                          原始 Benchmark 指标
                        </td>
                      </tr>
                      {INDICATORS.map((ind) => {
                        const vals = selected.map((t) => t.indicators[ind.key]);
                        const best = bestValue(vals, ind.isCost);
                        return (
                          <tr
                            key={ind.key}
                            className="border-b border-border/50 hover:bg-primary/[0.03]"
                          >
                            <td className="sticky left-0 z-10 whitespace-nowrap bg-card px-4 py-2 text-muted-foreground">
                              {ind.label}
                            </td>
                            {selected.map((t, i) => (
                              <td
                                key={t.id}
                                className={cn(
                                  'num whitespace-nowrap px-4 py-2 text-right',
                                  vals[i] === best ? 'font-bold text-primary' : 'text-foreground'
                                )}
                              >
                                {vals[i]}
                              </td>
                            ))}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <p className="border-t border-border/50 px-4 py-2 text-[11px] text-muted-foreground">
                  加粗高亮为该行最优值（成本类指标越小越优）
                </p>
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
      </div>
    </MainLayout>
  );
};

export default ComparePage;
