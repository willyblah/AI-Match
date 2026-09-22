import React, { useCallback, useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';

const STORAGE_KEY = 'ai-match:bg-theme';

type ThemeId = 'light' | 'dark';

const THEMES: { id: ThemeId; label: string; icon: React.FC<{ className?: string }> }[] = [
  { id: 'light', label: '浅色', icon: Sun },
  { id: 'dark', label: '深色', icon: Moon },
];

const DarkDots: React.FC = () => <div className="dark-dots" aria-hidden="true" />;

export const ThemeSwitcher: React.FC = () => {
  const [theme, setTheme] = useState<ThemeId>('light');

  useEffect(() => {
    if (localStorage.getItem(STORAGE_KEY) === 'dark') setTheme('dark');
  }, []);

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

  useEffect(() => () => document.documentElement.removeAttribute('data-theme'), []);

  const cycle = useCallback(() => {
    setTheme((current) => (current === 'light' ? 'dark' : 'light'));
  }, []);

  const current = THEMES.find((item) => item.id === theme) ?? THEMES[0];
  const next = THEMES[(THEMES.findIndex((item) => item.id === theme) + 1) % THEMES.length];
  const Icon = current.icon;

  return (
    <>
      {theme === 'dark' && <DarkDots />}
      <button
        type="button"
        onClick={cycle}
        title={`Current theme: ${current.label}. Switch to ${next.label}.`}
        aria-label={`Switch theme. Current: ${current.label}. Next: ${next.label}.`}
        className="fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-full border border-border bg-card/90 py-2 pl-3.5 pr-3 text-xs font-medium text-foreground shadow-card backdrop-blur transition-all duration-300 hover:scale-105 hover:border-primary/50 active:scale-95"
      >
        <Icon className="h-3.5 w-3.5 text-primary" />
        <span className="hidden sm:inline">{current.label}</span>
        <span className="ml-0.5 flex items-center gap-1">
          {THEMES.map((item) => (
            <span
              key={item.id}
              className={
                item.id === theme
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
