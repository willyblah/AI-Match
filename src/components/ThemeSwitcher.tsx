/* ═══════════════════════════════════════════════════════════════════════
   背景主题切换器 —— 试验性功能，可整体移除

   一个按钮循环切换四种背景：
     浅色（默认）
       → Cyber（深蓝紫 + 霓虹漂浮光球）
       → Circuit（深海军蓝 + 六边形电路晶格 + 呼吸脉冲）
       → Minimal（深蓝灰 + 极简点阵，克制专业）
       → 回到浅色

   如果都不喜欢：

   1) 临时关闭：点右下角按钮切回「浅色」即可，选择记在 localStorage。
   2) 彻底删除（三步，约 30 秒）：
        a. 删除本文件 src/components/ThemeSwitcher.tsx
        b. 在 src/components/layouts/MainLayout.tsx 里删掉
           `import { ThemeSwitcher }` 和 `<ThemeSwitcher />` 两行
        c. 在 src/index.css 里删掉标有
           「▼▼▼ 背景主题（试验性）」到「▲▲▲ 背景主题结束」之间的整段
        d.（可选）删掉 index.html <head> 里那段防闪白的 inline script；
           留着也无副作用，因为没有对应 CSS 时 data-theme 不产生任何效果

   删除后默认浅色主题完全不受影响——所有样式都限定在
   [data-theme='cyber'] / [data-theme='circuit'] / [data-theme='minimal']
   选择器下，不会污染原有样式。

   若只想删掉其中一个主题，把对应的 THEMES 条目和 index.css 里对应的小节删掉即可。
   ═══════════════════════════════════════════════════════════════════════ */

import React, { useCallback, useEffect, useState } from 'react';
import { Sun, Sparkles, CircuitBoard, Grid2x2 } from 'lucide-react';

const STORAGE_KEY = 'ai-match:bg-theme';

type ThemeId = 'light' | 'cyber' | 'circuit' | 'minimal';

const THEMES: { id: ThemeId; label: string; icon: React.FC<{ className?: string }> }[] = [
  { id: 'light', label: '浅色', icon: Sun },
  { id: 'cyber', label: 'Cyber', icon: Sparkles },
  { id: 'circuit', label: 'Circuit', icon: CircuitBoard },
  { id: 'minimal', label: 'Minimal', icon: Grid2x2 },
];

/** Cyber 主题的漂浮霓虹光球。纯装饰，不拦截任何点击。 */
const ORBS = [
  { color: 'hsl(187 100% 56%)', size: 30, top: '6%', left: '4%', anim: 'orb-a', dur: 22, delay: 0 },
  { color: 'hsl(315 100% 64%)', size: 26, top: '52%', left: '78%', anim: 'orb-b', dur: 26, delay: 2 },
  { color: 'hsl(265 95% 68%)', size: 34, top: '68%', left: '12%', anim: 'orb-a', dur: 30, delay: 5 },
  { color: 'hsl(187 100% 60%)', size: 20, top: '18%', left: '62%', anim: 'orb-b', dur: 19, delay: 1 },
  { color: 'hsl(315 100% 60%)', size: 22, top: '84%', left: '48%', anim: 'orb-a', dur: 34, delay: 7 },
];

const CyberOrbs: React.FC = () => (
  <div className="cyber-orbs" aria-hidden="true">
    {ORBS.map((o) => (
      <span
        key={`${o.top}-${o.left}`}
        className="cyber-orb"
        style={{
          background: o.color,
          width: `${o.size}vw`,
          height: `${o.size}vw`,
          top: o.top,
          left: o.left,
          animation: `${o.anim} ${o.dur}s ease-in-out ${o.delay}s infinite, orb-pulse ${o.dur / 2}s ease-in-out ${o.delay}s infinite`,
        }}
      />
    ))}
  </div>
);

/** Minimal 主题的漂移点阵层。 */
const MinimalDots: React.FC = () => <div className="minimal-dots" aria-hidden="true" />;

/** Circuit 主题的呼吸脉冲层与缓慢扫光。 */
const CircuitLayers: React.FC = () => (
  <div aria-hidden="true">
    <div className="circuit-pulse" />
    <div className="circuit-sweep" />
  </div>
);

export const ThemeSwitcher: React.FC = () => {
  const [theme, setTheme] = useState<ThemeId>('light');

  // 读取上次选择
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as ThemeId | null;
    if (saved && THEMES.some((t) => t.id === saved)) setTheme(saved);
  }, []);

  // 写到 <html data-theme>，CSS 据此切换；浅色为默认，不带属性。
  // 首帧由 index.html 里的 inline script 预先套用，避免刷新时闪一下浅色。
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'light') {
      root.removeAttribute('data-theme');
      localStorage.removeItem(STORAGE_KEY);
    } else {
      root.setAttribute('data-theme', theme);
      localStorage.setItem(STORAGE_KEY, theme);
    }
  }, [theme]);

  // 卸载时清掉属性，避免删除本组件后属性残留导致页面停在深色
  useEffect(() => {
    return () => document.documentElement.removeAttribute('data-theme');
  }, []);

  const cycle = useCallback(() => {
    setTheme((cur) => {
      const i = THEMES.findIndex((t) => t.id === cur);
      return THEMES[(i + 1) % THEMES.length].id;
    });
  }, []);

  const current = THEMES.find((t) => t.id === theme) ?? THEMES[0];
  const next = THEMES[(THEMES.findIndex((t) => t.id === theme) + 1) % THEMES.length];
  const Icon = current.icon;

  return (
    <>
      {theme === 'cyber' && <CyberOrbs />}
      {theme === 'circuit' && <CircuitLayers />}
      {theme === 'minimal' && <MinimalDots />}

      <button
        type="button"
        onClick={cycle}
        title={`当前背景：${current.label}，点击切换到 ${next.label}`}
        aria-label={`切换背景主题，当前 ${current.label}，下一个 ${next.label}`}
        className="fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-full border border-border bg-card/90 py-2 pl-3.5 pr-3 text-xs font-medium text-foreground shadow-card backdrop-blur transition-all duration-300 hover:scale-105 hover:border-primary/50 active:scale-95"
      >
        <Icon className="h-3.5 w-3.5 text-primary" />
        <span className="hidden sm:inline">{current.label}</span>
        {/* 小圆点指示当前处于哪一档，数量随 THEMES 自动变化 */}
        <span className="ml-0.5 flex items-center gap-1">
          {THEMES.map((t) => (
            <span
              key={t.id}
              className={
                t.id === theme
                  ? 'h-1.5 w-1.5 rounded-full bg-primary'
                  : 'h-1.5 w-1.5 rounded-full bg-muted-foreground/35'
              }
            />
          ))}
        </span>
      </button>
    </>
  );
};
