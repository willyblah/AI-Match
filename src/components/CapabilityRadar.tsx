import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import type { TopsisProfile } from '@/lib/types';
import { DIMENSIONS } from '@/lib/types';

interface Props {
  data: Array<Record<string, string | number>>;
  series: { key: string; name: string; color: string }[];
  height?: number;
  showLegend?: boolean;
}

export const CapabilityRadar: React.FC<Props> = ({ data, series, height = 300, showLegend = true }) => {
  return (
    <div className="w-full min-w-0 overflow-hidden" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="72%">
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis
            dataKey="label"
            tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 1]}
            tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
            tickCount={5}
          />
          {series.map((s) => (
            <Radar
              key={s.key}
              name={s.name}
              dataKey={s.key}
              stroke={s.color}
              fill={s.color}
              fillOpacity={0.2}
              strokeWidth={2}
            />
          ))}
          {showLegend && (
            <Legend
              layout="horizontal"
              wrapperStyle={{ paddingTop: 8, fontSize: 12, color: 'hsl(var(--muted-foreground))' }}
            />
          )}
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

// 将 TopsisProfile 转换为雷达图数据
export function buildRadarData(profiles: { name: string; profile: TopsisProfile; color: string }[]): Record<string, string | number>[] {
  return DIMENSIONS.map((d) => {
    const row: Record<string, string | number> = { label: d.shortLabel };
    for (const p of profiles) {
      row[p.name] = Number((p.profile[d.key] ?? 0).toFixed(2));
    }
    return row;
  });
}