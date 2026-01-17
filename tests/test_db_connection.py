"""
测试数据库连接（简化版，不导入其他模块）
"""
import sys
import os

# 直接导入配置模块，避免导入整个 src.services
sys.path.insert(0, 'D:/DeepTutor')

# 设置环境变量
os.environ['DATABASE_URL'] = 'postgresql://deeptutor:deeptutor_password@localhost:5433/deeptutor_memory'

try:
    # 测试数据库连接
    import psycopg2

    print("=" * 60)
    print("[OK] Testing database connection...")
    print("=" * 60)

    conn = psycopg2.connect(
        host='localhost',
        port=5433,
        database='deeptutor_memory',
        user='deeptutor',
        password='deeptutor_password'
    )

    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]

    print(f"PostgreSQL version: {version[:50]}...")

    # 检查表
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = cur.fetchall()

    print("\n[OK] Database tables:")
    for table in tables:
        print(f"  - {table[0]}")

    # 检查 pgvector 扩展
    cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
    pgvector = cur.fetchone()

    if pgvector:
        print("\n[OK] pgvector extension: Installed")
    else:
        print("\n[WARNING] pgvector extension: Not installed")

    cur.close()
    conn.close()

    print("\n" + "=" * 60)
    print("[OK] Database configured successfully!")
    print("=" * 60)
    print("\n[NEXT] Please edit .env.memory file and add your API Keys:")
    print("  - OPENAI_API_KEY=sk-your-key-here")
    print("  OR")
    print("  - DEEPSEEK_API_KEY=sk-your-key-here")
    print("\n[INFO] Edit command:")
    print("  notepad D:\\DeepTutor\\.env.memory")

except Exception as e:
    print(f"\n[ERROR] {e}")
    print("\n[SOLUTION] Try:")
    print("  1. Check Docker: docker ps")
    print("  2. Check port: netstat -ano | findstr :5433")
    print("  3. Restart container: docker-compose -f docker-compose.pgvector.yml restart")
    sys.exit(1)
