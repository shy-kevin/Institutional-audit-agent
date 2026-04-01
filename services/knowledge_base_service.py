"""
知识库服务模块
调用外部知识库在线管理平台的API接口
"""

import asyncio
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models.knowledge_base import KnowledgeBase
from services.knowledge_api_client import knowledge_api_client
from utils.logger import setup_logger

logger = setup_logger(__name__)


class KnowledgeBaseService:
    """
    知识库服务类
    
    调用外部知识库在线管理平台的API接口，
    提供知识库的创建、查询、更新、删除等操作
    """
    
    def __init__(self, db: Session):
        """
        初始化知识库服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        logger.debug("知识库服务初始化完成")
    
    async def create_knowledge_base(
        self,
        name: str,
        file_path: str,
        file_name: str,
        description: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> KnowledgeBase:
        """
        创建知识库
        
        先在本地数据库创建记录，然后调用外部API上传文档
        
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
    
    async def process_knowledge_base_file(self, knowledge_base_id: int) -> bool:
        """
        处理知识库文件，调用外部API上传并解析
        
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
            with open(knowledge_base.file_path, 'rb') as f:
                file_content = f.read()
            
            upload_result = await knowledge_api_client.upload_document(
                file_content=file_content,
                filename=knowledge_base.file_name
            )
            
            if not upload_result.get("success"):
                error_msg = upload_result.get("error", "上传失败")
                knowledge_base.status = "failed"
                knowledge_base.description = (knowledge_base.description or "") + f" [错误: {error_msg}]"
                self.db.commit()
                logger.error(f"知识库处理失败 - ID: {knowledge_base_id}, 原因: {error_msg}")
                return False
            
            file_id = upload_result.get("file_id")
            knowledge_base.external_file_id = file_id
            logger.info(f"文档上传成功 - file_id: {file_id}")
            
            parse_result = await knowledge_api_client.parse_document(
                file_id=file_id,
                filename=knowledge_base.file_name,
                department=knowledge_base.description
            )
            
            if not parse_result.get("success"):
                error_msg = parse_result.get("error", "解析失败")
                knowledge_base.status = "failed"
                knowledge_base.description = (knowledge_base.description or "") + f" [错误: {error_msg}]"
                self.db.commit()
                logger.error(f"知识库处理失败 - ID: {knowledge_base_id}, 原因: {error_msg}")
                return False
            
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
    
    async def get_all_knowledge_bases(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        获取所有知识库列表
        
        调用外部API获取文档列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            status: 按状态筛选
        
        Returns:
            tuple[List[Dict], int]: (知识库列表, 总数)
        """
        logger.debug(f"查询知识库列表 - skip: {skip}, limit: {limit}, status: {status}")
        
        try:
            result = await knowledge_api_client.get_all_documents()
            
            documents = []
            if isinstance(result, list):
                documents = result
            elif isinstance(result, dict):
                if not result.get("success", True):
                    logger.error(f"获取文档列表失败: {result.get('error')}")
                    return [], 0
                documents = result.get("results", result.get("items", []))
            
            knowledge_bases = []
            for doc in documents:
                doc_status = doc.get("status", "active")
                if status and doc_status != status:
                    continue
                
                kb_data = {
                    "id": doc.get("id"),
                    "external_id": doc.get("id"),
                    "name": doc.get("title") or doc.get("filename", "未命名"),
                    "description": doc.get("department") or doc.get("summary", ""),
                    "file_name": doc.get("filename", ""),
                    "file_size": doc.get("file_size"),
                    "status": "completed" if doc_status == "active" else doc_status,
                    "created_at": doc.get("created_at") or doc.get("upload_time", ""),
                    "updated_at": doc.get("updated_at") or doc.get("created_at", "")
                }
                knowledge_bases.append(kb_data)
            
            total = len(documents)
            
            logger.info(f"知识库列表查询完成 - 总数: {total}, 返回: {len(knowledge_bases)}")
            return knowledge_bases, total
            
        except Exception as e:
            logger.error(f"获取知识库列表异常: {str(e)}", exc_info=True)
            return [], 0
    
    async def get_knowledge_base_by_external_id(self, external_id: str) -> Optional[Dict[str, Any]]:
        """
        根据外部ID获取知识库详情
        
        Args:
            external_id: 外部文档ID
        
        Returns:
            Optional[Dict]: 知识库详情
        """
        logger.debug(f"查询知识库详情 - external_id: {external_id}")
        
        try:
            result = await knowledge_api_client.get_document(external_id)
            
            if isinstance(result, dict):
                if not result.get("success", True):
                    logger.error(f"获取文档详情失败: {result.get('error')}")
                    return None
                
                doc = result.get("document", result.get("result", result))
            else:
                doc = result
            
            return {
                "external_id": doc.get("id"),
                "name": doc.get("title") or doc.get("filename", "未命名"),
                "description": doc.get("department") or doc.get("summary", ""),
                "file_name": doc.get("filename", ""),
                "file_size": doc.get("file_size"),
                "status": "completed" if doc.get("status") == "active" else doc.get("status", ""),
                "created_at": doc.get("created_at") or doc.get("upload_time", ""),
                "updated_at": doc.get("updated_at") or doc.get("created_at", "")
            }
        except Exception as e:
            logger.error(f"获取知识库详情异常: {str(e)}", exc_info=True)
            return None
    
    async def get_document_detail(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档完整详情
        
        调用外部API获取文档的详细信息，包括内容、切片、元数据等
        
        Args:
            doc_id: 外部文档ID
        
        Returns:
            Optional[Dict]: 文档完整详情
        """
        logger.debug(f"获取文档详情 - doc_id: {doc_id}")
        
        try:
            result = await knowledge_api_client.get_document(doc_id)
            
            if isinstance(result, dict):
                if not result.get("success", True):
                    logger.error(f"获取文档详情失败: {result.get('error')}")
                    return None
                
                doc = result.get("document", result.get("result", result))
                return doc
            else:
                return result
                
        except Exception as e:
            logger.error(f"获取文档详情异常: {str(e)}", exc_info=True)
            return None
    
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
    
    async def delete_knowledge_base(self, knowledge_base_id: int) -> bool:
        """
        删除知识库
        
        调用外部API删除文档，然后删除本地记录
        
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
            if knowledge_base.external_file_id:
                delete_result = await knowledge_api_client.delete_document(
                    knowledge_base.external_file_id
                )
                if not delete_result.get("success"):
                    logger.warning(f"外部API删除文档失败: {delete_result.get('error')}")
            
            self.db.delete(knowledge_base)
            self.db.commit()
            
            logger.info(f"知识库删除成功 - ID: {knowledge_base_id}")
            return True
        except Exception as e:
            logger.error(f"知识库删除失败 - ID: {knowledge_base_id}, 错误: {str(e)}", exc_info=True)
            self.db.rollback()
            return False
    
    async def search_similar_documents(
        self,
        knowledge_base_id: int,
        query: str,
        k: int = 4
    ) -> List[dict]:
        """
        在知识库中搜索相似文档
        
        调用外部API的智能检索接口
        
        Args:
            knowledge_base_id: 知识库ID
            query: 查询文本
            k: 返回的文档数量
        
        Returns:
            List[dict]: 相似文档列表
        """
        logger.debug(f"搜索相似文档 - 知识库ID: {knowledge_base_id}, 查询: {query[:50]}...")
        
        knowledge_base = self.get_knowledge_base_by_id(knowledge_base_id)
        if not knowledge_base or not knowledge_base.external_file_id:
            logger.error(f"知识库不存在或未上传到外部系统 - ID: {knowledge_base_id}")
            return []
        
        try:
            search_result = await knowledge_api_client.search(
                query=query,
                top_k=k,
                search_type="hybrid"
            )
            
            if not search_result.get("success"):
                logger.error(f"检索失败: {search_result.get('error')}")
                return []
            
            results = []
            if isinstance(search_result, list):
                for item in search_result:
                    results.append({
                        "content": item.get("content", ""),
                        "metadata": item.get("metadata", {}),
                        "score": item.get("score", 0)
                    })
            elif isinstance(search_result, dict):
                items = search_result.get("results", search_result.get("items", []))
                for item in items:
                    results.append({
                        "content": item.get("content", ""),
                        "metadata": item.get("metadata", {}),
                        "score": item.get("score", 0)
                    })
            
            logger.info(f"相似文档搜索完成 - 返回文档数: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"检索异常: {str(e)}", exc_info=True)
            return []
    
    async def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        search_type: str = "hybrid"
    ) -> List[dict]:
        """
        通用知识检索
        
        调用外部API的智能检索接口，不限定特定知识库
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            search_type: 检索类型（semantic/keyword/hybrid）
        
        Returns:
            List[dict]: 检索结果列表
        """
        logger.debug(f"知识检索 - 查询: {query[:50]}..., top_k: {top_k}, type: {search_type}")
        
        try:
            search_result = await knowledge_api_client.search(
                query=query,
                top_k=top_k,
                search_type=search_type
            )
            
            if not search_result.get("success"):
                logger.error(f"检索失败: {search_result.get('error')}")
                return []
            
            results = []
            if isinstance(search_result, list):
                for item in search_result:
                    results.append({
                        "content": item.get("content", ""),
                        "metadata": item.get("metadata", {}),
                        "score": item.get("score", 0)
                    })
            elif isinstance(search_result, dict):
                items = search_result.get("results", search_result.get("items", []))
                for item in items:
                    results.append({
                        "content": item.get("content", ""),
                        "metadata": item.get("metadata", {}),
                        "score": item.get("score", 0)
                    })
            
            logger.info(f"知识检索完成 - 返回结果数: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"检索异常: {str(e)}", exc_info=True)
            return []
    
    async def get_task_status(self, file_id: str) -> Dict[str, Any]:
        """
        获取文档解析任务状态
        
        Args:
            file_id: 文件ID
        
        Returns:
            Dict[str, Any]: 任务状态信息
        """
        return await knowledge_api_client.get_task_status(file_id)
    
    async def get_document_chunks(self, doc_id: str) -> Dict[str, Any]:
        """
        获取文档切片
        
        Args:
            doc_id: 文档ID
        
        Returns:
            Dict[str, Any]: 文档切片列表
        """
        return await knowledge_api_client.get_document_chunks(doc_id)
