import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sparkles, Menu, Trophy, GitCompareArrows, LayoutDashboard } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from '@/components/ui/sheet';
import { cn } from '@/lib/utils';
// 背景主题切换器（试验性，可整体移除，见该文件顶部注释）
import { ThemeSwitcher } from '@/components/ThemeSwitcher';

const NAV = [
  { label: '首页', path: '/', icon: LayoutDashboard },
  { label: '排行榜', path: '/ranking', icon: Trophy },
  { label: '工具对比', path: '/compare', icon: GitCompareArrows },
];

export const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const [open, setOpen] = useState(false);

  const isActive = (path: string) =>
    path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);

  const NavItems = ({ onClick }: { onClick?: () => void }) => (
    <>
      {NAV.map((item) => {
        const Icon = item.icon;
        return (
          <Link
            key={item.path}
            to={item.path}
            onClick={onClick}
            className={cn(
              'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              isActive(item.path)
                ? 'bg-primary/15 text-primary'
                : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </>
  );

  return (
    <div className="flex min-h-screen w-full flex-col bg-background">
      {/* 背景主题切换器（试验性，可整体移除） */}
      <ThemeSwitcher />
      {/* 顶部导航 */}
      <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-4 md:px-6">
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-primary glow-primary">
              <Sparkles className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-lg font-bold gradient-text">AI Match</span>
          </Link>

          <nav className="hidden items-center gap-1 md:flex">
            <NavItems />
          </nav>

          <div className="hidden md:block">
            <Link to="/survey">
              <Button className="bg-gradient-primary text-primary-foreground hover:opacity-90">
                开始智能推荐
              </Button>
            </Link>
          </div>

          {/* 移动端菜单 */}
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="md:hidden">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72 bg-sidebar">
              <SheetTitle className="gradient-text text-lg">AI Match</SheetTitle>
              <div className="mt-6 flex flex-col gap-2">
                <NavItems onClick={() => setOpen(false)} />
                <Link to="/survey" onClick={() => setOpen(false)}>
                  <Button className="mt-4 w-full bg-gradient-primary text-primary-foreground hover:opacity-90">
                    开始智能推荐
                  </Button>
                </Link>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </header>

      {/* 主内容 */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 md:px-6 md:py-8">{children}</main>

      {/* 页脚 */}
      <footer className="border-t border-border py-6">
        <div className="mx-auto w-full max-w-7xl px-4 text-center text-xs text-muted-foreground md:px-6">
          <div>AI Match · 基于熵权-TOPSIS 与 AHP 层次分析法的 AI 工具智能推荐平台</div>
          {/* Artificial Analysis 数据 API 要求所有使用方标注来源，请勿移除。 */}
          <div className="mt-1.5">
            基准数据来源{' '}
            <a
              href="https://artificialanalysis.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="underline underline-offset-2 transition-colors hover:text-foreground"
            >
              Artificial Analysis
            </a>{' '}
            与{' '}
            <a
              href="https://livebench.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="underline underline-offset-2 transition-colors hover:text-foreground"
            >
              LiveBench
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};