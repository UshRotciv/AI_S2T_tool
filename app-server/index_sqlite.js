import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import Database from 'better-sqlite3';
import axios from 'axios';
import dotenv from 'dotenv';
import morgan from 'morgan';
import { nanoid } from 'nanoid';
import path from 'path';
import { fileURLToPath } from 'url';

// 載入環境變數
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = process.env.APP_PORT || 3001;

// 中間件設定
app.use(cors());
app.use(bodyParser.json());
app.use(morgan('combined')); // 請求日誌

// SQLite 資料庫設定
const DB_PATH = process.env.SQLITE_DB_PATH || path.join(__dirname, 'sqlite', 'db.sqlite');
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8001';

console.log(`📊 SQLite 資料庫路徑: ${DB_PATH}`);
console.log(`🤖 AI 服務 URL: ${AI_SERVICE_URL}`);

// 初始化資料庫連線
let db;
try {
    db = new Database(DB_PATH);
    console.log('✅ SQLite 資料庫連線成功');
    
    // 設定 WAL 模式以提升併發效能
    db.pragma('journal_mode = WAL');
    db.pragma('synchronous = NORMAL');
    
} catch (error) {
    console.error('❌ SQLite 資料庫連線失敗:', error.message);
    process.exit(1);
}

// 準備 SQL 語句
const queries = {
    // Groups 查詢
    getAllGroups: db.prepare('SELECT * FROM groups ORDER BY order_index'),
    getGroupById: db.prepare('SELECT * FROM groups WHERE id = ?'),
    insertGroup: db.prepare('INSERT INTO groups (id, name, order_index) VALUES (?, ?, ?)'),
    updateGroup: db.prepare('UPDATE groups SET name = ?, order_index = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'),
    deleteGroup: db.prepare('DELETE FROM groups WHERE id = ?'),
    
    // Scenarios 查詢
    getAllScenarios: db.prepare(`
        SELECT s.*, g.name as group_name 
        FROM scenarios s 
        LEFT JOIN groups g ON s.group_id = g.id 
        ORDER BY g.order_index, s.order_index
    `),
    getScenarioById: db.prepare('SELECT * FROM scenarios WHERE id = ?'),
    getScenariosByGroupId: db.prepare('SELECT * FROM scenarios WHERE group_id = ? ORDER BY order_index'),
    insertScenario: db.prepare(`
        INSERT INTO scenarios (id, category, title, question, answer, learnings, group_id, order_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `),
    updateScenario: db.prepare(`
        UPDATE scenarios 
        SET category = ?, title = ?, question = ?, answer = ?, learnings = ?, group_id = ?, order_index = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    `),
    updateScenarioGroup: db.prepare('UPDATE scenarios SET group_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'),
    deleteScenario: db.prepare('DELETE FROM scenarios WHERE id = ?'),
    
    // 統計查詢
    getScenarioCount: db.prepare('SELECT COUNT(*) as count FROM scenarios'),
    getGroupCount: db.prepare('SELECT COUNT(*) as count FROM groups')
};

/**
 * 呼叫 AI 服務同步端點
 */
async function syncToAIService(operation, data) {
    try {
        console.log(`🔄 同步到 AI 服務: ${operation}`, data);
        
        const response = await axios.post(`${AI_SERVICE_URL}/api/sync`, {
            operation,
            data
        }, {
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log('✅ AI 服務同步成功:', response.data);
        return response.data;
        
    } catch (error) {
        console.error('❌ AI 服務同步失敗:', error.message);
        // 不拋出錯誤，避免影響主要 CRUD 操作
        return { success: false, error: error.message };
    }
}

/**
 * 將 scenarios 資料轉換為 AI 服務格式
 */
function formatScenarioForAI(scenario) {
    return {
        id: scenario.id,
        title: scenario.title,
        body: `${scenario.question}\n\n${scenario.answer}`,
        group_id: scenario.group_id,
        updated_at: scenario.updated_at || new Date().toISOString()
    };
}

// --- Health Check ---
app.get('/health', (req, res) => {
    try {
        // 測試資料庫連線
        const groupCount = queries.getGroupCount.get();
        const scenarioCount = queries.getScenarioCount.get();
        
        res.json({
            status: 'healthy',
            timestamp: new Date().toISOString(),
            database: {
                connected: true,
                groups: groupCount.count,
                scenarios: scenarioCount.count
            }
        });
    } catch (error) {
        res.status(500).json({
            status: 'unhealthy',
            error: error.message
        });
    }
});

// --- Groups API ---
app.get('/api/groups', (req, res) => {
    try {
        const groups = queries.getAllGroups.all();
        res.json({ data: groups });
    } catch (error) {
        console.error('Error fetching groups:', error);
        res.status(500).json({ success: false, message: 'Failed to fetch groups' });
    }
});

app.post('/api/groups', async (req, res) => {
    try {
        const { name, order } = req.body;
        const id = `group-${nanoid(8)}`;
        
        queries.insertGroup.run(id, name, order || 0);
        
        const newGroup = queries.getGroupById.get(id);
        res.status(201).json({ success: true, data: newGroup });
        
    } catch (error) {
        console.error('Error creating group:', error);
        res.status(500).json({ success: false, message: 'Failed to create group' });
    }
});

app.put('/api/groups/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const { name, order } = req.body;
        
        const result = queries.updateGroup.run(name, order || 0, id);
        
        if (result.changes === 0) {
            return res.status(404).json({ success: false, message: 'Group not found' });
        }
        
        const updatedGroup = queries.getGroupById.get(id);
        res.json({ success: true, data: updatedGroup });
        
    } catch (error) {
        console.error('Error updating group:', error);
        res.status(500).json({ success: false, message: 'Failed to update group' });
    }
});

app.delete('/api/groups/:id', async (req, res) => {
    try {
        const { id } = req.params;
        
        // 檢查是否有關聯的 scenarios
        const relatedScenarios = queries.getScenariosByGroupId.all(id);
        if (relatedScenarios.length > 0) {
            return res.status(400).json({ 
                success: false, 
                message: `Cannot delete group with ${relatedScenarios.length} associated scenarios` 
            });
        }
        
        const result = queries.deleteGroup.run(id);
        
        if (result.changes === 0) {
            return res.status(404).json({ success: false, message: 'Group not found' });
        }
        
        res.json({ success: true, message: 'Group deleted successfully' });
        
    } catch (error) {
        console.error('Error deleting group:', error);
        res.status(500).json({ success: false, message: 'Failed to delete group' });
    }
});

// --- Scenarios API ---
app.get('/api/scenarios', (req, res) => {
    try {
        const scenarios = queries.getAllScenarios.all();
        
        // 將 learnings JSON 字串轉換回陣列
        const processedScenarios = scenarios.map(scenario => ({
            ...scenario,
            learnings: scenario.learnings ? JSON.parse(scenario.learnings) : []
        }));
        
        res.json({ data: processedScenarios });
    } catch (error) {
        console.error('Error fetching scenarios:', error);
        res.status(500).json({ success: false, message: 'Failed to fetch scenarios' });
    }
});

app.post('/api/scenarios', async (req, res) => {
    try {
        const { category, title, question, answer, learnings, groupId, order } = req.body;
        const id = `scenario-${nanoid(8)}`;
        
        const learningsJson = learnings ? JSON.stringify(learnings) : null;
        
        queries.insertScenario.run(
            id, category, title, question, answer, learningsJson, groupId, order || null
        );
        
        const newScenario = queries.getScenarioById.get(id);
        
        // 同步到 AI 服務
        await syncToAIService('upsert', [formatScenarioForAI(newScenario)]);
        
        res.status(201).json({ success: true, data: newScenario });
        
    } catch (error) {
        console.error('Error creating scenario:', error);
        res.status(500).json({ success: false, message: 'Failed to create scenario' });
    }
});

app.put('/api/scenarios/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const { category, title, question, answer, learnings, groupId, order } = req.body;
        
        console.log(`PUT /api/scenarios/${id} - Request body:`, req.body);
        
        const learningsJson = learnings ? JSON.stringify(learnings) : null;
        
        const result = queries.updateScenario.run(
            category, title, question, answer, learningsJson, groupId, order || null, id
        );
        
        if (result.changes === 0) {
            return res.status(404).json({ success: false, message: 'Scenario not found' });
        }
        
        const updatedScenario = queries.getScenarioById.get(id);
        
        // 同步到 AI 服務
        await syncToAIService('upsert', [formatScenarioForAI(updatedScenario)]);
        
        console.log('Updated scenario:', updatedScenario);
        res.json({ success: true, data: updatedScenario });
        
    } catch (error) {
        console.error('Error updating scenario:', error);
        res.status(500).json({ success: false, message: 'Failed to update scenario' });
    }
});

app.put('/api/scenarios/:id/group', async (req, res) => {
    try {
        const { id } = req.params;
        const { groupId } = req.body;
        
        console.log(`PUT /api/scenarios/${id}/group - Moving to group: ${groupId}`);
        
        const result = queries.updateScenarioGroup.run(groupId, id);
        
        if (result.changes === 0) {
            return res.status(404).json({ success: false, message: 'Scenario not found' });
        }
        
        const updatedScenario = queries.getScenarioById.get(id);
        
        // 同步到 AI 服務
        await syncToAIService('upsert', [formatScenarioForAI(updatedScenario)]);
        
        res.json({ success: true, data: updatedScenario });
        
    } catch (error) {
        console.error('Error moving scenario to group:', error);
        res.status(500).json({ success: false, message: 'Failed to move scenario to group' });
    }
});

app.delete('/api/scenarios/:id', async (req, res) => {
    try {
        const { id } = req.params;
        
        const result = queries.deleteScenario.run(id);
        
        if (result.changes === 0) {
            return res.status(404).json({ success: false, message: 'Scenario not found' });
        }
        
        // 同步到 AI 服務
        await syncToAIService('delete', { ids: [id] });
        
        res.json({ success: true, message: 'Scenario deleted successfully' });
        
    } catch (error) {
        console.error('Error deleting scenario:', error);
        res.status(500).json({ success: false, message: 'Failed to delete scenario' });
    }
});

// --- AI Ask API (代理到 AI 服務) ---
app.post('/api/ask', async (req, res) => {
    try {
        const response = await axios.post(`${AI_SERVICE_URL}/api/ask`, req.body, {
            timeout: 30000,
            headers: { 'Content-Type': 'application/json' }
        });
        
        res.json(response.data);
        
    } catch (error) {
        console.error('Error forwarding to AI service:', error.message);
        res.status(500).json({ 
            success: false, 
            message: 'AI service unavailable',
            error: error.message 
        });
    }
});

// --- 統計 API ---
app.get('/api/stats', (req, res) => {
    try {
        const groupCount = queries.getGroupCount.get();
        const scenarioCount = queries.getScenarioCount.get();
        
        res.json({
            groups: groupCount.count,
            scenarios: scenarioCount.count,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Error fetching stats:', error);
        res.status(500).json({ success: false, message: 'Failed to fetch stats' });
    }
});

// 優雅關閉處理
process.on('SIGINT', () => {
    console.log('\n🔄 正在關閉伺服器...');
    if (db) {
        db.close();
        console.log('✅ SQLite 資料庫連線已關閉');
    }
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🔄 正在關閉伺服器...');
    if (db) {
        db.close();
        console.log('✅ SQLite 資料庫連線已關閉');
    }
    process.exit(0);
});

// 啟動伺服器
app.listen(port, () => {
    console.log('='.repeat(60));
    console.log('🚀 App Server (SQLite 版本) 已啟動');
    console.log('='.repeat(60));
    console.log(`📍 伺服器位址: http://localhost:${port}`);
    console.log(`📊 資料庫: SQLite (${DB_PATH})`);
    console.log(`🤖 AI 服務: ${AI_SERVICE_URL}`);
    console.log(`🔍 健康檢查: http://localhost:${port}/health`);
    console.log('='.repeat(60));
});
