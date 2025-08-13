
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

interface Scenario {
  id: number;
  category: string;
  title: string;
  question: string;
  answer: string;
  learnings: string[];
}

const ScenarioCard: React.FC<{ scenario: Scenario }> = ({ scenario }) => {
  const { t } = useTranslation();
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div className="rule-card" onClick={toggleExpanded}>
      <h3>{scenario.title}</h3>
      {isExpanded && (
        <>
          <p><span className="label">{t('categoryLabel')}</span> {scenario.category}</p>
          <p><span className="label">{t('questionLabel')}</span> {scenario.question}</p>
          <p><span className="label">{t('answerLabel')}</span> {scenario.answer}</p>
          <p><span className="label">{t('learningsLabel')}</span></p>
          <ul>
            {scenario.learnings.map((item, index) => (
              item.trim() !== '' && <li key={index}>{item.trim()}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
};

export default ScenarioCard;
