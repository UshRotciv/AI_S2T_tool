#!/usr/bin/env node

/**
 * 修正版 JSON to SQLite 資料遷移腳本
 * 基於診斷結果的簡化版本
 */

import fs from 'fs';
import path from 'path';
import Database from 'better-sqlite3';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PROJECT_ROOT = path.join(__dirname, '..');
const SCENARIOS_PATH = path.join(PROJECT_ROOT, 'scenarios.json');
const GROUPS_PATH = path.join(PROJECT_ROOT, 'groups.json');
const SCHEMA_PATH = path.join(PROJECT_ROOT, 'sqlite', 'schema.sql');
const DB_PATH = path.join(PROJECT_ROOT, 'sqlite', 'db.sqlite');

console.log('🚀 開始修正版資料遷移...');

async function main() {
    try {
        // 1. 檢查檔案存在性
        console.log('\n📁 檢查檔案...');
        if (!fs.existsSync(SCENARIOS_PATH)) {
            throw new Error(`scenarios.json 不存在: ${SCENARIOS_PATH}`);
        }
        if (!fs.existsSync(GROUPS_PATH)) {
            throw new Error(`groups.json 不存在: ${GROUPS_PATH}`);
        }
        if (!fs.existsSync(SCHEMA_PATH)) {
            throw new Error(`schema.sql 不存在: ${SCHEMA_PATH}`);
        }
        
        console.log('✅ 所有必要檔案都存在');
        
        // 2. 讀取 JSON 資料
        console.log('\n📖 讀取 JSON 資料...');
        const groupsData = JSON.parse(fs.readFileSync(GROUPS_PATH, 'utf8'));
        const scenariosData = JSON.parse(fs.readFileSync(SCENARIOS_PATH, 'utf8'));
        
        console.log(`📋 群組: ${groupsData.data.length} 筆`);
        console.log(`🎯 情境卡片: ${scenariosData.data.length} 筆`);
        
        // 3. 重新建立資料庫
        console.log('\n🔨 重新建立資料庫...');
        if (fs.existsSync(DB_PATH)) {
            fs.unlinkSync(DB_PATH);
            console.log('🗑️ 已刪除舊資料庫');
        }
        
        const db = new Database(DB_PATH);
        console.log('✅ 資料庫連線成功');
        
        // 4. 執行 schema
        console.log('\n📜 執行 Schema...');
        const schema = fs.readFileSync(SCHEMA_PATH, 'utf8');
        db.exec(schema);
        console.log('✅ Schema 執行成功');
        
        // 5. 遷移群組資料
        console.log('\n📋 遷移群組資料...');
        const insertGroup = db.prepare('INSERT INTO groups (id, name, order_index) VALUES (?, ?, ?)');
        
        const groupTransaction = db.transaction((groups) => {
            for (const group of groups) {
                insertGroup.run(group.id, group.name, group.order);
                console.log(`  ✓ ${group.name} (${group.id})`);
            }
        });
        
        groupTransaction(groupsData.data);
        
        // 6. 遷移情境卡片資料
        console.log('\n🎯 遷移情境卡片資料...');
        const insertScenario = db.prepare(`
            INSERT INTO scenarios (id, category, title, question, answer, learnings, group_id, order_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `);
        
        const scenarioTransaction = db.transaction((scenarios) => {
            for (const scenario of scenarios) {
                const learningsJson = scenario.learnings ? JSON.stringify(scenario.learnings) : null;
                insertScenario.run(
                    scenario.id,
                    scenario.category,
                    scenario.title,
                    scenario.question,
                    scenario.answer,
                    learningsJson,
                    scenario.groupId,
                    scenario.order || null
                );
                console.log(`  ✓ ${scenario.title} (${scenario.id})`);
            }
        });
        
        scenarioTransaction(scenariosData.data);
        
        // 7. 驗證結果
        console.log('\n🔍 驗證遷移結果...');
        const groupCount = db.prepare('SELECT COUNT(*) as count FROM groups').get();
        const scenarioCount = db.prepare('SELECT COUNT(*) as count FROM scenarios').get();
        
        console.log(`📊 群組: ${groupCount.count} 筆 (預期: ${groupsData.data.length})`);
        console.log(`🎯 情境卡片: ${scenarioCount.count} 筆 (預期: ${scenariosData.data.length})`);
        
        if (groupCount.count !== groupsData.data.length) {
            throw new Error('群組數量不符');
        }
        if (scenarioCount.count !== scenariosData.data.length) {
            throw new Error('情境卡片數量不符');
        }
        
        // 8. 測試查詢
        console.log('\n🧪 測試查詢功能...');
        const sampleScenario = db.prepare(`
            SELECT s.title, g.name as group_name 
            FROM scenarios s 
            JOIN groups g ON s.group_id = g.id 
            LIMIT 1
        `).get();
        
        console.log(`📝 範例查詢: ${sampleScenario.title} (群組: ${sampleScenario.group_name})`);
        
        db.close();
        
        console.log('\n' + '='.repeat(60));
        console.log('🎉 資料遷移成功完成！');
        console.log('='.repeat(60));
        console.log(`📍 SQLite 資料庫: ${DB_PATH}`);
        console.log('💡 下一步: 更新 app-server/index.js 使用 SQLite');
        
    } catch (error) {
        console.error('\n❌ 遷移失敗:', error.message);
        console.error('詳細錯誤:', error);
        process.exit(1);
    }
}

main();
