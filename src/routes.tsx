import HomePage from './pages/HomePage';
import SurveyPage from './pages/SurveyPage';
import ProfilePage from './pages/ProfilePage';
import TaskInputPage from './pages/TaskInputPage';
import ResultPage from './pages/ResultPage';
import RankingPage from './pages/RankingPage';
import ComparePage from './pages/ComparePage';
import ToolDetailPage from './pages/ToolDetailPage';

export const routes = [
  { path: '/', element: <HomePage /> },
  { path: '/survey', element: <SurveyPage /> },
  { path: '/profile', element: <ProfilePage /> },
  { path: '/task', element: <TaskInputPage /> },
  { path: '/result', element: <ResultPage /> },
  { path: '/ranking', element: <RankingPage /> },
  { path: '/compare', element: <ComparePage /> },
  { path: '/tool/:id', element: <ToolDetailPage /> },
];
