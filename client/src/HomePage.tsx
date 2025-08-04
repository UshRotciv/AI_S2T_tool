import React, { useState, useMemo, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import ScenarioCard from './ScenarioCard';
import ChatWindow from './ChatWindow';

interface Scenario {
  id: number;
  category: string;
  title: string;
  question: string;
  answer: string;
  learnings: string[];
  order?: number;
  groupId?: string | null;
}

const HomePage = () => {
  const { t, i18n } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const [scenarios, setScenarios] = useState<Scenario[]>([]);


  useEffect(() => {
    fetch('http://localhost:3001/api/scenarios')
      .then(res => res.json())
      .then(data => setScenarios(data?.data || []));
  }, []);

  const filteredScenarios = useMemo(() => {
    // 先按照 order 屬性排序場景
    const sortedScenarios = [...scenarios].sort((a, b) => {
      // 如果 order 都存在，按 order 排序
      if (a.order !== undefined && b.order !== undefined) {
        return a.order - b.order;
      }
      // 如果只有一個有 order，有 order 的優先
      if (a.order !== undefined) return -1;
      if (b.order !== undefined) return 1;
      // 都沒有 order，保持原順序
      return 0;
    });
    
    return sortedScenarios.filter(scenario => {
      const searchContent = (
        scenario.category +
        scenario.title +
        scenario.question +
        scenario.answer +
        scenario.learnings.join(' ')
      ).toLowerCase();
      return searchContent.includes(searchTerm.toLowerCase());
    });
  }, [searchTerm, scenarios]);

  const groupedScenarios = useMemo(() => {
    return filteredScenarios.reduce((acc, scenario) => {
      const { category } = scenario;
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(scenario);
      return acc;
    }, {} as Record<string, Scenario[]>);
  }, [filteredScenarios]);

  const categoryOrder = useMemo(() => [
    "Part A: 辦公室基礎好習慣 (Basic Office Habits)",
    "Part B: 數位檔案的溝通與傳遞 (Digital File Communication & Transfer)",
    "Part C: 機敏資料與高風險工具 (Sensitive Data & High-Risk Tools)",
    "Part D: 智慧財產與你的權責 (Intellectual Property & Your Responsibilities)"
  ], []);

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>{t('appTitle')}</h1>
        <div className="language-switcher">
          <label htmlFor="language-select">{t('language')}: </label>
          <select id="language-select" onChange={(e) => changeLanguage(e.target.value)} value={i18n.language}>
            <option value="zh">{t('chinese')}</option>
            <option value="en">{t('english')}</option>
          </select>
        </div>

      </header>
      <main>
        <ChatWindow />
        <div className="controls">
          <input
            type="text"
            placeholder={t('searchPlaceholder')}
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="rule-list">
          {categoryOrder.map(category => {
            const scenariosInCategory = groupedScenarios[category];
            if (!scenariosInCategory || scenariosInCategory.length === 0) {
              return null;
            }
            return (
              <div key={category}>
                <h2>{t(category, category)}</h2>
                {scenariosInCategory.map(scenario => (
                  <ScenarioCard key={scenario.id} scenario={scenario} />
                ))}
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}

export default HomePage;