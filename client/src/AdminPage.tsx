import React, { useState, useEffect } from 'react';
import './App.css'; // Import the CSS file for styling

interface Scenario {
    id: string;
    category: string;
    title: string;
    question: string;
    answer: string;
    learnings: string[];
    order?: number;
    groupId?: string | null; // 群組ID
}

interface Group {
    id: string;
    name: string;
    order: number;
}

const AdminPage = () => {
    const [scenarios, setScenarios] = useState<Scenario[]>([]);
    const [groups, setGroups] = useState<Group[]>([]);
    const [formState, setFormState] = useState({
        id: '',
        category: '',
        title: '',
        question: '',
        answer: '',
        learnings: ''
    });
    const [isEditing, setIsEditing] = useState(false);
    const [editingCardId, setEditingCardId] = useState<string | null>(null);
    const [draggedItem, setDraggedItem] = useState<Scenario | null>(null);
    const [draggedItemType, setDraggedItemType] = useState<'scenario' | 'group' | null>(null);
    const [editingGroupId, setEditingGroupId] = useState<string | null>(null);
    const [newGroupName, setNewGroupName] = useState<string>('');
    const [showNewGroupForm, setShowNewGroupForm] = useState<boolean>(false);
    const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
    const [dragOverGroupId, setDragOverGroupId] = useState<string | null>(null);
    // const [dragOverScenarioId, setDragOverScenarioId] = useState<string | null>(null);

    useEffect(() => {
        fetchScenarios();
        fetchGroups();
    }, []);

    const fetchScenarios = async () => {
        const response = await fetch('http://localhost:3001/api/scenarios');
        const data = await response.json();
        // 確保所有場景都有一個順序屬性
        const scenariosWithOrder = data.data.map((scenario: Scenario, index: number) => ({
            ...scenario,
            order: scenario.order ?? index, // 如果沒有order屬性，則使用索引
            groupId: scenario.groupId || null // 確保groupId存在
        }));
        // 按照順序屬性排序
        scenariosWithOrder.sort((a: Scenario, b: Scenario) => (a.order || 0) - (b.order || 0));
        setScenarios(scenariosWithOrder);
    };
    
    const fetchGroups = async () => {
        try {
            const response = await fetch('http://localhost:3001/api/groups');
            const data = await response.json();
            setGroups(data.data || []);
        } catch (error) {
            console.error('Failed to fetch groups:', error);
            setGroups([]);
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setFormState({ ...formState, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const url = isEditing ? `http://localhost:3001/api/scenarios/${formState.id}` : 'http://localhost:3001/api/scenarios';
        const method = isEditing ? 'PUT' : 'POST';

        await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...formState,
                learnings: formState.learnings.split(',').map(s => s.trim())
            }),
        });

        fetchScenarios();
        resetForm();
    };

    // Commented out since it's not being used
    // const handleEdit = (scenario: any) => {
    //     setFormState({
    //         ...scenario,
    //         learnings: scenario.learnings.join(', ')
    //     });
    //     setIsEditing(true);
    //     window.scrollTo(0, document.body.scrollHeight); // Scroll to the bottom to see the form
    // };

    const handleCardEdit = (id: string) => {
        console.log('Starting card edit for ID:', id);
        
        // 驗證ID有效性
        if (!id || typeof id !== 'string' || id.trim() === '' || id === 'undefined' || id === 'null') {
            console.error('Invalid card ID provided for editing:', id);
            alert('無效的卡片ID，無法進行編輯。');
            return;
        }
        
        // 驗證卡片是否存在
        const cardExists = scenarios.find(s => s.id === id);
        if (!cardExists) {
            console.error('Card not found for editing:', id, 'Available IDs:', scenarios.map(s => s.id));
            alert(`找不到ID為 ${id} 的卡片，無法進行編輯。`);
            return;
        }
        
        console.log('Setting editing card ID to:', id);
        setEditingCardId(id);
    };

    const handleCardUpdate = async (id: string, updatedData: any) => {
        console.log('Updating card:', id, updatedData);
        
        // 確保 ID 不為空值和有效性
        if (!id || typeof id !== 'string' || id.trim() === '' || id === 'undefined' || id === 'null') {
            console.error('Invalid scenario ID for update:', id, 'Type:', typeof id);
            alert(`卡片ID無效（${id}），無法更新。請重新整理頁面後再試。`);
            return;
        }
        
        const originalScenarios = [...scenarios];
        const scenarioToUpdate = scenarios.find(s => s.id === id);

        if (!scenarioToUpdate) {
            console.error('Cannot find scenario with id:', id, 'Available IDs:', scenarios.map(s => s.id));
            alert(`找不到ID為 ${id} 的情境卡片，無法更新。`);
            return;
        }

        // 確保 ID 不會被覆蓋並移除可能導致錯誤的欄位
        const { groupId, order, ...cleanedData } = updatedData;
        const newScenarioData = { 
            ...scenarioToUpdate, 
            ...cleanedData, 
            id: scenarioToUpdate.id, // 確保使用原始的ID
            // 保留原始的群組和順序資訊
            groupId: scenarioToUpdate.groupId,
            order: scenarioToUpdate.order
        };
        console.log('New scenario data for API call:', newScenarioData);

        // 在 UI 上先更新（樂觀 UI 更新）
        const updatedScenarios = scenarios.map(s => s.id === id ? newScenarioData : s);
        setScenarios(updatedScenarios);
        setEditingCardId(null);

        try {
            // 確保 API URL 正確且 ID 有效
            const scenarioId = newScenarioData.id;
            
            if (!scenarioId) {
                throw new Error('卡片ID無效，無法更新。');
            }
            
            const apiUrl = `http://localhost:3001/api/scenarios/${encodeURIComponent(scenarioId)}`;
            console.log('Sending PUT request to:', apiUrl);
            
            const response = await fetch(apiUrl, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newScenarioData),
            });

            console.log('Server response status:', response.status);
            
            // 線時探測後端錯誤
            if (!response.ok) {
                let errorMessage = `伺服器回應狀態碼: ${response.status}`;
                try {
                    const errorData = await response.json();
                    console.log('Error response data:', errorData);
                    errorMessage += `, 訊息: ${errorData.message || JSON.stringify(errorData)}`;
                } catch (parseError) {
                    console.error('Failed to parse error response:', parseError);
                }
                throw new Error(errorMessage);
            }

            const responseData = await response.json();
            console.log('Success response data:', responseData);

        } catch (error) {
            console.error('Failed to update scenario:', error);
            setScenarios(originalScenarios); // 失敗時恢復原始狀態
            setEditingCardId(null); // 重設編輯狀態
            
            let errorMessage = '未知錯誤';
            if (error instanceof Error) {
                if (error.message.includes('404')) {
                    errorMessage = '找不到指定的卡片，可能已被刪除或ID不正確';
                } else if (error.message.includes('500')) {
                    errorMessage = '伺服器內部錯誤，請稍後再試';
                } else {
                    errorMessage = error.message;
                }
            }
            
            alert(`儲存失敗: ${errorMessage}\n\n請檢查：\n1. 網路連線是否正常\n2. 後端伺服器是否運行\n3. 嘗試重新整理頁面`);
        }
    };

    const handleCancelCardEdit = () => {
        setEditingCardId(null);
    };
    
    // 拖曳排序相關函數
    const handleDragStart = (scenario: Scenario) => (e: React.DragEvent<HTMLDivElement>) => {
        // 設置拖曳數據
        e.dataTransfer.setData('text/plain', JSON.stringify({ id: scenario.id, type: 'scenario' }));
        e.dataTransfer.effectAllowed = 'move';
        
        // 設置拖曳狀態
        setDraggedItem(scenario);
        setDraggedItemType('scenario');
        
        // 一些視覺反饋
        const target = e.currentTarget as HTMLElement;
        target.classList.add('dragging');
        
        console.log(`開始拖曳卡片 ID: ${scenario.id}, 原群組: ${scenario.groupId || '無'}`);  
    };
    
    const handleDragOver = (e: React.DragEvent, targetScenario: Scenario) => {
        e.preventDefault(); // 允許放置
        if (!draggedItem || draggedItem.id === targetScenario.id) return;
        
        // 添加視覺反饋
        const elements = document.querySelectorAll('.admin-card');
        elements.forEach(el => {
            if ((el as HTMLElement).dataset.id === targetScenario.id) {
                el.classList.add('drag-over');
            } else {
                el.classList.remove('drag-over');
            }
        });
    };
    
    const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
        // 移除所有視覺反饋
        document.querySelectorAll('.admin-card').forEach(el => {
            el.classList.remove('drag-over');
        });
    };
    
    const handleDrop = async (e: React.DragEvent, targetScenario: Scenario) => {
        e.preventDefault();
        e.stopPropagation(); // Prevent group's onDrop from firing

        if (!draggedItem || draggedItem.id === targetScenario.id) return;

        // Only handle reordering within the same group
        if (draggedItem.groupId !== targetScenario.groupId) {
            // If dragged to a different group, let handleDropOnGroup handle it.
            // This drop event is on a card, but we can treat it as a drop on the group.
            handleDropOnGroup(e, targetScenario.groupId || '');
            return;
        }

        const originalScenarios = [...scenarios];
        const groupScenarios = scenarios.filter(s => s.groupId === draggedItem.groupId);
        const otherScenarios = scenarios.filter(s => s.groupId !== draggedItem.groupId);

        const draggedIndex = groupScenarios.findIndex(s => s.id === draggedItem.id);
        const targetIndex = groupScenarios.findIndex(s => s.id === targetScenario.id);

        const [movedItem] = groupScenarios.splice(draggedIndex, 1);
        groupScenarios.splice(targetIndex, 0, movedItem);

        const updatedScenarios = [...otherScenarios, ...groupScenarios].map((s, i) => ({ ...s, order: i }));

        setScenarios(updatedScenarios);

        try {
            await fetch('http://localhost:3001/api/scenarios/reorder', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scenarios: updatedScenarios }),
            });
        } catch (error) {
            console.error('Failed to reorder scenarios:', error);
            setScenarios(originalScenarios);
        }
    };
    
    const handleDragEnd = (e: React.DragEvent) => {
        // 移除拖曳過程中的視覺效果
        const elements = document.querySelectorAll('.dragging');
        elements.forEach(el => el.classList.remove('dragging'));
        
        // 重置所有拖曳狀態
        setDraggedItem(null);
        setDraggedItemType(null);
        // setDragOverScenarioId(null); // This state is no longer used
        setDragOverGroupId(null);
        
        console.log('完成拖曳操作');
    };
    
    // 群組相關函數
    const toggleGroupExpand = (groupId: string) => {
        setExpandedGroups(prev => ({
            ...prev,
            [groupId]: !prev[groupId]
        }));
    };
    
    const handleCreateGroup = async () => {
        if (newGroupName.trim() === '') return;

        const newGroupData = { name: newGroupName, order: groups.length };

        try {
            const response = await fetch('http://localhost:3001/api/groups', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newGroupData),
            });
            const result = await response.json();
            if (result.success) {
                const newGroup = result.data;
                setGroups(prev => [...prev, newGroup]);
                setNewGroupName('');
                setShowNewGroupForm(false);
                setExpandedGroups(prev => ({ ...prev, [newGroup.id]: true }));
            }
        } catch (error) {
            console.error('Failed to create group:', error);
        }
    };
    
    const handleStartEditGroup = (groupId: string) => {
        setEditingGroupId(groupId);
        // 設定編輯時的初始名稱
        const group = groups.find(g => g.id === groupId);
        if (group) setNewGroupName(group.name);
    };
    
    const handleSaveGroupName = async (groupId: string) => {
        if (newGroupName.trim() === '') return;
        
        try {
            await fetch(`http://localhost:3001/api/groups/${groupId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newGroupName }),
            });
            
            // 更新前端群組名稱
            setGroups(groups.map(group => 
                group.id === groupId ? { ...group, name: newGroupName } : group
            ));
            
            setEditingGroupId(null);
            setNewGroupName('');
        } catch (error) {
            console.error('Failed to update group name:', error);
        }
    };
    
    const handleDeleteGroup = async (groupId: string) => {
        if (!window.confirm('Are you sure you want to delete this group? Scenarios in this group will be moved out of the group.')) return;
        
        try {
            await fetch(`http://localhost:3001/api/groups/${groupId}`, {
                method: 'DELETE'
            });
            
            // 移除該群組並將所有場景設為無群組
            setGroups(groups.filter(group => group.id !== groupId));
            setScenarios(scenarios.map(scenario => {
                if (scenario.groupId === groupId) {
                    return { ...scenario, groupId: null };
                }
                return scenario;
            }));
        } catch (error) {
            console.error('Failed to delete group:', error);
        }
    };
    
    const handleDragOverGroup = (e: React.DragEvent, groupId: string) => {
        e.preventDefault();
        if (!draggedItem || draggedItemType !== 'scenario') return;
        
        setDragOverGroupId(groupId);
    };
    
    const handleDragLeaveGroup = () => {
        setDragOverGroupId(null);
    };
    
    const handleDropOnGroup = async (e: React.DragEvent, groupId: string) => {
        e.preventDefault();
        e.stopPropagation(); // 阻止事件冒泡
        
        // 直接使用狀態中的拖曳項目，而不依賴 dataTransfer
        if (!draggedItem || draggedItemType !== 'scenario') {
            console.error('無效的拖曳操作：沒有正在拖曳的情境卡片', { draggedItem, draggedItemType });
            alert('拖曳失敗：沒有有效的拖曳項目。請重新嘗試。');
            return;
        }
        
        // 確保我們有一個有效的卡片 ID
        const scenarioId = draggedItem.id;
        
        // 驗證 scenarioId 的有效性
        if (!scenarioId || typeof scenarioId !== 'string' || scenarioId.trim() === '') {
            console.error('Invalid scenario ID for drag operation:', scenarioId, 'Type:', typeof scenarioId);
            alert('拖曳失敗：卡片ID無效。請重新整理頁面後再試。');
            return;
        }
        
        const scenarioToMove = scenarios.find(s => s.id === scenarioId);
        
        if (!scenarioToMove) {
            console.error('Cannot find scenario with ID:', scenarioId, 'Available IDs:', scenarios.map(s => s.id));
            alert(`拖曳失敗：找不到ID為 ${scenarioId} 的卡片。請重新整理頁面後再試。`);
            return;
        }
        
        // 如果卡片已在此群組中，不需要操作
        if (scenarioToMove.groupId === groupId) {
            console.log(`卡片 ${scenarioId} 已在群組 ${groupId} 中，不需要移動`);
            return;
        }

        console.log(`拖曳單一卡片 ${scenarioId} 到群組 ${groupId}`);
        
        // 保存原始狀態以便復原
        const originalScenarios = [...scenarios];
        
        // 嘗試樂觀更新 - 僅更新單一卡片
        const updatedScenarios = scenarios.map(s => 
            s.id === scenarioId ? { ...s, groupId } : s
        );
        
        // 更新前端狀態
        setScenarios(updatedScenarios);
        setDragOverGroupId(null);

        try {
            // 通知後端更新卡片的群組
            const response = await fetch(`http://localhost:3001/api/scenarios/${scenarioId}/group`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ groupId }),
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }
            
            console.log(`成功更新卡片 ${scenarioId} 群組為 ${groupId}`);
        } catch (error) {
            console.error('Failed to update scenario group:', error);
            // 失敗時恢復原始狀態
            setScenarios(originalScenarios);
            setDragOverGroupId(null);
            
            let errorMessage = '未知錯誤';
            if (error instanceof Error) {
                if (error.message.includes('404')) {
                    errorMessage = '找不到指定的卡片或群組，請重新整理頁面';
                } else if (error.message.includes('500')) {
                    errorMessage = '伺服器內部錯誤，請稍後再試';
                } else if (error.message.includes('400')) {
                    errorMessage = '請求參數錯誤，卡片ID可能無效';
                } else {
                    errorMessage = error.message;
                }
            }
            
            alert(`拖曳失敗，已恢復原始狀態: ${errorMessage}\n\n請檢查：\n1. 網路連線是否正常\n2. 後端伺服器是否運行\n3. 嘗試重新整理頁面`);
        }
    };

    const handleDelete = async (id: string) => {
        if (window.confirm(`Are you sure you want to delete scenario ${id}?`)) {
            await fetch(`http://localhost:3001/api/scenarios/${id}`, { method: 'DELETE' });
            fetchScenarios();
        }
    };

    const resetForm = () => {
        setFormState({ id: '', category: '', title: '', question: '', answer: '', learnings: '' });
        setIsEditing(false);
    };

    return (
        <div className="App">
            <header className="App-header">
                <h1>Admin Panel</h1>
            </header>
            <main>
                {/* 新增群組按鈕和表單 */}
                <div className="new-group-container">
                    {showNewGroupForm ? (
                        <div className="group-edit-form">
                            <input 
                                type="text" 
                                value={newGroupName} 
                                onChange={(e) => setNewGroupName(e.target.value)} 
                                placeholder="Enter group name"
                            />
                            <button onClick={handleCreateGroup} className="btn-primary">Save</button>
                            <button onClick={() => {
                                setShowNewGroupForm(false);
                                setNewGroupName('');
                            }} className="btn-secondary">Cancel</button>
                        </div>
                    ) : (
                        <button onClick={() => setShowNewGroupForm(true)} className="btn-new-group">+ Add New Group</button>
                    )}
                </div>
                
                {/* 顯示群組 */}
                {groups.map(group => {
                    // 筛選屬於該群組的場景
                    const groupScenarios = scenarios.filter(scenario => scenario.groupId === group.id);
                    const isExpanded = expandedGroups[group.id] || false;
                    
                    return (
                        <div 
                            key={group.id} 
                            className={`group-container ${dragOverGroupId === group.id ? 'group-drag-over' : ''}`}
                            onDragOver={(e) => handleDragOverGroup(e, group.id)}
                            onDrop={e => handleDropOnGroup(e, group.id)}
                            onDragEnter={(e) => {
                                e.preventDefault();
                                setDragOverGroupId(group.id);
                            }}
                            onDragLeave={handleDragLeaveGroup}
                        >
                            <div className="group-header" onClick={() => toggleGroupExpand(group.id)}>
                                {editingGroupId === group.id ? (
                                    <div className="group-edit-form" onClick={(e) => e.stopPropagation()}>
                                        <input 
                                            type="text" 
                                            value={newGroupName} 
                                            onChange={(e) => setNewGroupName(e.target.value)} 
                                            placeholder="Enter group name"
                                        />
                                        <button onClick={() => handleSaveGroupName(group.id)} className="btn-primary">Save</button>
                                        <button onClick={() => {
                                            setEditingGroupId(null);
                                            setNewGroupName('');
                                        }} className="btn-secondary">Cancel</button>
                                    </div>
                                ) : (
                                    <>
                                        <h3 className="group-title">{group.name} ({groupScenarios.length})</h3>
                                        <div className="group-actions">
                                            <button onClick={(e) => {
                                                e.stopPropagation();
                                                handleStartEditGroup(group.id);
                                            }} className="btn-edit">Edit</button>
                                            <button onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteGroup(group.id);
                                            }} className="btn-delete">Delete</button>
                                        </div>
                                    </>
                                )}
                            </div>
                            
                            {isExpanded && groupScenarios.length > 0 && (
                                <div className="group-content">
                                    {groupScenarios.map(scenario => {
                                        const isCardEditing = editingCardId === scenario.id;
                                        const isAnyCardEditing = editingCardId !== null;
                                        
                                        // 直接使用事件處理函數內的本地變量
                                        const handleCardSubmit = (e: React.FormEvent) => {
                                            e.preventDefault();
                                            const formElement = e.target as HTMLFormElement;
                                            
                                            // 從表單元素直接獲取值
                                            const title = (formElement.elements.namedItem('title') as HTMLInputElement).value;
                                            const category = (formElement.elements.namedItem('category') as HTMLInputElement).value;
                                            const question = (formElement.elements.namedItem('question') as HTMLTextAreaElement).value;
                                            const answer = (formElement.elements.namedItem('answer') as HTMLTextAreaElement).value;
                                            const learningsText = (formElement.elements.namedItem('learningsText') as HTMLTextAreaElement).value;
                                            
                                            const updatedData = {
                                                ...scenario,
                                                title,
                                                category,
                                                question,
                                                answer,
                                                learnings: learningsText.split(',').map(s => s.trim())
                                            };
                                            
                                            handleCardUpdate(scenario.id, updatedData);
                                        };

                                        return (
                                            <div 
                                                key={scenario.id} 
                                                className={`rule-card admin-card ${isCardEditing ? 'editing' : ''} ${isAnyCardEditing && !isCardEditing ? 'dimmed' : ''} ${draggedItem?.id === scenario.id ? 'dragging' : ''}`}
                                                draggable={!isAnyCardEditing} 
                                                onDragStart={handleDragStart(scenario)}
                                                onDragOver={(e) => handleDragOver(e, scenario)}
                                                onDragLeave={(e) => handleDragLeave(e)}
                                                onDrop={(e) => handleDrop(e, scenario)}
                                                onDragEnd={handleDragEnd}
                                                data-id={scenario.id}
                                            >
                                                {isCardEditing ? (
                                                    // Edit mode - show form inside card
                                                    <form onSubmit={handleCardSubmit} className="card-edit-form">
                                                        <div className="form-group">
                                                            <label>Title</label>
                                                            <input name="title" defaultValue={scenario.title} required />
                                                        </div>
                                                        <div className="form-group">
                                                            <label>Category</label>
                                                            <input name="category" defaultValue={scenario.category} required />
                                                        </div>
                                                        <div className="form-group">
                                                            <label>Question</label>
                                                            <textarea name="question" defaultValue={scenario.question} required></textarea>
                                                        </div>
                                                        <div className="form-group">
                                                            <label>Answer</label>
                                                            <textarea name="answer" defaultValue={scenario.answer} required></textarea>
                                                        </div>
                                                        <div className="form-group">
                                                            <label>Learnings</label>
                                                            <textarea name="learningsText" defaultValue={scenario.learnings.join(', ')} placeholder="Comma-separated learnings" required></textarea>
                                                        </div>
                                                        <div className="card-actions">
                                                            <button type="submit" className="btn-primary">Save</button>
                                                            <button type="button" onClick={handleCancelCardEdit} className="btn-secondary">Cancel</button>
                                                        </div>
                                                    </form>
                                                ) : (
                                                    // View mode - show card content
                                                    <>
                                                        <h3>{scenario.title}</h3>
                                                        <p><span className="label">ID:</span> {scenario.id}</p>
                                                        <p><span className="label">Category:</span> {scenario.category}</p>
                                                        <p><span className="label">Question:</span> {scenario.question}</p>
                                                        <p><span className="label">Answer:</span> {scenario.answer}</p>
                                                        <p><span className="label">Learnings:</span></p>
                                                        <ul>
                                                            {scenario.learnings.map((item:string, index:number) => (
                                                                item.trim() !== '' && <li key={index}>{item.trim()}</li>
                                                            ))}
                                                        </ul>
                                                        <div className="card-actions">
                                                            <button onClick={() => handleCardEdit(scenario.id)} className="btn-edit">Edit</button>
                                                            <button onClick={() => handleDelete(scenario.id)} className="btn-delete">Delete</button>
                                                        </div>
                                                    </>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    );
                })}
                
                {/* 不屬於任何群組的場景 */}
                <div className="rule-list">
                    <h3 className="ungrouped-title">Ungrouped Scenarios</h3>
                    {scenarios.filter(scenario => !scenario.groupId).map(scenario => {
                        const isCardEditing = editingCardId === scenario.id;
                        
                        // 直接使用事件處理函數內的本地變量
                        const handleCardSubmit = (e: React.FormEvent) => {
                            e.preventDefault();
                            const formElement = e.target as HTMLFormElement;
                            
                            // 從表單元素直接獲取值
                            const title = (formElement.elements.namedItem('title') as HTMLInputElement).value;
                            const category = (formElement.elements.namedItem('category') as HTMLInputElement).value;
                            const question = (formElement.elements.namedItem('question') as HTMLTextAreaElement).value;
                            const answer = (formElement.elements.namedItem('answer') as HTMLTextAreaElement).value;
                            const learningsText = (formElement.elements.namedItem('learningsText') as HTMLTextAreaElement).value;
                            
                            const updatedData = {
                                ...scenario,
                                title,
                                category,
                                question,
                                answer,
                                learnings: learningsText.split(',').map(s => s.trim())
                            };
                            
                            handleCardUpdate(scenario.id, updatedData);
                        };

                        return (
                            <div 
                                key={scenario.id} 
                                className={`rule-card admin-card ${isCardEditing ? 'editing' : ''} ${draggedItem?.id === scenario.id ? 'dragging' : ''}`}
                                draggable={!isCardEditing} 
                                onDragStart={handleDragStart(scenario)}
                                onDragOver={(e) => handleDragOver(e, scenario)}
                                onDragLeave={(e) => handleDragLeave(e)}
                                onDrop={(e) => handleDrop(e, scenario)}
                                onDragEnd={handleDragEnd}
                                data-id={scenario.id}
                            >
                                {isCardEditing ? (
                                    // Edit mode - show form inside card
                                    <form onSubmit={handleCardSubmit} className="card-edit-form">
                                        <div className="form-group">
                                            <label>Title</label>
                                            <input name="title" defaultValue={scenario.title} required />
                                        </div>
                                        <div className="form-group">
                                            <label>Category</label>
                                            <input name="category" defaultValue={scenario.category} required />
                                        </div>
                                        <div className="form-group">
                                            <label>Question</label>
                                            <textarea name="question" defaultValue={scenario.question} required></textarea>
                                        </div>
                                        <div className="form-group">
                                            <label>Answer</label>
                                            <textarea name="answer" defaultValue={scenario.answer} required></textarea>
                                        </div>
                                        <div className="form-group">
                                            <label>Learnings</label>
                                            <textarea name="learningsText" defaultValue={scenario.learnings.join(', ')} placeholder="Comma-separated learnings" required></textarea>
                                        </div>
                                        <div className="card-actions">
                                            <button type="submit" className="btn-primary">Save</button>
                                            <button type="button" onClick={handleCancelCardEdit} className="btn-secondary">Cancel</button>
                                        </div>
                                    </form>
                                ) : (
                                    // View mode - show card content
                                    <>
                                        <h3>{scenario.title}</h3>
                                        <p><span className="label">ID:</span> {scenario.id}</p>
                                        <p><span className="label">Category:</span> {scenario.category}</p>
                                        <p><span className="label">Question:</span> {scenario.question}</p>
                                        <p><span className="label">Answer:</span> {scenario.answer}</p>
                                        <p><span className="label">Learnings:</span></p>
                                        <ul>
                                            {scenario.learnings.map((item:string, index:number) => (
                                                item.trim() !== '' && <li key={index}>{item.trim()}</li>
                                            ))}
                                        </ul>
                                        <div className="card-actions">
                                            <button onClick={() => handleCardEdit(scenario.id)} className="btn-edit">Edit</button>
                                            <button onClick={() => handleDelete(scenario.id)} className="btn-delete">Delete</button>
                                        </div>
                                    </>
                                )}
                            </div>
                        );
                    })}
                </div>
                
                <div className="admin-form-container">
                    <form onSubmit={handleSubmit} className="admin-form">
                        <h3>{isEditing ? 'Edit Scenario' : 'Create New Scenario'}</h3>
                        <div className="form-grid">
                            <div className="form-group">
                                <label>ID</label>
                                <input name="id" value={formState.id} onChange={handleInputChange} placeholder="scenario-XXX" required disabled={isEditing} />
                            </div>
                            <div className="form-group">
                                <label>Category</label>
                                <input name="category" value={formState.category} onChange={handleInputChange} placeholder="e.g., General" required />
                            </div>
                            <div className="form-group full-width">
                                <label>Title</label>
                                <input name="title" value={formState.title} onChange={handleInputChange} placeholder="Title" required />
                            </div>
                            <div className="form-group full-width">
                                <label>Question</label>
                                <textarea name="question" value={formState.question} onChange={handleInputChange} placeholder="Question" required></textarea>
                            </div>
                            <div className="form-group full-width">
                                <label>Answer</label>
                                <textarea name="answer" value={formState.answer} onChange={handleInputChange} placeholder="Answer" required></textarea>
                            </div>
                            <div className="form-group full-width">
                                <label>Learnings</label>
                                <textarea name="learnings" value={formState.learnings} onChange={handleInputChange} placeholder="Comma-separated learnings" required></textarea>
                            </div>
                        </div>
                        <div className="form-actions">
                            <button type="submit" className="btn-primary">{isEditing ? 'Update Scenario' : 'Create Scenario'}</button>
                            {isEditing && <button type="button" onClick={resetForm} className="btn-secondary">Cancel</button>}
                        </div>
                    </form>
                </div>
            </main>
        </div>
    );
};

export default AdminPage;