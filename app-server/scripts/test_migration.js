#!/usr/bin/env node

/**
 * 簡化版遷移測試腳本
 * 用於診斷遷移問題
 */

import fs from 'fs';
import path from 'path';
import Database from 'better-sqlite3';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PROJECT_ROOT = path.join(__dirname, '..');
const DB_PATH = path.join(PROJECT_ROOT, 'sqlite', 'db.sqlite');
const SCHEMA_PATH = path.join(PROJECT_ROOT, 'sqlite', 'schema.sql');

console.log('🔍 診斷遷移問題...');
console.log('專案根目錄:', PROJECT_ROOT);
console.log('資料庫路徑:', DB_PATH);
console.log('Schema 路徑:', SCHEMA_PATH);

try {
    // 1. 檢查檔案是否存在
    console.log('\n📁 檢查檔案存在性:');
    console.log('Schema 檔案存在:', fs.existsSync(SCHEMA_PATH));
    console.log('資料庫檔案存在:', fs.existsSync(DB_PATH));
    
    // 2. 刪除舊的資料庫檔案
    if (fs.existsSync(DB_PATH)) {
        fs.unlinkSync(DB_PATH);
        console.log('🗑️ 已刪除舊的資料庫檔案');
    }
    
    // 3. 建立新的資料庫
    console.log('\n🔨 建立新資料庫...');
    const db = new Database(DB_PATH);
    console.log('✅ 資料庫連線成功');
    
    // 4. 讀取並執行 schema
    console.log('\n📜 執行 Schema...');
    const schema = fs.readFileSync(SCHEMA_PATH, 'utf8');
    console.log('Schema 內容長度:', schema.length);
    
    db.exec(schema);
    console.log('✅ Schema 執行成功');
    
    // 5. 驗證表格是否建立
    console.log('\n🔍 驗證表格建立:');
    const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all();
    console.log('建立的表格:', tables.map(t => t.name));
    
    // 6. 測試插入資料
    console.log('\n🧪 測試插入資料...');
    const insertGroup = db.prepare('INSERT INTO groups (id, name, order_index) VALUES (?, ?, ?)');
    insertGroup.run('test-group', '測試群組', 0);
    
    const groupCount = db.prepare('SELECT COUNT(*) as count FROM groups').get();
    console.log('群組數量:', groupCount.count);
    
    db.close();
    console.log('\n🎉 診斷完成，資料庫功能正常！');
    
} catch (error) {
    console.error('\n❌ 診斷過程發生錯誤:', error.message);
    console.error('錯誤詳情:', error);
}
