import React from 'react';
import { Link } from 'react-router-dom';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

const STEPS = [
  { n: 1, label: '设定偏好', path: '/survey' },
  { n: 2, label: '偏好画像', path: '/profile' },
  { n: 3, label: '选择任务', path: '/task' },
  { n: 4, label: '推荐结果', path: '/result' },
];

interface Props {
  /** 当前所处步骤（1-4） */
  current: number;
  /** 已完成的步骤可点击回退 */
  reachable?: number;
}

/** 四步推荐流程的进度条，让用户随时知道自己在哪一步、还剩几步。 */
export const StepIndicator: React.FC<Props> = ({ current, reachable = current }) => {
  return (
    <nav aria-label="推荐流程进度" className="mx-auto mb-8 w-full max-w-2xl">
      <ol className="flex items-center">
        {STEPS.map((s, i) => {
          const done = s.n < current;
          const active = s.n === current;
          const canGo = s.n <= reachable && !active;

          const dot = (
            <span
              className={cn(
                'flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-xs font-semibold transition-all duration-300',
                active && 'border-transparent bg-gradient-primary text-primary-foreground glow-primary',
                done && 'border-primary/40 bg-primary/10 text-primary',
                !active && !done && 'border-border bg-card text-muted-foreground'
              )}
            >
              {done ? <Check className="h-4 w-4" /> : s.n}
            </span>
          );

          return (
            <li key={s.n} className={cn('flex items-center', i < STEPS.length - 1 && 'flex-1')}>
              <div className="flex flex-col items-center gap-1.5">
                {canGo ? (
                  <Link to={s.path} aria-label={`返回${s.label}`} className="rounded-full">
                    {dot}
                  </Link>
                ) : (
                  dot
                )}
                <span
                  className={cn(
                    'hidden text-[11px] transition-colors sm:block',
                    active ? 'font-medium text-foreground' : 'text-muted-foreground'
                  )}
                >
                  {s.label}
                </span>
              </div>

              {i < STEPS.length - 1 && (
                <div className="mx-2 -mt-5 h-px flex-1 overflow-hidden rounded bg-border">
                  <div
                    className="h-full bg-gradient-primary transition-all duration-500"
                    style={{ width: s.n < current ? '100%' : '0%' }}
                  />
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};
