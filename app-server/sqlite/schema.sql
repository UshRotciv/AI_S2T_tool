-- SQLite Schema for Confidential Expert AI System
-- 建立時間: 2025-08-12
-- 用途: 將 JSON 檔案資料結構遷移至 SQLite

-- 群組資料表 (對應 groups.json)
CREATE TABLE IF NOT EXISTS groups (
    id TEXT PRIMARY KEY,           -- 群組 ID (如 "group-habits")
    name TEXT NOT NULL,            -- 群組名稱 (如 "辦公室基礎好習慣")
    order_index INTEGER NOT NULL,  -- 排序順序
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 情境卡片資料表 (對應 scenarios.json)
CREATE TABLE IF NOT EXISTS scenarios (
    id TEXT PRIMARY KEY,           -- 情境卡片 ID (如 "scenario-new-001")
    category TEXT NOT NULL,        -- 分類 (如 "Part A: 辦公室基礎好習慣")
    title TEXT NOT NULL,           -- 標題
    question TEXT NOT NULL,        -- 問題內容
    answer TEXT NOT NULL,          -- 答案內容
    learnings TEXT,                -- 學習重點 (JSON 格式儲存陣列)
    group_id TEXT NOT NULL,        -- 所屬群組 ID
    order_index INTEGER,           -- 在群組內的排序
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
);

-- 建立索引以提升查詢效能
CREATE INDEX IF NOT EXISTS idx_scenarios_group_id ON scenarios(group_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_order ON scenarios(group_id, order_index);
CREATE INDEX IF NOT EXISTS idx_scenarios_title ON scenarios(title);
CREATE INDEX IF NOT EXISTS idx_groups_order ON groups(order_index);

-- 建立觸發器以自動更新 updated_at 欄位
CREATE TRIGGER IF NOT EXISTS update_groups_timestamp 
    AFTER UPDATE ON groups
    FOR EACH ROW
BEGIN
    UPDATE groups SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_scenarios_timestamp 
    AFTER UPDATE ON scenarios
    FOR EACH ROW
BEGIN
    UPDATE scenarios SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 建立視圖以方便查詢 (包含群組資訊的完整情境卡片)
CREATE VIEW IF NOT EXISTS scenarios_with_groups AS
SELECT 
    s.id,
    s.category,
    s.title,
    s.question,
    s.answer,
    s.learnings,
    s.order_index as scenario_order,
    s.created_at as scenario_created_at,
    s.updated_at as scenario_updated_at,
    g.id as group_id,
    g.name as group_name,
    g.order_index as group_order
FROM scenarios s
LEFT JOIN groups g ON s.group_id = g.id
ORDER BY g.order_index, s.order_index;
