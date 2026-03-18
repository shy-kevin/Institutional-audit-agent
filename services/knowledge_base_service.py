"""
知识库服务模块
提供知识库的CRUD操作和向量存储管理
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from models.knowledge_base import KnowledgeBase
from db.postgres_session import vector_store_manager
from utils.pdf_parser import PDFParser
from utils.logger import setup_logger

logger = setup_logger(__name__)


class KnowledgeBaseService:
    """
    知识库服务类
    
    提供知识库的创建、查询、更新、删除等操作，
    以及向量存储的管理
    
    Attributes:
        db: 数据库会话
        pdf_parser: PDF解析器
    """
    
    def __init__(self, db: Session):
        """
        初始化知识库服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.pdf_parser = PDFParser()
        logger.debug("知识库服务初始化完成")
    
    def create_knowledge_base(
        self,
        name: str,
        file_path: str,
        file_name: str,
        description: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> KnowledgeBase:
        """
        创建知识库
        
        Args:
            name: 知识库名称
            file_path: 文件存储路径
            file_name: 原始文件名
            description: 知识库描述
            file_size: 文件大小
        
        Returns:
            KnowledgeBase: 创建的知识库对象
        """
        logger.info(f"创建知识库 - 名称: {name}, 文件: {file_name}")
        
        knowledge_base = KnowledgeBase(
            name=name,
            description=description,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            status="processing"
        )
        self.db.add(knowledge_base)
        self.db.commit()
        self.db.refresh(knowledge_base)
        
        logger.info(f"知识库创建成功 - ID: {knowledge_base.id}")
        return knowledge_base
    
    def process_knowledge_base_file(self, knowledge_base_id: int) -> bool:
        """
        处理知识库文件，解析并向量化存储
        
        Args:
            knowledge_base_id: 知识库ID
        
        Returns:
            bool: 处理是否成功
        """
        logger.info(f"开始处理知识库文件 - ID: {knowledge_base_id}")
        
        knowledge_base = self.get_knowledge_base_by_id(knowledge_base_id)
        if not knowledge_base:
            logger.error(f"知识库不存在 - ID: {knowledge_base_id}")
            return False
        
        try:
            logger.debug(f"解析PDF文件 - 路径: {knowledge_base.file_path}")
            documents = self.pdf_parser.parse_pdf_to_documents(
                knowledge_base.file_path,
                metadata={"knowledge_base_id": knowledge_base_id}
            )
            
            if not documents:
                error_msg = "PDF解析失败，无法提取文本内容"
                knowledge_base.status = "failed"
                knowledge_base.description = (knowledge_base.description or "") + f" [错误: {error_msg}]"
                self.db.commit()
                logger.error(f"知识库处理失败 - ID: {knowledge_base_id}, 原因: {error_msg}")
                return False
            
            logger.info(f"PDF解析成功 - 提取文档数: {len(documents)}")
            
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            collection_name = f"kb_{knowledge_base_id}"
            logger.debug(f"创建向量存储 - 集合名: {collection_name}")
            
            vector_store_manager.create_vector_store(
                collection_name=collection_name,
                texts=texts,
                metadatas=metadatas
            )
            
            knowledge_base.status = "completed"
            self.db.commit()
            
            logger.info(f"知识库处理完成 - ID: {knowledge_base_id}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"知识库处理异常 - ID: {knowledge_base_id}, 错误: {error_msg}", exc_info=True)
            
            knowledge_base.status = "failed"
            knowledge_base.description = (knowledge_base.description or "") + f" [错误: {error_msg}]"
            self.db.commit()
            return False
    
    def get_knowledge_base_by_id(self, knowledge_base_id: int) -> Optional[KnowledgeBase]:
        """
        根据ID获取知识库
        
        Args:
            knowledge_base_id: 知识库ID
        
        Returns:
            Optional[KnowledgeBase]: 知识库对象，不存在则返回None
        """
        logger.debug(f"查询知识库 - ID: {knowledge_base_id}")
        
        result = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.id == knowledge_base_id
        ).first()
        
        if result:
            logger.debug(f"知识库查询成功 - ID: {knowledge_base_id}")
        else:
            logger.debug(f"知识库不存在 - ID: {knowledge_base_id}")
        
        return result
    
    def get_all_knowledge_bases(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> tuple[List[KnowledgeBase], int]:
        """
        获取所有知识库列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            status: 按状态筛选
        
        Returns:
            tuple[List[KnowledgeBase], int]: (知识库列表, 总数)
        """
        logger.debug(f"查询知识库列表 - skip: {skip}, limit: {limit}, status: {status}")
        
        query = self.db.query(KnowledgeBase)
        
        if status:
            query = query.filter(KnowledgeBase.status == status)
        
        total = query.count()
        knowledge_bases = query.order_by(
            KnowledgeBase.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        logger.info(f"知识库列表查询完成 - 总数: {total}, 返回: {len(knowledge_bases)}")
        return knowledge_bases, total
    
    def update_knowledge_base(
        self,
        knowledge_base_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[KnowledgeBase]:
        """
        更新知识库信息
        
        Args:
            knowledge_base_id: 知识库ID
            name: 新名称
            description: 新描述
        
        Returns:
            Optional[KnowledgeBase]: 更新后的知识库对象
        """
        logger.info(f"更新知识库 - ID: {knowledge_base_id}")
        
        knowledge_base = self.get_knowledge_base_by_id(knowledge_base_id)
        if not knowledge_base:
            logger.error(f"知识库不存在 - ID: {knowledge_base_id}")
            return None
        
        if name is not None:
            knowledge_base.name = name
        if description is not None:
            knowledge_base.description = description
        
        self.db.commit()
        self.db.refresh(knowledge_base)
        
        logger.info(f"知识库更新成功 - ID: {knowledge_base_id}")
        return knowledge_base
    
    def delete_knowledge_base(self, knowledge_base_id: int) -> bool:
        """
        删除知识库
        
        Args:
            knowledge_base_id: 知识库ID
        
        Returns:
            bool: 删除是否成功
        """
        logger.info(f"删除知识库 - ID: {knowledge_base_id}")
        
        knowledge_base = self.get_knowledge_base_by_id(knowledge_base_id)
        if not knowledge_base:
            logger.error(f"知识库不存在 - ID: {knowledge_base_id}")
            return False
        
        try:
            collection_name = f"kb_{knowledge_base_id}"
            logger.debug(f"删除向量存储 - 集合名: {collection_name}")
            vector_store_manager.delete_vector_store(collection_name)
            
            self.db.delete(knowledge_base)
            self.db.commit()
            
            logger.info(f"知识库删除成功 - ID: {knowledge_base_id}")
            return True
        except Exception as e:
            logger.error(f"知识库删除失败 - ID: {knowledge_base_id}, 错误: {str(e)}", exc_info=True)
            self.db.rollback()
            return False
    
    def search_similar_documents(
        self,
        knowledge_base_id: int,
        query: str,
        k: int = 4
    ) -> List[dict]:
        """
        在知识库中搜索相似文档
        
        Args:
            knowledge_base_id: 知识库ID
            query: 查询文本
            k: 返回的文档数量
        
        Returns:
            List[dict]: 相似文档列表
        """
        logger.debug(f"搜索相似文档 - 知识库ID: {knowledge_base_id}, 查询: {query[:50]}...")
        
        collection_name = f"kb_{knowledge_base_id}"
        vector_store = vector_store_manager.get_vector_store(collection_name)
        
        results = vector_store.similarity_search_with_score(query, k=k)
        
        logger.info(f"相似文档搜索完成 - 返回文档数: {len(results)}")
        
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            }
            for doc, score in results
        ]
