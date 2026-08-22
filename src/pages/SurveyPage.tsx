import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import { ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { MainLayout } from '@/components/layouts/MainLayout';
import { SURVEY_QUESTIONS } from '@/lib/survey';
import { useApp } from '@/contexts/AppContext';

const SurveyPage: React.FC = () => {
  const navigate = useNavigate();
  const { setProfileFromAnswers } = useApp();
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});

  const question = SURVEY_QUESTIONS[current];
  const isLast = current === SURVEY_QUESTIONS.length - 1;
  const progress = ((current + 1) / SURVEY_QUESTIONS.length) * 100;

  const isAnswered = () => {
    const a = answers[question.id];
    if (question.type === 'multi') return Array.isArray(a) && a.length > 0;
    return !!a;
  };

  const handleSelect = (value: string) => {
    if (question.type === 'multi') {
      const prev = Array.isArray(answers[question.id]) ? (answers[question.id] as string[]) : [];
      const next = prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value];
      setAnswers((s) => ({ ...s, [question.id]: next }));
    } else {
      setAnswers((s) => ({ ...s, [question.id]: value }));
    }
  };

  const isSelected = (value: string) => {
    const a = answers[question.id];
    if (question.type === 'multi') return Array.isArray(a) && a.includes(value);
    return a === value;
  };

  const handleNext = () => {
    if (isLast) {
      setProfileFromAnswers(answers);
      navigate('/profile');
    } else {
      setCurrent((c) => c + 1);
    }
  };

  const handlePrev = () => {
    if (current > 0) setCurrent((c) => c - 1);
  };

  return (
    <MainLayout>
      <div className="mx-auto max-w-2xl">
        {/* 进度 */}
        <div className="mb-6">
          <div className="mb-2 flex items-center justify-between text-xs text-muted-foreground">
            <span>
              第 {current + 1} / {SURVEY_QUESTIONS.length} 题
            </span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
            <motion.div
              className="h-full rounded-full bg-gradient-primary"
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.4 }}
            />
          </div>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={question.id}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            transition={{ duration: 0.25 }}
          >
            <Card className="glass-card p-6 md:p-8">
              <h2 className="text-balance text-xl font-bold text-foreground md:text-2xl">
                {question.title}
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">{question.subtitle}</p>

              <div className="mt-6 grid gap-3">
                {question.options.map((opt) => {
                  const selected = isSelected(opt.value);
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => handleSelect(opt.value)}
                      className={cn(
                        'flex items-center justify-between gap-3 rounded-xl border p-4 text-left transition-all',
                        selected
                          ? 'border-primary bg-primary/10 glow-primary'
                          : 'border-border bg-background/40 hover:border-primary/40 hover:bg-secondary/50'
                      )}
                    >
                      <span
                        className={cn(
                          'text-sm font-medium',
                          selected ? 'text-foreground' : 'text-muted-foreground'
                        )}
                      >
                        {opt.label}
                      </span>
                      <div
                        className={cn(
                          'flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition-colors',
                          selected ? 'border-primary bg-primary text-primary-foreground' : 'border-border'
                        )}
                      >
                        {selected && <Check className="h-3 w-3" />}
                      </div>
                    </button>
                  );
                })}
              </div>
            </Card>
          </motion.div>
        </AnimatePresence>

        {/* 导航 */}
        <div className="mt-6 flex items-center justify-between">
          <Button variant="ghost" onClick={handlePrev} disabled={current === 0}>
            <ChevronLeft className="mr-1 h-4 w-4" /> 上一题
          </Button>
          <Button
            onClick={handleNext}
            disabled={!isAnswered()}
            className="bg-gradient-primary text-primary-foreground hover:opacity-90"
          >
            {isLast ? '生成偏好画像' : '下一题'}
            {!isLast && <ChevronRight className="ml-1 h-4 w-4" />}
          </Button>
        </div>
      </div>
    </MainLayout>
  );
};

export default SurveyPage;