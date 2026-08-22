import type { ReactNode } from 'react';
import HomePage from './pages/HomePage';
import SurveyPage from './pages/SurveyPage';
import ProfilePage from './pages/ProfilePage';
import TaskInputPage from './pages/TaskInputPage';
import ResultPage from './pages/ResultPage';
import RankingPage from './pages/RankingPage';
import ComparePage from './pages/ComparePage';
import ToolDetailPage from './pages/ToolDetailPage';

export interface RouteConfig {
  name: string;
  path: string;
  element: ReactNode;
  visible?: boolean;
  /** Accessible without login. Routes without this flag require authentication. Has no effect when RouteGuard is not in use. */
  public?: boolean;
}

export const routes: RouteConfig[] = [
  { name: '首页', path: '/', element: <HomePage />, public: true },
  { name: '偏好问卷', path: '/survey', element: <SurveyPage />, public: true },
  { name: '偏好画像', path: '/profile', element: <ProfilePage />, public: true },
  { name: '任务输入', path: '/task', element: <TaskInputPage />, public: true },
  { name: '推荐结果', path: '/result', element: <ResultPage />, public: true },
  { name: '排行榜', path: '/ranking', element: <RankingPage />, public: true },
  { name: '工具对比', path: '/compare', element: <ComparePage />, public: true },
  { name: '工具详情', path: '/tool/:id', element: <ToolDetailPage />, public: true },
];
