import React from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, AlertTriangle, DollarSign, Zap, TrendingUp } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CapabilityRadar, buildRadarData } from '@/components/CapabilityRadar';
import type { Recommendation } from '@/lib/types';

interface Props {
  rec: Recommendation;
  rank: number;
}

export const RecommendationCard: React.FC<Props> = ({ rec, rank }) => {
  const { tool, topsis, matchScore, cost, monthlyCost, affordable, advantages, reason } = rec;
  const radarData = buildRadarData([{ name: '能力', profile: topsis, color: 'hsl(var(--chart-1))' }]);

  return (
    <Card className="glass-card overflow-hidden">
      {/* 头部 */}
      <div className="flex items-start justify-between gap-3 border-b border-border/50 p-5">
        <div className="flex min-w-0 items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/15 text-sm font-bold text-primary">
            #{rank}
          </div>
          <div className="min-w-0">
            <h3 className="truncate text-lg font-bold text-foreground">{tool.name}</h3>
            <p className="truncate text-xs text-muted-foreground">
              {tool.company} · {tool.version}
            </p>
          </div>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-2xl font-bold gradient-text">{matchScore}%</div>
          <p className="text-[10px] text-muted-foreground">匹配度</p>
        </div>
      </div>

      <div className="grid gap-4 p-5 md:grid-cols-2">
        {/* 雷达图 */}
        <div>
          <p className="mb-1 text-xs font-medium text-muted-foreground">七维能力画像</p>
          <CapabilityRadar data={radarData} series={[{ key: '能力', name: tool.name, color: 'hsl(var(--chart-1))' }]} height={220} showLegend={false} />
        </div>

        {/* 详情 */}
        <div className="flex flex-col gap-3">
          {/* 优势标签 */}
          <div className="flex flex-wrap gap-1.5">
            {advantages.map((a) => (
              <Badge key={a} variant="secondary" className="border border-primary/30 bg-primary/10 text-primary">
                {a}
              </Badge>
            ))}
          </div>

          {/* 成本 */}
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-lg bg-secondary/50 p-2.5">
              <p className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <DollarSign className="h-3 w-3" /> 单次成本
              </p>
              <p className="text-sm font-semibold text-foreground">${cost.toFixed(2)}</p>
            </div>
            <div className="rounded-lg bg-secondary/50 p-2.5">
              <p className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <TrendingUp className="h-3 w-3" /> 月度成本
              </p>
              <p className="text-sm font-semibold text-foreground">${monthlyCost.toFixed(2)}</p>
            </div>
          </div>

          {/* 预算状态 */}
          <div
            className={`flex items-center gap-1.5 rounded-lg p-2 text-xs ${
              affordable ? 'bg-chart-5/15 text-chart-5' : 'bg-destructive/15 text-destructive'
            }`}
          >
            {affordable ? <CheckCircle2 className="h-3.5 w-3.5" /> : <AlertTriangle className="h-3.5 w-3.5" />}
            <span>{affordable ? '在预算范围内' : '略超当前预算'}</span>
          </div>

          {/* 推荐理由 */}
          <div className="rounded-lg border border-border/50 bg-background/40 p-3">
            <p className="mb-1 flex items-center gap-1 text-xs font-medium text-accent">
              <Zap className="h-3 w-3" /> 为什么推荐
            </p>
            <p className="text-xs leading-relaxed text-muted-foreground">{reason}</p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-end gap-2 border-t border-border/50 p-4">
        <Link to={`/tool/${tool.id}`}>
          <Button variant="secondary" size="sm">
            查看详情
          </Button>
        </Link>
      </div>
    </Card>
  );
};