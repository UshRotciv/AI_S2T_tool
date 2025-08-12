#!/usr/bin/env node

/**
 * JSON to SQLite 資料遷移腳本
 * 用途: 將 scenarios.json 和 groups.json 的資料遷移到 SQLite 資料庫
 * 執行: node scripts/migrate_json_to_sqlite.js
 */

import fs from 'fs';
import path from 'path';
import Database from 'better-sqlite3';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 設定檔案路徑
const PROJECT_ROOT = path.join(__dirname, '..');
const SCENARIOS_PATH = path.join(PROJECT_ROOT, 'scenarios.json');
const GROUPS_PATH = path.join(PROJECT_ROOT, 'groups.json');
const SCHEMA_PATH = path.join(PROJECT_ROOT, 'sqlite', 'schema.sql');
const DB_PATH = path.join(PROJECT_ROOT, 'sqlite', 'db.sqlite');

console.log('🚀 開始 JSON 到 SQLite 資料遷移...');
console.log(`📁 專案根目錄: ${PROJECT_ROOT}`);
console.log(`📄 Scenarios 檔案: ${SCENARIOS_PATH}`);
console.log(`📄 Groups 檔案: ${GROUPS_PATH}`);
console.log(`🗄️ 資料庫檔案: ${DB_PATH}`);

/**
 * 讀取並解析 JSON 檔案
 */
function readJsonFile(filePath) {
    try {
        if (!fs.existsSync(filePath)) {
            throw new Error(`檔案不存在: ${filePath}`);
        }
        const content = fs.readFileSync(filePath, 'utf8');
        return JSON.parse(content);
    } catch (error) {
        console.error(`❌ 讀取檔案失敗: ${filePath}`, error.message);
        process.exit(1);
    }
}

/**
 * 初始化資料庫並執行 schema
 */
function initializeDatabase() {
    try {
        console.log('📊 初始化 SQLite 資料庫...');
        
        // 建立資料庫連線
        const db = new Database(DB_PATH);
        
        // 讀取並執行 schema
        const schema = fs.readFileSync(SCHEMA_PATH, 'utf8');
        db.exec(schema);
        
        console.log('✅ 資料庫初始化完成');
        return db;
    } catch (error) {
        console.error('❌ 資料庫初始化失敗:', error.message);
        process.exit(1);
    }
}

/**
 * 遷移群組資料
 */
function migrateGroups(db, groupsData) {
    console.log('📋 開始遷移群組資料...');
    
    const insertGroup = db.prepare(`
        INSERT OR REPLACE INTO groups (id, name, order_index)
        VALUES (?, ?, ?)
    `);
    
    let migratedCount = 0;
    
    try {
        const transaction = db.transaction((groups) => {
            for (const group of groups) {
                insertGroup.run(group.id, group.name, group.order);
                migratedCount++;
                console.log(`  ✓ 群組: ${group.name} (${group.id})`);
            }
        });
        
        transaction(groupsData.data);
        console.log(`✅ 群組遷移完成，共 ${migratedCount} 筆資料`);
        
    } catch (error) {
        console.error('❌ 群組遷移失敗:', error.message);
        throw error;
    }
}

/**
 * 遷移情境卡片資料
 */
function migrateScenarios(db, scenariosData) {
    console.log('🎯 開始遷移情境卡片資料...');
    
    const insertScenario = db.prepare(`
        INSERT OR REPLACE INTO scenarios 
        (id, category, title, question, answer, learnings, group_id, order_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);
    
    let migratedCount = 0;
    
    try {
        const transaction = db.transaction((scenarios) => {
            for (const scenario of scenarios) {
                // 將 learnings 陣列轉換為 JSON 字串
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
                
                migratedCount++;
                console.log(`  ✓ 情境: ${scenario.title} (${scenario.id})`);
            }
        });
        
        transaction(scenariosData.data);
        console.log(`✅ 情境卡片遷移完成，共 ${migratedCount} 筆資料`);
        
    } catch (error) {
        console.error('❌ 情境卡片遷移失敗:', error.message);
        throw error;
    }
}

/**
 * 驗證遷移結果
 */
function validateMigration(db, originalGroups, originalScenarios) {
    console.log('🔍 驗證遷移結果...');
    
    try {
        // 檢查群組數量
        const groupCount = db.prepare('SELECT COUNT(*) as count FROM groups').get();
        const expectedGroupCount = originalGroups.data.length;
        
        if (groupCount.count !== expectedGroupCount) {
            throw new Error(`群組數量不符: 預期 ${expectedGroupCount}，實際 ${groupCount.count}`);
        }
        
        // 檢查情境卡片數量
        const scenarioCount = db.prepare('SELECT COUNT(*) as count FROM scenarios').get();
        const expectedScenarioCount = originalScenarios.data.length;
        
        if (scenarioCount.count !== expectedScenarioCount) {
            throw new Error(`情境卡片數量不符: 預期 ${expectedScenarioCount}，實際 ${scenarioCount.count}`);
        }
        
        // 檢查外鍵關聯
        const orphanScenarios = db.prepare(`
            SELECT COUNT(*) as count 
            FROM scenarios s 
            LEFT JOIN groups g ON s.group_id = g.id 
            WHERE g.id IS NULL
        `).get();
        
        if (orphanScenarios.count > 0) {
            throw new Error(`發現 ${orphanScenarios.count} 個孤立的情境卡片（無對應群組）`);
        }
        
        console.log('✅ 資料驗證通過');
        console.log(`  📊 群組: ${groupCount.count} 筆`);
        console.log(`  🎯 情境卡片: ${scenarioCount.count} 筆`);
        
    } catch (error) {
        console.error('❌ 資料驗證失敗:', error.message);
        throw error;
    }
}

/**
 * 建立備份
 */
function createBackup() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupDir = path.join(PROJECT_ROOT, 'backup', timestamp);
    
    try {
        // 建立備份目錄
        fs.mkdirSync(backupDir, { recursive: true });
        
        // 備份 JSON 檔案
        if (fs.existsSync(SCENARIOS_PATH)) {
            fs.copyFileSync(SCENARIOS_PATH, path.join(backupDir, 'scenarios.json'));
        }
        if (fs.existsSync(GROUPS_PATH)) {
            fs.copyFileSync(GROUPS_PATH, path.join(backupDir, 'groups.json'));
        }
        
        console.log(`💾 備份已建立: ${backupDir}`);
        return backupDir;
        
    } catch (error) {
        console.warn('⚠️ 備份建立失敗:', error.message);
        return null;
    }
}

/**
 * 主要執行函數
 */
async function main() {
    try {
        console.log('=' .repeat(60));
        console.log('🔄 JSON to SQLite 資料遷移工具');
        console.log('=' .repeat(60));
        
        // 1. 建立備份
        createBackup();
        
        // 2. 讀取原始資料
        console.log('\n📖 讀取原始 JSON 資料...');
        const groupsData = readJsonFile(GROUPS_PATH);
        const scenariosData = readJsonFile(SCENARIOS_PATH);
        
        console.log(`  📋 群組: ${groupsData.data.length} 筆`);
        console.log(`  🎯 情境卡片: ${scenariosData.data.length} 筆`);
        
        // 3. 初始化資料庫
        const db = initializeDatabase();
        
        // 4. 執行遷移
        console.log('\n🚀 開始資料遷移...');
        migrateGroups(db, groupsData);
        migrateScenarios(db, scenariosData);
        
        // 5. 驗證結果
        console.log('\n🔍 驗證遷移結果...');
        validateMigration(db, groupsData, scenariosData);
        
        // 6. 關閉資料庫連線
        db.close();
        
        console.log('\n' + '=' .repeat(60));
        console.log('🎉 資料遷移完成！');
        console.log('=' .repeat(60));
        console.log(`📍 SQLite 資料庫位置: ${DB_PATH}`);
        console.log('💡 下一步: 更新 app-server/index.js 以使用 SQLite');
        
    } catch (error) {
        console.error('\n❌ 遷移過程發生錯誤:', error.message);
        console.error('🔧 請檢查錯誤訊息並修正後重新執行');
        process.exit(1);
    }
}

// 執行主程式
if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}
