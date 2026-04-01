"""
外部知识库API客户端
调用知识库在线管理平台的API接口
"""

import httpx
from typing import Optional, List, Dict, Any
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class KnowledgeApiClient:
    """
    知识库API客户端
    
    调用外部知识库在线管理平台的API接口
    """
    
    def __init__(self):
        self.base_url = settings.KNOWLEDGE_API_URL
        self.timeout = settings.KNOWLEDGE_API_TIMEOUT
        self.api_key = settings.KNOWLEDGE_API_KEY
    
    def _get_headers(self) -> Dict[str, str]:
        """
        获取请求头
        
        Returns:
            Dict[str, str]: 请求头字典
        """
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict] = None,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            json: JSON数据
            data: 表单数据
            files: 文件数据
        
        Returns:
            Dict[str, Any]: 响应数据
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        if files:
            headers.pop("Content-Type", None)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                    data=data,
                    files=files
                )
                
                if response.status_code >= 400:
                    error_text = response.text
                    logger.error(f"API请求失败: {method} {url}, 状态码: {response.status_code}, 错误: {error_text}")
                    return {
                        "success": False,
                        "error": f"API请求失败: {response.status_code}",
                        "detail": error_text
                    }
                
                return response.json()
                
        except httpx.TimeoutException:
            logger.error(f"API请求超时: {method} {url}")
            return {"success": False, "error": "请求超时"}
        except Exception as e:
            logger.error(f"API请求异常: {method} {url}, 错误: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def upload_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        上传文档到知识库
        
        Args:
            file_content: 文件内容（字节）
            filename: 文件名
        
        Returns:
            Dict[str, Any]: 上传结果，包含file_id等信息
        """
        logger.info(f"上传文档: {filename}")
        
        files = {
            "file": (filename, file_content)
        }
        data = {
            "name": filename
        }
        
        result = await self._request("POST", "/api/documents/upload", data=data, files=files)
        
        if result.get("success"):
            logger.info(f"文档上传成功: file_id={result.get('file_id')}")
        else:
            logger.error(f"文档上传失败: {result.get('error')}")
        
        return result
    
    async def parse_document(
        self,
        file_id: str,
        filename: str,
        department: Optional[str] = None,
        regulation_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        effective_date: Optional[str] = None,
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        解析文档并生成向量
        
        Args:
            file_id: 文件ID
            filename: 文件名
            department: 部门
            regulation_type: 制度类型
            tags: 标签列表
            effective_date: 生效日期
            source: 来源
        
        Returns:
            Dict[str, Any]: 解析结果
        """
        logger.info(f"解析文档: file_id={file_id}, filename={filename}")
        
        data = {
            "file_id": file_id,
            "filename": filename
        }
        
        if department:
            data["department"] = department
        if regulation_type:
            data["regulation_type"] = regulation_type
        if tags:
            data["tags"] = tags
        if effective_date:
            data["effective_date"] = effective_date
        if source:
            data["source"] = source
        
        result = await self._request("POST", "/api/documents/parse", json=data)
        logger.info(f"文档解析请求已提交: {result}")
        
        return result
    
    async def get_task_status(self, file_id: str) -> Dict[str, Any]:
        """
        获取文档解析任务状态
        
        Args:
            file_id: 文件ID
        
        Returns:
            Dict[str, Any]: 任务状态信息
        """
        return await self._request("GET", f"/api/documents/task-status/{file_id}")
    
    async def get_all_documents(self) -> Dict[str, Any]:
        """
        获取所有文档列表
        
        Returns:
            Dict[str, Any]: 文档列表
        """
        return await self._request("GET", "/api/documents")
    
    async def get_document(self, doc_id: str) -> Dict[str, Any]:
        """
        获取文档详情
        
        Args:
            doc_id: 文档ID
        
        Returns:
            Dict[str, Any]: 文档详情
        """
        return await self._request("GET", f"/api/documents/{doc_id}")
    
    async def update_document(
        self,
        doc_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        department: Optional[str] = None,
        regulation_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        source: Optional[str] = None,
        effective_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新文档信息
        
        Args:
            doc_id: 文档ID
            title: 标题
            content: 内容
            department: 部门
            regulation_type: 制度类型
            tags: 标签列表
            summary: 摘要
            source: 来源
            effective_date: 生效日期
        
        Returns:
            Dict[str, Any]: 更新结果
        """
        data = {}
        
        if title is not None:
            data["title"] = title
        if content is not None:
            data["content"] = content
        if department is not None:
            data["department"] = department
        if regulation_type is not None:
            data["regulation_type"] = regulation_type
        if tags is not None:
            data["tags"] = tags
        if summary is not None:
            data["summary"] = summary
        if source is not None:
            data["source"] = source
        if effective_date is not None:
            data["effective_date"] = effective_date
        
        return await self._request("PUT", f"/api/documents/{doc_id}", json=data)
    
    async def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """
        删除文档
        
        Args:
            doc_id: 文档ID
        
        Returns:
            Dict[str, Any]: 删除结果
        """
        logger.info(f"删除文档: doc_id={doc_id}")
        return await self._request("DELETE", f"/api/documents/{doc_id}")
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        search_type: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        智能检索
        
        支持语义检索、关键词检索和混合检索
        
        Args:
            query: 检索查询语句
            top_k: 返回结果数量
            search_type: 检索类型（semantic/keyword/hybrid）
        
        Returns:
            Dict[str, Any]: 检索结果
        """
        logger.info(f"智能检索: query={query[:50]}..., top_k={top_k}, type={search_type}")
        
        data = {
            "query": query,
            "top_k": top_k,
            "search_type": search_type
        }
        
        result = await self._request("POST", "/api/search", json=data)
        logger.info(f"检索完成")
        
        return result
    
    async def get_document_chunks(self, doc_id: str) -> Dict[str, Any]:
        """
        获取文档切片
        
        Args:
            doc_id: 文档ID
        
        Returns:
            Dict[str, Any]: 文档切片列表
        """
        return await self._request("GET", f"/api/documents/{doc_id}/chunks")
    
    async def get_document_versions(self, doc_id: str) -> Dict[str, Any]:
        """
        获取文档版本历史
        
        Args:
            doc_id: 文档ID
        
        Returns:
            Dict[str, Any]: 版本历史列表
        """
        return await self._request("GET", f"/api/documents/{doc_id}/versions")
    
    async def get_document_version(self, doc_id: str, version_id: str) -> Dict[str, Any]:
        """
        获取特定版本
        
        Args:
            doc_id: 文档ID
            version_id: 版本ID
        
        Returns:
            Dict[str, Any]: 特定版本详情
        """
        return await self._request("GET", f"/api/documents/{doc_id}/versions/{version_id}")
    
    async def restore_version(self, doc_id: str, version_id: str) -> Dict[str, Any]:
        """
        恢复版本
        
        Args:
            doc_id: 文档ID
            version_id: 版本ID
        
        Returns:
            Dict[str, Any]: 恢复结果
        """
        return await self._request("POST", f"/api/documents/{doc_id}/versions/{version_id}/restore")
    
    async def enhance_document(self, doc_id: str) -> Dict[str, Any]:
        """
        知识增强
        
        Args:
            doc_id: 文档ID
        
        Returns:
            Dict[str, Any]: 增强结果
        """
        return await self._request("POST", f"/api/documents/{doc_id}/enhance")
    
    async def full_enhance_document(self, doc_id: str) -> Dict[str, Any]:
        """
        完整知识增强
        
        Args:
            doc_id: 文档ID
        
        Returns:
            Dict[str, Any]: 增强结果
        """
        return await self._request("POST", f"/api/documents/{doc_id}/full-enhance")
    
    async def keyword_enhance_document(self, doc_id: str) -> Dict[str, Any]:
        """
        关键字增强
        
        Args:
            doc_id: 文档ID
        
        Returns:
            Dict[str, Any]: 增强结果
        """
        return await self._request("POST", f"/api/documents/{doc_id}/keyword-enhance")
    
    async def custom_enhance_document(self, doc_id: str, question: str) -> Dict[str, Any]:
        """
        自定义增强
        
        Args:
            doc_id: 文档ID
            question: 用户问题
        
        Returns:
            Dict[str, Any]: 增强结果
        """
        data = {"question": question}
        return await self._request("POST", f"/api/documents/{doc_id}/custom-enhance", json=data)
    
    async def get_knowledge_graph(self, doc_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取知识图谱
        
        Args:
            doc_id: 文档ID（可选）
        
        Returns:
            Dict[str, Any]: 知识图谱数据
        """
        params = {}
        if doc_id:
            params["doc_id"] = doc_id
        
        return await self._request("GET", "/api/knowledge/graph", json=params if params else None)
    
    async def llm_chat(self, user_message: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        大模型聊天
        
        Args:
            user_message: 用户消息
            system_prompt: 系统提示词
        
        Returns:
            Dict[str, Any]: AI回复
        """
        data = {"user_message": user_message}
        if system_prompt:
            data["system_prompt"] = system_prompt
        
        return await self._request("POST", "/api/llm/chat", json=data)
    
    async def summarize(self, content: str) -> Dict[str, Any]:
        """
        生成摘要
        
        Args:
            content: 需要摘要的文本内容
        
        Returns:
            Dict[str, Any]: 摘要内容
        """
        data = {"content": content}
        return await self._request("POST", "/api/summarize", json=data)


knowledge_api_client = KnowledgeApiClient()
