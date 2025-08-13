
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Card,
  CardContent,
  Typography,
  Chip,
  Box,
  Modal,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Divider,
  Fade
} from '@mui/material';
import {
  Security as SecurityIcon,
  Close as CloseIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';

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

interface ScenarioCardProps {
  scenario: Scenario;
  onCardClick?: (scenario: Scenario) => void;
}

const ScenarioCard: React.FC<ScenarioCardProps> = ({ scenario, onCardClick }) => {
  const { t } = useTranslation();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const handleCardClick = () => {
    if (onCardClick) {
      onCardClick(scenario);
    } else {
      setIsModalOpen(true);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  // 獲取分類的簡短名稱
  const getCategoryShort = (category: string) => {
    if (category.includes('Part A')) return 'A: 基礎習慣';
    if (category.includes('Part B')) return 'B: 檔案傳遞';
    if (category.includes('Part C')) return 'C: 機敏資料';
    if (category.includes('Part D')) return 'D: 智慧財產';
    return category;
  };

  // 獲取分類顏色
  const getCategoryColor = (category: string) => {
    if (category.includes('Part A')) return '#2196F3'; // 藍色
    if (category.includes('Part B')) return '#4CAF50'; // 綠色
    if (category.includes('Part C')) return '#FF9800'; // 橙色
    if (category.includes('Part D')) return '#9C27B0'; // 紫色
    return '#757575'; // 灰色
  };

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        whileHover={{ y: -4 }}
        onHoverStart={() => setIsHovered(true)}
        onHoverEnd={() => setIsHovered(false)}
      >
        <Card
          onClick={handleCardClick}
          sx={{
            cursor: 'pointer',
            borderRadius: 3,
            border: 'none',
            boxShadow: isHovered 
              ? '0 12px 24px rgba(0,0,0,0.15)' 
              : '0 2px 8px rgba(0,0,0,0.1)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            backgroundColor: '#ffffff',
            overflow: 'visible',
            position: 'relative',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: '0 12px 24px rgba(0,0,0,0.15)',
            }
          }}
        >
          <CardContent sx={{ p: 3 }}>
            {/* 分類標籤 */}
            <Box sx={{ mb: 2 }}>
              <Chip
                label={getCategoryShort(scenario.category)}
                size="small"
                sx={{
                  backgroundColor: getCategoryColor(scenario.category),
                  color: 'white',
                  fontWeight: 600,
                  fontSize: '0.75rem'
                }}
              />
            </Box>

            {/* 標題 */}
            <Typography
              variant="h6"
              component="h3"
              sx={{
                fontWeight: 600,
                fontSize: '1.1rem',
                lineHeight: 1.4,
                color: '#1a1a1a',
                mb: 2,
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden'
              }}
            >
              {scenario.title}
            </Typography>

            {/* 問題預覽 */}
            <Typography
              variant="body2"
              sx={{
                color: '#666',
                lineHeight: 1.5,
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
                mb: 2
              }}
            >
              {scenario.question}
            </Typography>

            {/* 底部區域 */}
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                mt: 'auto'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SecurityIcon sx={{ fontSize: 16, color: '#999' }} />
                <Typography variant="caption" sx={{ color: '#999' }}>
                  {t('clickToView', '點擊查看詳情')}
                </Typography>
              </Box>
              
              {isHovered && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <ArrowForwardIcon sx={{ fontSize: 18, color: getCategoryColor(scenario.category) }} />
                </motion.div>
              )}
            </Box>
          </CardContent>
        </Card>
      </motion.div>

      {/* 詳細內容 Modal */}
      <Modal
        open={isModalOpen}
        onClose={handleCloseModal}
        closeAfterTransition
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 2
        }}
      >
        <Fade in={isModalOpen}>
          <Box
            sx={{
              backgroundColor: 'white',
              borderRadius: 3,
              boxShadow: '0 24px 48px rgba(0,0,0,0.2)',
              maxWidth: '800px',
              maxHeight: '90vh',
              overflow: 'auto',
              position: 'relative',
              outline: 'none'
            }}
          >
            {/* Modal Header */}
            <Box
              sx={{
                p: 3,
                borderBottom: '1px solid #f0f0f0',
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between'
              }}
            >
              <Box sx={{ flex: 1, pr: 2 }}>
                <Chip
                  label={getCategoryShort(scenario.category)}
                  size="small"
                  sx={{
                    backgroundColor: getCategoryColor(scenario.category),
                    color: 'white',
                    fontWeight: 600,
                    mb: 2
                  }}
                />
                <Typography variant="h5" component="h2" sx={{ fontWeight: 600, color: '#1a1a1a' }}>
                  {scenario.title}
                </Typography>
              </Box>
              <IconButton onClick={handleCloseModal} sx={{ color: '#666' }}>
                <CloseIcon />
              </IconButton>
            </Box>

            {/* Modal Content */}
            <Box sx={{ p: 3 }}>
              {/* 問題 */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: '#333' }}>
                  {t('questionLabel', '情境問題')}
                </Typography>
                <Typography variant="body1" sx={{ lineHeight: 1.6, color: '#555' }}>
                  {scenario.question}
                </Typography>
              </Box>

              <Divider sx={{ my: 3 }} />

              {/* 解答 */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: '#333' }}>
                  {t('answerLabel', '解答')}
                </Typography>
                <Typography variant="body1" sx={{ lineHeight: 1.6, color: '#555' }}>
                  {scenario.answer}
                </Typography>
              </Box>

              <Divider sx={{ my: 3 }} />

              {/* 學習重點 */}
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: '#333' }}>
                  {t('learningsLabel', '學習重點')}
                </Typography>
                <List sx={{ p: 0 }}>
                  {scenario.learnings.map((item, index) => (
                    item.trim() !== '' && (
                      <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                        <ListItemText
                          primary={item.trim()}
                          sx={{
                            '& .MuiListItemText-primary': {
                              fontSize: '0.95rem',
                              lineHeight: 1.6,
                              color: '#555'
                            }
                          }}
                        />
                      </ListItem>
                    )
                  ))}
                </List>
              </Box>
            </Box>
          </Box>
        </Fade>
      </Modal>
    </>
  );
};

export default ScenarioCard;
