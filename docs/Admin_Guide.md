# 管理後台使用與開發指南
_版本: 1.0.0 | 最後更新: 2025-08-04_

本文檔詳細說明管理後台的使用方法、開發指南、以及已修復的問題與優化方向。管理後台是本系統的核心操作介面，負責卡片內容與群組的維護管理。

## 1. 管理後台功能介紹

管理後台提供完整的內容管理功能，包括卡片的創建、編輯、刪除及分類整理：

### 1.1 主要功能列表

- **卡片管理**：創建、編輯、刪除資安情境卡片
- **群組管理**：創建、編輯、刪除卡片群組
- **卡片排序**：調整卡片在群組內的顯示順序
- **群組排序**：調整群組自身的顯示順序
- **卡片分類**：將卡片歸類到不同群組
- **資料同步**：將更新後的卡片資料同步至 AI 服務

### 1.2 管理後台界面導覽

管理後台分為以下幾個主要區域：

1. **左側導航區**：功能選單
2. **群組列表區**：顯示所有可用群組
3. **卡片列表區**：顯示選定群組內的卡片
4. **操作區**：包含添加、編輯、刪除等操作按鈕
5. **詳情編輯區**：卡片或群組的詳細信息編輯表單

## 2. 使用指南

### 2.1 卡片管理操作

#### 2.1.1 創建新卡片

1. 點擊「新增卡片」按鈕
2. 填寫必要資訊：
   - 卡片標題
   - 卡片分類
   - 情境問題
   - 專家解答
   - 學習重點（可添加多項）
3. 選擇歸屬群組
4. 點擊「保存」按鈕完成創建

```jsx
// 卡片創建表單結構
<form onSubmit={handleSubmit}>
  <TextField 
    label="標題" 
    name="title" 
    value={formData.title} 
    onChange={handleChange} 
    required 
    fullWidth 
    margin="normal" 
  />
  
  <TextField 
    label="分類" 
    name="category" 
    value={formData.category} 
    onChange={handleChange} 
    required 
    fullWidth 
    margin="normal" 
  />
  
  <TextField 
    label="情境問題" 
    name="question" 
    value={formData.question} 
    onChange={handleChange} 
    required 
    fullWidth 
    multiline 
    rows={3} 
    margin="normal" 
  />
  
  <TextField 
    label="專家解答" 
    name="answer" 
    value={formData.answer} 
    onChange={handleChange} 
    required 
    fullWidth 
    multiline 
    rows={5} 
    margin="normal" 
  />
  
  <FormControl fullWidth margin="normal">
    <InputLabel>所屬群組</InputLabel>
    <Select 
      name="groupId" 
      value={formData.groupId} 
      onChange={handleChange}
      required
    >
      {groups.map(group => (
        <MenuItem key={group.id} value={group.id}>
          {group.name}
        </MenuItem>
      ))}
    </Select>
  </FormControl>
  
  {/* 學習重點動態添加區塊 */}
  <Box sx={{ mt: 3 }}>
    <Typography variant="h6">學習重點</Typography>
    {formData.learnings.map((point, index) => (
      <Box key={index} sx={{ display: 'flex', mb: 1 }}>
        <TextField 
          value={point} 
          onChange={(e) => handleLearningChange(index, e.target.value)} 
          fullWidth
        />
        <IconButton onClick={() => removeLearning(index)}>
          <Delete />
        </IconButton>
      </Box>
    ))}
    <Button startIcon={<Add />} onClick={addLearning}>
      添加學習重點
    </Button>
  </Box>
  
  <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
    <Button type="button" onClick={onCancel} sx={{ mr: 1 }}>
      取消
    </Button>
    <Button type="submit" variant="contained" color="primary">
      保存
    </Button>
  </Box>
</form>
```

#### 2.1.2 編輯卡片

1. 在卡片列表中選擇要編輯的卡片
2. 點擊「編輯」按鈕
3. 修改相應資訊
4. 點擊「保存」按鈕完成編輯

**注意**：編輯卡片時，系統會自動保留卡片的原始 ID，請勿手動修改。

#### 2.1.3 刪除卡片

1. 在卡片列表中選擇要刪除的卡片
2. 點擊「刪除」按鈕
3. 確認刪除操作

**警告**：刪除操作不可恢復，請謹慎操作。

### 2.2 群組管理操作

#### 2.2.1 創建新群組

1. 點擊「新增群組」按鈕
2. 填寫群組名稱
3. 點擊「保存」按鈕完成創建

```jsx
// 群組創建表單結構
<form onSubmit={handleSubmit}>
  <TextField 
    label="群組名稱" 
    name="name" 
    value={groupName} 
    onChange={(e) => setGroupName(e.target.value)} 
    required 
    fullWidth 
    margin="normal" 
  />
  
  <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
    <Button type="button" onClick={onCancel} sx={{ mr: 1 }}>
      取消
    </Button>
    <Button type="submit" variant="contained" color="primary">
      保存
    </Button>
  </Box>
</form>
```

#### 2.2.2 編輯群組

1. 在群組列表中選擇要編輯的群組
2. 點擊「編輯」按鈕
3. 修改群組名稱
4. 點擊「保存」按鈕完成編輯

#### 2.2.3 刪除群組

1. 在群組列表中選擇要刪除的群組
2. 點擊「刪除」按鈕
3. 確認刪除操作

**警告**：刪除群組會導致該群組內的卡片失去歸屬，建議先將卡片移至其他群組。

### 2.3 拖曳排序功能

系統支援直觀的拖曳排序功能：

#### 2.3.1 卡片排序

1. 在卡片列表中，長按卡片並拖動到目標位置
2. 釋放鼠標完成排序
3. 系統會自動保存新的順序

```jsx
// 卡片拖曳排序實現
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

function CardList({ cards, onReorder }) {
  const handleDragEnd = (result) => {
    if (!result.destination) return;
    
    const items = Array.from(cards);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);
    
    // 更新順序屬性
    const reorderedCards = items.map((card, index) => ({
      ...card,
      order: index + 1
    }));
    
    onReorder(reorderedCards);
  };
  
  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <Droppable droppableId="cards">
        {(provided) => (
          <div
            {...provided.droppableProps}
            ref={provided.innerRef}
          >
            {cards.map((card, index) => (
              <Draggable key={card.id} draggableId={card.id} index={index}>
                {(provided) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    {...provided.dragHandleProps}
                  >
                    <CardItem card={card} />
                  </div>
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </DragDropContext>
  );
}
```

#### 2.3.2 群組排序

1. 在群組列表中，長按群組並拖動到目標位置
2. 釋放鼠標完成排序
3. 系統會自動保存新的順序

#### 2.3.3 卡片移動到群組

1. 長按卡片並拖動到目標群組
2. 釋放鼠標完成移動
3. 系統會自動更新卡片的群組歸屬

### 2.4 資料同步操作

為了確保前端顯示和 AI 系統使用最新的卡片資料，需要手動執行同步操作：

1. 點擊管理後台頂部的「同步到 AI 系統」按鈕
2. 等待同步完成通知
3. 同步成功後，AI 系統將使用更新後的卡片數據回答問題

## 3. 管理後台開發指南

### 3.1 代碼結構

管理後台的前端代碼主要位於以下目錄：

```
/src
  /pages
    /Admin
      index.jsx           - 管理頁面入口
      GroupList.jsx       - 群組列表組件
      CardList.jsx        - 卡片列表組件
      CardForm.jsx        - 卡片編輯表單
      GroupForm.jsx       - 群組編輯表單
      DragLayer.jsx       - 拖曳層實現
```

### 3.2 狀態管理

管理後台使用 Context API 管理全局狀態：

```jsx
// AdminContext.jsx
import React, { createContext, useState, useEffect } from 'react';

export const AdminContext = createContext();

export function AdminProvider({ children }) {
  const [groups, setGroups] = useState([]);
  const [cards, setCards] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // 加載數據
  useEffect(() => {
    fetchGroups();
    fetchCards();
  }, []);
  
  // 獲取群組
  const fetchGroups = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/groups');
      const data = await response.json();
      setGroups(data);
      
      // 默認選擇第一個群組
      if (data.length > 0 && !selectedGroup) {
        setSelectedGroup(data[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch groups:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 獲取卡片
  const fetchCards = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/scenarios');
      const data = await response.json();
      setCards(data);
    } catch (error) {
      console.error('Failed to fetch cards:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 添加卡片
  const addCard = async (cardData) => {
    try {
      const response = await fetch('/api/scenarios', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(cardData),
      });
      
      if (!response.ok) throw new Error('Failed to add card');
      
      const newCard = await response.json();
      setCards(prev => [...prev, newCard]);
      return newCard;
    } catch (error) {
      console.error('Error adding card:', error);
      throw error;
    }
  };
  
  // 更新卡片
  const updateCard = async (id, cardData) => {
    try {
      const response = await fetch(`/api/scenarios/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(cardData),
      });
      
      if (!response.ok) throw new Error('Failed to update card');
      
      const updatedCard = await response.json();
      setCards(prev => prev.map(card => 
        card.id === id ? updatedCard : card
      ));
      return updatedCard;
    } catch (error) {
      console.error('Error updating card:', error);
      throw error;
    }
  };
  
  // 刪除卡片
  const deleteCard = async (id) => {
    try {
      const response = await fetch(`/api/scenarios/${id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) throw new Error('Failed to delete card');
      
      setCards(prev => prev.filter(card => card.id !== id));
      return true;
    } catch (error) {
      console.error('Error deleting card:', error);
      throw error;
    }
  };
  
  // 更新卡片順序
  const updateCardOrder = async (reorderedCards) => {
    try {
      // 批量更新卡片順序
      const updatePromises = reorderedCards.map(card => 
        fetch(`/api/scenarios/${card.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ order: card.order }),
        })
      );
      
      await Promise.all(updatePromises);
      
      // 更新本地狀態
      setCards(prev => {
        const updated = [...prev];
        reorderedCards.forEach(card => {
          const index = updated.findIndex(c => c.id === card.id);
          if (index !== -1) {
            updated[index] = { ...updated[index], order: card.order };
          }
        });
        return updated;
      });
      
      return true;
    } catch (error) {
      console.error('Error updating card order:', error);
      throw error;
    }
  };
  
  // 提供上下文值
  const contextValue = {
    groups,
    cards,
    selectedGroup,
    isLoading,
    setSelectedGroup,
    addCard,
    updateCard,
    deleteCard,
    updateCardOrder,
    fetchGroups,
    fetchCards,
    // 其他群組相關方法...
  };
  
  return (
    <AdminContext.Provider value={contextValue}>
      {children}
    </AdminContext.Provider>
  );
}

export const useAdmin = () => React.useContext(AdminContext);
```

### 3.3 API 集成

管理後台依賴以下 API 端點：

| 端點 | 方法 | 功能 |
|-----|-----|-----|
| `/api/groups` | GET | 獲取所有群組 |
| `/api/groups` | POST | 創建新群組 |
| `/api/groups/:id` | PUT | 更新群組信息 |
| `/api/groups/:id` | DELETE | 刪除群組 |
| `/api/scenarios` | GET | 獲取所有卡片 |
| `/api/scenarios` | POST | 創建新卡片 |
| `/api/scenarios/:id` | PUT | 更新卡片信息 |
| `/api/scenarios/:id` | DELETE | 刪除卡片 |
| `/api/scenarios/:id/group` | PUT | 更新卡片的群組歸屬 |
| `/api/sync` | POST | 觸發資料同步到 AI 系統 |

## 4. 問題修復與優化

### 4.1 已修復問題

#### 4.1.1 拖曳卡片進群組 404 錯誤修復

該問題由於後端路由重複定義導致，已完成以下修復：

1. **後端路由優化**：
   - 移除了重複定義的 `/api/scenarios/:id/group` 路由
   - 加強了路由參數驗證與錯誤處理

2. **前端錯誤處理增強**：
   - 添加了詳細的錯誤反饋機制
   - 改進拖曳操作的狀態管理

```javascript
// 修復後的拖曳到群組處理函數
const handleDragToGroup = async (cardId, targetGroupId) => {
  setIsLoading(true);
  try {
    const response = await fetch(`/api/scenarios/${cardId}/group`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ groupId: targetGroupId }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '更新群組失敗');
    }
    
    // 更新本地狀態
    setCards(prev => prev.map(card => 
      card.id === cardId ? { ...card, groupId: targetGroupId } : card
    ));
    
    showNotification('卡片已成功移動到新群組', 'success');
  } catch (error) {
    console.error('拖曳卡片到群組錯誤:', error);
    showNotification(`操作失敗: ${error.message}`, 'error');
    
    // 復原 UI 狀態
    refreshCards();
  } finally {
    setIsLoading(false);
  }
};
```

#### 4.1.2 編輯卡片儲存 ID 無效錯誤修復

該問題由於前端 ID 驗證邏輯不嚴謹導致，已完成以下修復：

1. **ID 驗證增強**：
   - 增加更嚴格的類型檢查
   - 添加空值檢查邏輯

2. **錯誤處理優化**：
   - 改進 `handleCardEdit` 和 `handleCardUpdate` 函數的錯誤處理
   - 添加詳細的用戶錯誤反饋

```javascript
// 修復後的卡片更新處理函數
const handleCardUpdate = async (cardData) => {
  // ID 驗證
  if (!cardData.id || typeof cardData.id !== 'string' || cardData.id.trim() === '') {
    showNotification('卡片 ID 無效，無法更新', 'error');
    return;
  }
  
  setIsLoading(true);
  try {
    const response = await fetch(`/api/scenarios/${cardData.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(cardData),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '更新卡片失敗');
    }
    
    const updatedCard = await response.json();
    
    // 驗證返回數據
    if (!updatedCard || !updatedCard.id) {
      throw new Error('更新後返回的卡片數據無效');
    }
    
    // 更新本地狀態
    setCards(prev => prev.map(card => 
      card.id === cardData.id ? updatedCard : card
    ));
    
    showNotification('卡片更新成功', 'success');
    return updatedCard;
  } catch (error) {
    console.error('更新卡片錯誤:', error);
    showNotification(`更新失敗: ${error.message}`, 'error');
    throw error;
  } finally {
    setIsLoading(false);
  }
};
```

### 4.2 未來優化計劃

#### 4.2.1 數據庫優化

目前系統使用 JSON 文件存儲數據，計劃遷移至 SQLite 數據庫：

1. **創建數據庫模式**：
   ```sql
   -- 群組表
   CREATE TABLE groups (
     id TEXT PRIMARY KEY,
     name TEXT NOT NULL,
     order INTEGER NOT NULL
   );
   
   -- 卡片表
   CREATE TABLE scenarios (
     id TEXT PRIMARY KEY,
     category TEXT NOT NULL,
     title TEXT NOT NULL,
     question TEXT NOT NULL,
     answer TEXT NOT NULL,
     learnings TEXT NOT NULL, -- JSON 字符串
     groupId TEXT,
     order INTEGER NOT NULL,
     FOREIGN KEY(groupId) REFERENCES groups(id)
   );
   ```

2. **API 層更新**：修改所有 API 端點使用 SQLite 查詢替代 JSON 文件操作
3. **數據遷移**：開發遷移腳本將現有數據導入 SQLite

#### 4.2.2 批量操作功能

計劃添加批量操作功能提升管理效率：

1. **批量編輯**：同時修改多張卡片的特定字段（如分類）
2. **批量移動**：一次將多張卡片移動到指定群組
3. **批量導入導出**：支持 Excel/CSV 格式的數據導入導出

#### 4.2.3 歷史記錄與版本控制

計劃添加歷史記錄功能：

1. **操作日誌**：記錄所有數據修改操作
2. **版本回溯**：支持回溯到卡片的歷史版本
3. **變更比較**：可視化顯示卡片內容的變更

#### 4.2.4 同步自動化

目前的同步流程需要手動觸發，計劃實現自動化：

1. **文件監聽**：監聽 JSON 文件變化自動觸發同步
2. **定時同步**：設置定時任務定期執行同步
3. **一鍵同步**：在後台管理界面添加一鍵同步按鈕

## 5. 常見問題與故障排除

### 5.1 常見錯誤與解決方案

| 錯誤情況 | 可能原因 | 解決方案 |
|---------|---------|---------|
| 創建卡片失敗 | JSON 文件權限問題 | 檢查 scenarios.json 文件權限 |
| 拖曳排序不生效 | 前端狀態與後端不同步 | 刷新頁面重新加載數據 |
| 同步按鈕無響應 | AI 服務未運行 | 確認 AI 服務是否正常運行 |
| ID 重複錯誤 | 手動編輯導致 ID 衝突 | 讓系統自動生成 ID，不手動修改 |

### 5.2 性能優化建議

1. **分頁加載**：當卡片數量較大時，實現分頁加載
2. **延遲保存**：拖曳排序時使用防抖技術延遲請求
3. **本地緩存**：使用 localStorage 緩存不常變化的數據
4. **壓縮圖片**：如添加卡片配圖，需進行適當壓縮

### 5.3 數據備份建議

1. 定期備份 JSON 文件
2. 實現自動備份腳本，每日執行
3. 在進行大量修改前手動創建備份

## 6. 擴展與定制

### 6.1 主題定制

管理後台支持主題定制，可通過修改以下文件實現：

```jsx
// src/themes/adminTheme.js
import { createTheme } from '@mui/material/styles';

const adminTheme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // 可自定義主色調
    },
    secondary: {
      main: '#dc004e', // 可自定義輔色調
    },
    background: {
      default: '#f5f5f5', // 可自定義背景色
    },
  },
  typography: {
    fontFamily: '"Noto Sans TC", "Roboto", "Arial", sans-serif',
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
    // 其他組件樣式覆蓋...
  },
});

export default adminTheme;
```

### 6.2 功能擴展點

1. **用戶權限系統**：可擴展添加基於角色的權限控制
2. **資料分析面板**：添加卡片使用統計與分析功能
3. **自定義字段**：支持為卡片添加自定義字段
4. **審核工作流**：添加內容審核與發布流程
