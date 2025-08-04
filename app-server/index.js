const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const fs = require('fs');

const app = express();
const port = 3001;

app.use(cors());
app.use(bodyParser.json());

// File paths
const SCENARIOS_PATH = 'scenarios.json';
const GROUPS_PATH = 'groups.json';

// Helper to read JSON file
const readJsonFile = (filePath) => {
    try {
        if (!fs.existsSync(filePath)) return [];
        const data = fs.readFileSync(filePath, 'utf8');
        const cleanData = data.charCodeAt(0) === 0xFEFF ? data.slice(1) : data;
        const jsonData = JSON.parse(cleanData);
        return jsonData.data || [];
    } catch (err) {
        console.error(`Error reading or parsing ${filePath}:`, err);
        return [];
    }
};

// Helper to write JSON file
const writeJsonFile = (filePath, data) => {
    try {
        fs.writeFileSync(filePath, JSON.stringify({ data }, null, 2), 'utf8');
    } catch (err) {
        console.error(`Error writing to ${filePath}:`, err);
    }
};

// Load initial data
let scenarios = readJsonFile(SCENARIOS_PATH);
let groups = readJsonFile(GROUPS_PATH);

// Ensure every scenario has a unique id (data migration helper)
let scenariosModified = false;
scenarios = scenarios.map((s) => {
    if (!s.id || typeof s.id !== 'string' || s.id.trim() === '') {
        scenariosModified = true;
        return { ...s, id: `scenario-${Date.now()}-${Math.random().toString(16).slice(2,8)}` };
    }
    return s;
});
if (scenariosModified) {
    console.log('[Data Migration] Added missing IDs to some scenarios');
    writeJsonFile(SCENARIOS_PATH, scenarios);
}

// --- Scenarios API ---
app.get('/api/scenarios', (req, res) => {
    res.json({ data: scenarios });
});

app.post('/api/scenarios', (req, res) => {
    const newScenario = { ...req.body, id: `scenario-${Date.now()}` };
    scenarios.push(newScenario);
    writeJsonFile(SCENARIOS_PATH, scenarios);
    res.status(201).json({ success: true, data: newScenario });
});

app.put('/api/scenarios/:id', (req, res) => {
    console.log('PUT /api/scenarios/:id - Request params:', req.params);
    console.log('PUT /api/scenarios/:id - Request body:', req.body);
    
    const { id } = req.params;
    console.log('Looking for scenario with ID:', id);
    console.log('Available scenario IDs:', scenarios.map(s => s.id));
    
    const scenarioIndex = scenarios.findIndex(s => s.id === id);
    console.log('Found scenario at index:', scenarioIndex);
    
    if (scenarioIndex !== -1) {
        // Ensure the id is not overwritten by the request body
        const updatedScenario = { ...scenarios[scenarioIndex], ...req.body, id };
        scenarios[scenarioIndex] = updatedScenario;
        
        console.log('Updated scenario:', updatedScenario);
        
        try {
            writeJsonFile(SCENARIOS_PATH, scenarios);
            console.log('Successfully wrote scenarios to file');
            res.json({ success: true, data: updatedScenario });
        } catch (error) {
            console.error('Error writing to file:', error);
            res.status(500).json({ success: false, message: 'Failed to save scenario', error: error.message });
        }
    } else {
        console.error(`Scenario with ID ${id} not found`);
        res.status(404).json({ success: false, message: `Scenario with ID ${id} not found` });
    }
});

// 更新卡片所屬群組
app.put('/api/scenarios/:id/group', (req, res) => {
    console.log('PUT /api/scenarios/:id/group - Request params:', req.params);
    console.log('PUT /api/scenarios/:id/group - Request body:', req.body);
    
    const { id } = req.params;
    const { groupId } = req.body;
    
    // 驗證請求參數
    if (!id || id.trim() === '') {
        console.error('Invalid scenario ID provided:', id);
        return res.status(400).json({ 
            success: false, 
            message: 'Invalid scenario ID provided',
            error: 'INVALID_SCENARIO_ID'
        });
    }
    
    console.log(`Updating scenario ${id} to group ${groupId || 'null'}`);
    console.log('Available scenario IDs:', scenarios.map(s => s.id));
    
    // 查找場景索引
    const scenarioIndex = scenarios.findIndex(s => s.id === id);
    console.log('Found scenario at index:', scenarioIndex);
    
    if (scenarioIndex !== -1) {
        // 保存原始狀態以便錯誤時恢復
        const originalScenario = { ...scenarios[scenarioIndex] };
        
        // 更新場景的群組ID
        const updatedScenario = { 
            ...scenarios[scenarioIndex], 
            groupId: groupId === "" ? null : groupId  // 空字符串轉換為 null
        };
        scenarios[scenarioIndex] = updatedScenario;
        
        console.log('Updated scenario:', updatedScenario);
        
        try {
            writeJsonFile(SCENARIOS_PATH, scenarios);
            console.log('Successfully wrote scenarios to file after group update');
            res.json({ 
                success: true, 
                data: updatedScenario,
                message: 'Scenario group updated successfully'
            });
        } catch (error) {
            console.error('Error writing to file after group update:', error);
            // 恢復原始狀態
            scenarios[scenarioIndex] = originalScenario;
            res.status(500).json({ 
                success: false, 
                message: 'Failed to update scenario group - file write error', 
                error: error.message,
                errorCode: 'FILE_WRITE_ERROR'
            });
        }
    } else {
        console.error(`Scenario with ID ${id} not found for group update`);
        console.error('Available scenarios:', scenarios.map(s => ({ id: s.id, title: s.title })));
        res.status(404).json({ 
            success: false, 
            message: `Scenario with ID ${id} not found for group update`,
            error: 'SCENARIO_NOT_FOUND',
            availableIds: scenarios.map(s => s.id)
        });
    }
});

app.delete('/api/scenarios/:id', (req, res) => {
    const { id } = req.params;
    const scenarioIndex = scenarios.findIndex(s => s.id === id);
    if (scenarioIndex !== -1) {
        scenarios.splice(scenarioIndex, 1);
        writeJsonFile(SCENARIOS_PATH, scenarios);
        res.status(204).send();
    } else {
        res.status(404).json({ success: false, message: 'Scenario not found' });
    }
});

app.put('/api/scenarios/reorder', (req, res) => {
    const { scenarios: updatedScenarios } = req.body;
    if (!Array.isArray(updatedScenarios)) {
        return res.status(400).json({ success: false, message: 'Invalid data format' });
    }
    scenarios = updatedScenarios;
    writeJsonFile(SCENARIOS_PATH, scenarios);
    res.json({ success: true });
});

// Duplicate route removed - using the complete implementation above

// --- Groups API ---
app.get('/api/groups', (req, res) => {
    res.json({ data: groups });
});

app.post('/api/groups', (req, res) => {
    const newGroup = { ...req.body, id: `group-${Date.now()}` };
    groups.push(newGroup);
    writeJsonFile(GROUPS_PATH, groups);
    res.status(201).json({ success: true, data: newGroup });
});

app.put('/api/groups/:id', (req, res) => {
    const { id } = req.params;
    const { name } = req.body;
    const groupIndex = groups.findIndex(g => g.id === id);
    if (groupIndex !== -1) {
        groups[groupIndex].name = name;
        writeJsonFile(GROUPS_PATH, groups);
        res.json({ success: true, data: groups[groupIndex] });
    } else {
        res.status(404).json({ success: false, message: 'Group not found' });
    }
});

app.delete('/api/groups/:id', (req, res) => {
    const { id } = req.params;
    const groupIndex = groups.findIndex(g => g.id === id);
    if (groupIndex !== -1) {
        groups.splice(groupIndex, 1);
        // Un-group scenarios associated with this group
        scenarios = scenarios.map(s => s.groupId === id ? { ...s, groupId: null } : s);
        writeJsonFile(GROUPS_PATH, groups);
        writeJsonFile(SCENARIOS_PATH, scenarios);
        res.status(204).send();
    } else {
        res.status(404).json({ success: false, message: 'Group not found' });
    }
});

// --- AI Service Proxy ---
app.post('/api/ask', async (req, res) => {
    try {
        const response = await fetch('http://localhost:8000/api/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(req.body),
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Error proxying to AI service:', error);
        res.status(500).send('Error proxying to AI service');
    }
});

app.listen(port, () => {
    console.log(`app-server listening at http://localhost:${port}`);
});
