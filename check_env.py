"""
检查PostgreSQL pgvector扩展是否安装
"""

import psycopg2
from config import settings


def check_pgvector():
    """
    检查pgvector扩展是否已安装
    """
    try:
        connection = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DATABASE
        )
        
        cursor = connection.cursor()
        
        # 检查pgvector扩展是否已安装
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        
        if result:
            print("✅ pgvector扩展已安装")
        else:
            print("❌ pgvector扩展未安装，正在尝试安装...")
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                connection.commit()
                print("✅ pgvector扩展安装成功")
            except Exception as e:
                print(f"❌ pgvector扩展安装失败: {e}")
                print("请手动在PostgreSQL中执行: CREATE EXTENSION vector;")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 连接PostgreSQL失败: {e}")


def check_ollama():
    """
    检查Ollama服务是否可用
    """
    import httpx
    
    try:
        response = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5.0)
        if response.status_code == 200:
            print(f"✅ Ollama服务可用: {settings.OLLAMA_BASE_URL}")
            models = response.json().get("models", [])
            if models:
                print(f"   可用模型: {[m['name'] for m in models]}")
            else:
                print("   ⚠️ 没有可用的模型，请先拉取模型")
        else:
            print(f"❌ Ollama服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ Ollama服务不可用: {settings.OLLAMA_BASE_URL}")
        print(f"   错误: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("环境检查")
    print("=" * 50)
    
    print("\n1. 检查PostgreSQL pgvector扩展...")
    check_pgvector()
    
    print("\n2. 检查Ollama服务...")
    check_ollama()
    
    print("\n" + "=" * 50)
