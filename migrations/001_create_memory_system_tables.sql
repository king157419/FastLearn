-- DeepTutor Memory System Database Schema
-- Version: 1.0.0
-- Date: 2025-01-17
-- Description: 用户画像、会话摘要、向量嵌入表

-- ============================================
-- Table 1: user_profiles（用户画像）
-- ============================================

CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) UNIQUE NOT NULL,

    -- 学习偏好
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    /*
    示例：
    {
        "learning_style": "code_first",     -- visual | textual | hands_on | code_first
        "difficulty_preference": "intermediate",  -- beginner | intermediate | advanced
        "language": "zh-CN",
        "include_code": true,
        "include_math": true,
        "response_format": "html"           -- text | html | markdown
    }
    */

    -- 学习统计
    statistics JSONB DEFAULT '{}'::jsonb,
    /*
    示例：
    {
        "total_sessions": 42,
        "total_questions": 156,
        "active_days": 15,
        "avg_session_length": 15,           -- 分钟
        "most_active_hour": 20,             -- 24小时制
        "last_active_date": "2025-01-17"
    }
    */

    -- 知识图谱（学习进度）
    knowledge_graph JSONB DEFAULT '{}'::jsonb,
    /*
    示例：
    {
        "梯度下降": {
            "mastery_level": 0.8,           -- 0-1
            "last_reviewed": "2025-01-15T10:30:00Z",
            "interaction_count": 5,
            "confusion_score": 20,          -- 0-100
            "subject": "计算机",
            "topic": "深度学习优化",
            "difficulty": "intermediate"
        },
        "Adam 优化器": {
            "mastery_level": 0.4,
            "last_reviewed": "2025-01-17T09:00:00Z",
            "interaction_count": 3,
            "confusion_score": 75,
            "subject": "计算机",
            "topic": "深度学习优化",
            "difficulty": "intermediate"
        }
    }
    */

    -- 兴趣领域
    interests JSONB DEFAULT '[]'::jsonb,
    /*
    示例：["深度学习", "Python", "数据结构"]
    */

    -- 薄弱知识点列表（冗余存储，加速查询）
    weak_points JSONB DEFAULT '[]'::jsonb,
    /*
    示例：
    [
        {
            "concept": "优化器选择",
            "confusion_score": 75,
            "last_confused": "2025-01-17T10:00:00Z",
            "subject": "计算机",
            "topic": "深度学习优化"
        }
    ]
    */

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT user_preferences_not_null CHECK (preferences IS NOT NULL),
    CONSTRAINT user_id_not_empty CHECK (LENGTH(user_id) > 0)
);

-- 索引
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_created_at ON user_profiles(created_at DESC);
CREATE INDEX idx_user_profiles_updated_at ON user_profiles(updated_at DESC);

-- 注释
COMMENT ON TABLE user_profiles IS '用户画像表：存储用户的学习偏好、统计数据、知识图谱';
COMMENT ON COLUMN user_profiles.user_id IS '用户唯一标识符';
COMMENT ON COLUMN user_profiles.preferences IS '用户学习偏好设置（JSONB）';
COMMENT ON COLUMN user_profiles.statistics IS '学习统计数据（JSONB）';
COMMENT ON COLUMN user_profiles.knowledge_graph IS '知识图谱和掌握度（JSONB）';


-- ============================================
-- Table 2: session_summaries（会话摘要）
-- ============================================

CREATE TABLE IF NOT EXISTS session_summaries (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    user_id VARCHAR(64) NOT NULL,

    -- 摘要内容
    core_topic TEXT NOT NULL,
    key_points JSONB NOT NULL DEFAULT '[]'::jsonb,
    /*
    示例：["梯度下降是基础优化器", "SGD 每次只使用一个样本"]
    */

    resolved_questions JSONB DEFAULT '[]'::jsonb,
    /*
    示例：["什么是梯度", "SGD 和 GD 的区别"]
    */

    unresolved_questions JSONB DEFAULT '[]'::jsonb,
    /*
    示例：["Adam 和 SGD 的具体区别"]
    */

    -- 用户偏好（从对话中提取）
    user_preferences JSONB DEFAULT '{}'::jsonb,
    /*
    示例：
    {
        "style": "代码优先",
        "difficulty": "中等深度",
        "include_math": false
    }
    */

    -- 薄弱知识点（从对话中识别）
    weak_points JSONB DEFAULT '[]'::jsonb,
    /*
    示例：
    [
        {
            "concept": "优化器选择",
            "confusion_score": 75,
            "reason": "用户重复提问 3 次",
            "related_concepts": ["SGD", "Adam", "学习率"]
        }
    ]
    */

    -- 分区字段（加速检索）
    subject VARCHAR(50),
    /*
    示例：数学, 物理, 计算机, 化学, 生物, 经济学
    */

    topic VARCHAR(100),
    /*
    示例：深度学习优化, 线性代数, 数据结构
    */

    difficulty VARCHAR(20),
    /*
    示例：beginner, intermediate, advanced
    */

    -- 最近消息（保留最近 5 条完整消息）
    recent_messages JSONB DEFAULT '[]'::jsonb,
    /*
    示例：
    [
        {"role": "user", "content": "...", "timestamp": 1234567890},
        {"role": "assistant", "content": "...", "timestamp": 1234567891}
    ]
    */

    -- 元数据
    message_count INT DEFAULT 0,
    token_count INT DEFAULT 0,

    -- 摘要质量指标
    summary_quality JSONB DEFAULT '{}'::jsonb,
    /*
    示例：
    {
        "bleu_score": 0.75,
        "compression_ratio": 0.6,      -- 压缩率（新 tokens / 原 tokens）
        "key_points_coverage": 0.85,    -- 关键点覆盖率
        "generated_at": "2025-01-17T10:30:00Z",
        "generated_by": "SummarizerAgent"
    }
    */

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT session_summaries_session_id_not_empty CHECK (LENGTH(session_id) > 0),
    CONSTRAINT session_summaries_user_id_not_empty CHECK (LENGTH(user_id) > 0),
    CONSTRAINT session_summaries_core_topic_not_empty CHECK (LENGTH(core_topic) > 0),
    CONSTRAINT session_summaries_difficulty_check
        CHECK (difficulty IN ('beginner', 'intermediate', 'advanced', NULL))
);

-- 索引（基础索引）
CREATE INDEX idx_session_summaries_session_id ON session_summaries(session_id);
CREATE INDEX idx_session_summaries_user_id ON session_summaries(user_id);
CREATE INDEX idx_session_summaries_created_at ON session_summaries(created_at DESC);

-- 复合索引（加速检索）
CREATE INDEX idx_session_summaries_user_subject ON session_summaries(user_id, subject);
CREATE INDEX idx_session_summaries_user_topic ON session_summaries(user_id, topic);
CREATE INDEX idx_session_summaries_user_difficulty ON session_summaries(user_id, difficulty);
CREATE INDEX idx_session_summaries_user_created ON session_summaries(user_id, created_at DESC);

-- 全文搜索索引（用于关键词检索）
CREATE INDEX idx_session_summaries_core_topic_gin ON session_summaries USING gin(to_tsvector('simple', core_topic));
CREATE INDEX idx_session_summaries_key_points_gin ON session_summaries USING gin(to_tsvector('simple', key_points::text));

-- 注释
COMMENT ON TABLE session_summaries IS '会话摘要表：存储对话摘要、关键知识点、用户偏好';
COMMENT ON COLUMN session_summaries.session_id IS '会话唯一标识符';
COMMENT ON COLUMN session_summaries.core_topic IS '核心主题';
COMMENT ON COLUMN session_summaries.key_points IS '关键知识点列表';
COMMENT ON COLUMN session_summaries.subject IS '学科分类（分区字段）';
COMMENT ON COLUMN session_summaries.topic IS '主题分类（分区字段）';
COMMENT ON COLUMN session_summaries.difficulty IS '难度级别（分区字段）';


-- ============================================
-- Table 3: memory_embeddings（向量嵌入）
-- ============================================

-- 注意：此表需要先安装 pgvector 扩展
-- 安装命令：CREATE EXTENSION IF NOT EXISTS vector;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS memory_embeddings (
    id SERIAL PRIMARY KEY,
    memory_id INTEGER NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(64),

    -- 向量嵌入（1536 维 for OpenAI text-embedding-3-small）
    -- 可以根据选择的 Embedding 模型调整维度
    embedding vector(1536),

    -- 元数据（用于过滤）
    metadata JSONB DEFAULT '{}'::jsonb,
    /*
    示例：
    {
        "subject": "计算机",
        "topic": "深度学习优化",
        "difficulty": "intermediate",
        "created_at": "2025-01-17T10:30:00Z",
        "embedding_model": "text-embedding-3-small",
        "embedding_version": "1.0"
    }
    */

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    CONSTRAINT fk_memory_id
        FOREIGN KEY (memory_id)
        REFERENCES session_summaries(id)
        ON DELETE CASCADE,

    -- 约束
    CONSTRAINT memory_embeddings_memory_id_not_null CHECK (memory_id IS NOT NULL),
    CONSTRAINT memory_embeddings_user_id_not_empty CHECK (LENGTH(user_id) > 0)
);

-- 向量相似度索引（IVFFlat 或 HNSW）
-- IVFFlat：适合静态数据，需要指定索引参数
CREATE INDEX idx_memory_embeddings_embedding_ivfflat
    ON memory_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- HNSW：更适合动态数据，性能更好
-- 如果数据量大（> 100K），使用 HNSW
-- CREATE INDEX idx_memory_embeddings_embedding_hnsw
--     ON memory_embeddings
--     USING hnsw (embedding vector_cosine_ops);

-- 元数据索引（加速过滤）
CREATE INDEX idx_memory_embeddings_user_id ON memory_embeddings(user_id);
CREATE INDEX idx_memory_embeddings_subject ON memory_embeddings((metadata->>'subject'));
CREATE INDEX idx_memory_embeddings_topic ON memory_embeddings((metadata->>'topic'));
CREATE INDEX idx_memory_embeddings_difficulty ON memory_embeddings((metadata->>'difficulty'));
CREATE INDEX idx_memory_embeddings_created_at ON memory_embeddings((metadata->>'created_at'));

-- 复合索引（user_id + subject）
CREATE INDEX idx_memory_embeddings_user_subject
    ON memory_embeddings(user_id, (metadata->>'subject'));

-- 注释
COMMENT ON TABLE memory_embeddings IS '向量嵌入表：用于语义检索，存储会话摘要的向量表示';
COMMENT ON COLUMN memory_embeddings.embedding IS '向量嵌入（1536维）';
COMMENT ON COLUMN memory_embeddings.metadata IS '元数据（用于过滤：学科、主题、难度等）';


-- ============================================
-- 触发器：自动更新 updated_at 字段
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 应用到所有表
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_session_summaries_updated_at
    BEFORE UPDATE ON session_summaries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memory_embeddings_updated_at
    BEFORE UPDATE ON memory_embeddings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- 初始化数据
-- ============================================

-- 创建默认用户（用于测试）
INSERT INTO user_profiles (
    user_id,
    preferences,
    statistics,
    knowledge_graph,
    interests,
    weak_points
) VALUES (
    'test_user_001',
    '{
        "learning_style": "code_first",
        "difficulty_preference": "intermediate",
        "language": "zh-CN",
        "include_code": true,
        "include_math": false,
        "response_format": "html"
    }'::jsonb,
    '{
        "total_sessions": 0,
        "total_questions": 0,
        "active_days": 0,
        "avg_session_length": 0,
        "most_active_hour": null,
        "last_active_date": null
    }'::jsonb,
    '{}'::jsonb,
    '[]'::jsonb,
    '[]'::jsonb
) ON CONFLICT (user_id) DO NOTHING;


-- ============================================
-- 完成提示
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '======================================';
    RAISE NOTICE 'Database Schema Created Successfully!';
    RAISE NOTICE '======================================';
    RAISE NOTICE 'Created Tables:';
    RAISE NOTICE '  1. user_profiles (用户画像)';
    RAISE NOTICE '  2. session_summaries (会话摘要)';
    RAISE NOTICE '  3. memory_embeddings (向量嵌入)';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. 配置 pgvector 扩展（如果还未安装）';
    RAISE NOTICE '  2. 创建数据模型（Python）';
    RAISE NOTICE '  3. 实现 Agent 类';
    RAISE NOTICE '======================================';
END $$;
