import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        translation: {
          "appTitle": "Confidentiality Ruleset Inquiry Assistant",
          "language": "Language",
          "chinese": "Chinese",
          "english": "English",
          "searchPlaceholder": "Search rules...",
          "descriptionLabel": "Description:",
          "digitalManagementLabel": "Digital Asset Management:",
          "physicalManagementLabel": "Physical Asset Management:",
          "accessRightsLabel": "Access Rights:",
          "externalCommunicationLabel": "External Communication:",
          "lastUpdated": "Last Updated"
        }
      },
      zh: {
        translation: {
          "appTitle": "ADC資安看板",
          "lastUpdated": "更新日期",
          "language": "語言",
          "chinese": "中文",
          "english": "英文",
          "searchPlaceholder": "搜尋規範...",
          "descriptionLabel": "描述：",
          "digitalManagementLabel": "數位資產管理：",
          "physicalManagementLabel": "實體資產管理：",
          "accessRightsLabel": "存取權限：",
          "externalCommunicationLabel": "對外交流："
        }
      }
    },
    lng: "zh", // default language
    fallbackLng: "en",
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
