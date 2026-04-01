import asyncio
from services.knowledge_base_service import KnowledgeBaseService
from db import get_db

async def test():
    db = next(get_db())
    service = KnowledgeBaseService(db)
    
    result, total = await service.get_all_knowledge_bases(skip=0, limit=5)
    print(f'总数: {total}')
    print(f'返回数量: {len(result)}')
    if result:
        print(f'第一条数据ID: {result[0].get("id")}')
        print(f'第一条数据: {result[0]}')

if __name__ == '__main__':
    asyncio.run(test())
