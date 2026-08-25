import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import {
  Sparkles,
  ArrowRight,
  BarChart3,
  Layers,
  RefreshCw,
  Target,
  BrainCircuit,
  ShieldCheck,
  FileText,
  Search,
  Code2,
  Presentation,
  Database,
  Bot,
  PenTool,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { MainLayout } from '@/components/layouts/MainLayout';
import { AI_TOOLS } from '@/lib/data';

const FEATURES = [
  {
    icon: BarChart3,
    title: '熵权-TOPSIS 能力画像',
    desc: '基于 7 大维度、16 项 Benchmark 指标，客观量化每个 AI 工具的分维度能力贴近度。',
  },
  {
    icon: BrainCircuit,
    title: '偏好权重建模',
    desc: '拖动滑块直接设定各维度偏好强度，系统自动归一化计算您的个性化偏好权重。',
  },
  {
    icon: Target,
    title: '任务级智能推荐',
    desc: '融合偏好权重 × 任务需求 × 能力画像 × 成本约束，推荐 Top 3 最优方案。',
  },
  {
    icon: RefreshCw,
    title: '数据实时更新',
    desc: '工具数据库与算法解耦，支持持续接入新 AI 工具与最新 Benchmark 数据。',
  },
];

const STEPS = [
  { step: '01', title: '设定偏好', desc: '拖动滑块设定各维度的偏好权重' },
  { step: '02', title: '生成偏好画像', desc: '系统归一化计算您的七维偏好权重' },
  { step: '03', title: '输入任务', desc: '选择任务类型并设置预算与频率' },
  { step: '04', title: '智能推荐', desc: '获得 Top 3 匹配方案与推荐理由' },
];

/* 首页展示的 AI 工具能力图标 */
const TOOL_ICONS = [
  { icon: PenTool, label: '论文写作' },
  { icon: FileText, label: '文献分析' },
  { icon: Database, label: '数据分析' },
  { icon: Code2, label: 'Python 编程' },
  { icon: Presentation, label: 'PPT 制作' },
  { icon: Search, label: '信息检索' },
  { icon: Bot, label: 'Agent 自动化' },
  { icon: BrainCircuit, label: '深度推理' },
];

const HomePage: React.FC = () => {
  return (
    <MainLayout>
      {/* Hero */}
      <section className="relative overflow-hidden py-12 md:py-20">
        <div className="orb -left-20 top-0 h-72 w-72 bg-primary/25 animate-drift" />
        <div className="orb -right-20 top-20 h-72 w-72 bg-accent/25 animate-drift [animation-delay:3s]" />
        <div className="orb left-1/3 top-40 h-56 w-56 bg-chart-3/20 animate-drift [animation-delay:1.5s]" />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative mx-auto max-w-3xl text-center"
        >
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-medium text-primary">
            <Sparkles className="h-3.5 w-3.5" />
            基于论文熵权-TOPSIS 与偏好权重建模
          </div>
          <h1 className="text-balance text-3xl font-bold leading-tight text-foreground md:text-5xl">
            让每一个任务 <span className="gradient-text-animated">找到最适合的 AI 工具</span>
          </h1>
          <p className="mx-auto mt-4 max-w-prose text-pretty text-sm text-muted-foreground md:text-base">
            无需复杂问卷，只需拖动滑块设定偏好权重并输入任务，AI Match 即可基于多维能力画像与成本约束，
            为你推荐 Top 3 最适合的 AI 工具方案。
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link to="/survey">
              <Button size="lg" className="w-full bg-gradient-primary text-primary-foreground hover:opacity-90 sm:w-auto">
                开始智能推荐 <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
            <Link to="/ranking">
              <Button size="lg" variant="secondary" className="w-full sm:w-auto">
                查看排行榜
              </Button>
            </Link>
          </div>

          {/* AI 工具能力图标 */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-10 grid grid-cols-4 gap-3 md:grid-cols-8"
          >
            {TOOL_ICONS.map((t) => {
              const Icon = t.icon;
              return (
                <div
                  key={t.label}
                  className="card-interactive flex flex-col items-center gap-2 rounded-xl border border-border bg-card/80 p-3 shadow-card"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="text-center text-[11px] leading-tight text-muted-foreground">
                    {t.label}
                  </span>
                </div>
              );
            })}
          </motion.div>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-primary" />
              已收录 {AI_TOOLS.length} 款主流 AI 工具
            </span>
            <span className="flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-primary" />
              7 大能力维度 · 16 项 Benchmark
            </span>
          </div>
        </motion.div>
      </section>

      {/* 流程 */}
      <section className="py-8 md:py-12">
        <div className="mb-8 text-center">
          <h2 className="text-balance text-xl font-bold text-foreground md:text-2xl">四步完成智能推荐</h2>
          <p className="mt-2 text-sm text-muted-foreground">从测试到推荐，全流程数据驱动</p>
        </div>
        <div className="grid gap-4 md:grid-cols-4">
          {STEPS.map((s, i) => (
            <motion.div
              key={s.step}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <Card className="glass-card card-interactive relative h-full overflow-hidden p-5">
                <div className="num mb-3 text-2xl font-bold gradient-text">{s.step}</div>
                <h3 className="mb-1 text-sm font-semibold text-foreground">{s.title}</h3>
                <p className="text-xs text-muted-foreground">{s.desc}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* 特性 */}
      <section className="py-8 md:py-12">
        <div className="mb-8 text-center">
          <h2 className="text-balance text-xl font-bold text-foreground md:text-2xl">核心能力</h2>
          <p className="mt-2 text-sm text-muted-foreground">严谨的数学建模，让推荐有理可依</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {FEATURES.map((f) => {
            const Icon = f.icon;
            return (
              <Card key={f.title} className="glass-card card-interactive flex h-full gap-4 p-5">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/15 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <h3 className="mb-1 text-sm font-semibold text-foreground">{f.title}</h3>
                  <p className="text-xs leading-relaxed text-muted-foreground">{f.desc}</p>
                </div>
              </Card>
            );
          })}
        </div>
      </section>

      {/* CTA */}
      <section className="py-8 md:py-12">
        <Card className="glass-card relative overflow-hidden p-8 text-center md:p-12">
          <div className="pointer-events-none absolute inset-0 bg-gradient-primary opacity-5" />
          <div className="relative">
            <h2 className="text-balance text-xl font-bold text-foreground md:text-2xl">
              现在就开始，找到你的最优 AI 方案
            </h2>
            <p className="mx-auto mt-3 max-w-prose text-sm text-muted-foreground">
              拖动滑块设定偏好权重，仅需一分钟，即可获得专属 AI 工具推荐。
            </p>
            <Link to="/survey" className="mt-6 inline-block">
              <Button size="lg" className="bg-gradient-primary text-primary-foreground hover:opacity-90">
                立即测试 <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </Card>
      </section>
    </MainLayout>
  );
};

export default HomePage;