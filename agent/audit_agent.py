"""
制度审查智能体模块
基于LangGraph实现智能问答和审查功能，支持文件操作工具调用
"""

from typing import TypedDict, Annotated, Sequence, Optional, List, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from config import settings
from agent.tools import get_file_tools


class AgentState(TypedDict):
    """
    智能体状态定义
    
    Attributes:
        messages: 消息历史
        question: 用户问题
        context: 检索到的上下文
        knowledge_base_id: 知识库ID
        file_content: 上传文件的内容
        file_paths: 上传文件路径列表
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: str
    context: Optional[str]
    knowledge_base_id: Optional[int]
    file_content: Optional[str]
    file_paths: Optional[List[str]]


SYSTEM_PROMPT = """你是依托法律垂类大模型构建的企业制度全生命周期智能化审查工具，核心职责是基于多源合规依据，实现制度条款审查的自动化、标准化处理，为企业提供全面、精准、高效的制度审查服务。请严格遵循以下规则与要求开展审查工作：

一、审查依据与规则基础
核心数据来源：需优先调取并依据两类核心数据开展审查 ——
内部数据：企业内部制度管理规范、历史审查案例、上位制度文件、部门权责清单；
外部数据：海量法律法规、行业监管政策、地方规范性文件。
审查规则构建：
合规审查规则：整合上述多源数据，经外规内化与规则梳理，覆盖合规性、一致性、适用性三大核心维度；
形式审查规则：依据企业内部要求，聚焦制度结构完整性、排版规范性、表达准确性、逻辑清晰度等维度。
审查清单应用：基于企业合规管理体系，结合法律法规与内部管控要求，启用通用类、专项类、特定场景类多维度审查清单，确保审查覆盖全面且具备实操性，明确各环节审查核心与重点方向。

二、审查范围与核心能力
（一）审查维度全覆盖
合规性审查：校验拟制/修订/现行制度条款是否与现行法律法规、部门规章相抵触，明确冲突边界；
一致性审查：校验条款与上位制度、企业内部现有制度、部门权责划分是否一致，排查逻辑矛盾；
适用性审查：评估条款是否符合企业管控流程要求，是否适配实际业务场景；
形式审查：排查条款中的错别字、章节书写不规范、格式混乱、逻辑不清晰等问题；
版本比对：支持对制度文件不同版本的差异精准识别与呈现。

（二）多场景审查支持
文档类型：支持单文档审查、批量文档审查，兼容Word、PDF（含图片格式）等文件，可识别流程图、表格等内嵌内容；
审查对象：可针对拟制制度、修订制度、现行制度开展专项审查；
自定义功能：支持用户指定审查范围与重点审查条款，按个性化需求执行审查。

三、审查结果与操作规范
结果展示要求：
结构化呈现：包含风险点、风险等级、风险说明、冲突说明、具体修改建议及对应的法律依据/制度依据；
可视化定位：在制度原文中对风险内容进行高亮标注，支持快速定位查看。
结果校验与输出：
支持用户对审查意见执行采纳、驳回或部分采纳操作；
采纳意见后自动修订制度内容，并同步优化其他审查点的定位准确性；
支持导出带批注的Word/PDF格式审查报告。
进度与记录管理：
提供当前文档及批量审查文档的实时进度查看功能；
自动保存所有审查历史记录（含审查时间、审查文档、审查结果、修改轨迹），支持快速查询、筛选及带审查结果的文件下载，确保审查工作可追溯、可审计。

四、时效与返回格式要求
返回模式：支持流式返回与非流式返回两种模式，所有审查结果均以结构化格式输出，确保适配前端展示需求。

当用户要求修改文件或标注文件时，请使用相应的工具完成任务。

当前上下文信息：
{context}

当前可用的文件路径：
{file_paths}

请基于以上信息和规则回答用户问题，如果上下文信息不足，请明确告知用户需要提供哪些补充材料。"""


class AuditAgent:
    """
    制度审查智能体
    
    使用LangGraph构建智能问答流程，支持：
    - 基于知识库的检索增强生成（RAG）
    - 文件内容分析
    - 流式输出
    - 工具调用（文件操作）
    
    Attributes:
        llm: 大语言模型
        tools: 可用工具列表
        graph: LangGraph工作流图
    """
    
    def __init__(self, enable_tools: bool = True):
        """
        初始化智能体
        
        Args:
            enable_tools: 是否启用工具调用
        """
        self.tools = get_file_tools() if enable_tools else []
        self.enable_tools = enable_tools
        self.llm = self._init_llm()
        self.graph = self._build_graph()
    
    def _init_llm(self):
        """
        初始化大语言模型
        
        根据配置文件中的 MODEL_PROVIDER 选择模型提供商
        
        Returns:
            LLM: 大语言模型实例
        """
        provider = settings.MODEL_PROVIDER.lower()
        
        if provider == "alibaba" and settings.ALIBABA_API_KEY:
            from langchain_openai import ChatOpenAI
            
            llm = ChatOpenAI(
                model=settings.ALIBABA_MODEL,
                api_key=settings.ALIBABA_API_KEY,
                base_url=settings.ALIBABA_API_URL,
                streaming=True
            )
            if self.tools:
                llm = llm.bind_tools(self.tools)
            return llm
        else:
            llm = ChatOllama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
                streaming=True
            )
            if self.tools:
                llm = llm.bind_tools(self.tools)
            return llm
    
    def _build_graph(self) -> StateGraph:
        """
        构建LangGraph工作流图
        
        Returns:
            StateGraph: 工作流图
        """
        workflow = StateGraph(AgentState)
        
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("agent", self._agent_node)
        
        if self.enable_tools and self.tools:
            workflow.add_node("tools", ToolNode(self.tools))
        
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "agent")
        
        if self.enable_tools and self.tools:
            workflow.add_conditional_edges(
                "agent",
                self._should_continue,
                {
                    "continue": "tools",
                    "end": END
                }
            )
            workflow.add_edge("tools", "agent")
        else:
            workflow.add_edge("agent", END)
        
        return workflow.compile()
    
    def _should_continue(self, state: AgentState) -> str:
        """
        判断是否继续调用工具
        
        Args:
            state: 当前状态
        
        Returns:
            str: "continue" 或 "end"
        """
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "continue"
        return "end"
    
    def _retrieve_node(self, state: AgentState) -> dict:
        """
        检索节点
        
        根据知识库ID检索相关文档
        
        Args:
            state: 当前状态
        
        Returns:
            dict: 更新后的状态
        """
        context = ""
        
        if state.get("knowledge_base_id"):
            from db.postgres_session import vector_store_manager
            
            collection_name = f"kb_{state['knowledge_base_id']}"
            try:
                vector_store = vector_store_manager.get_vector_store(collection_name)
                docs = vector_store.similarity_search(state["question"], k=4)
                context = "\n\n".join([doc.page_content for doc in docs])
            except Exception:
                context = ""
        
        if state.get("file_content"):
            context = f"{context}\n\n上传文件内容：\n{state['file_content']}" if context else f"上传文件内容：\n{state['file_content']}"
        
        return {"context": context}
    
    def _agent_node(self, state: AgentState) -> dict:
        """
        智能体节点
        
        基于上下文和历史消息生成回答
        
        Args:
            state: 当前状态
        
        Returns:
            dict: 更新后的状态
        """
        file_paths_str = ""
        if state.get("file_paths"):
            file_paths_str = "\n".join(state["file_paths"])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{question}")
        ])
        
        chain = prompt | self.llm
        
        response = chain.invoke({
            "context": state.get("context", ""),
            "file_paths": file_paths_str,
            "messages": state.get("messages", []),
            "question": state["question"]
        })
        
        return {"messages": [response]}
    
    def _retrieve_context(
        self,
        question: str,
        knowledge_base_id: Optional[int] = None,
        file_content: Optional[str] = None
    ) -> str:
        """
        检索上下文
        
        Args:
            question: 用户问题
            knowledge_base_id: 知识库ID
            file_content: 上传文件内容
        
        Returns:
            str: 检索到的上下文
        """
        context = ""
        
        if knowledge_base_id:
            from db.postgres_session import vector_store_manager
            
            collection_name = f"kb_{knowledge_base_id}"
            try:
                vector_store = vector_store_manager.get_vector_store(collection_name)
                docs = vector_store.similarity_search(question, k=4)
                context = "\n\n".join([doc.page_content for doc in docs])
            except Exception:
                context = ""
        
        if file_content:
            context = f"{context}\n\n上传文件内容：\n{file_content}" if context else f"上传文件内容：\n{file_content}"
        
        return context
    
    def stream_chat(
        self,
        question: str,
        messages: list,
        knowledge_base_id: Optional[int] = None,
        file_content: Optional[str] = None,
        file_paths: Optional[List[str]] = None
    ):
        """
        流式聊天
        
        Args:
            question: 用户问题
            messages: 历史消息列表
            knowledge_base_id: 知识库ID
            file_content: 上传文件内容
            file_paths: 上传文件路径列表
        
        Yields:
            str: 生成的文本片段
        """
        formatted_messages = []
        for msg in messages:
            if msg["role"] == "user":
                formatted_messages.append(HumanMessage(content=msg["content"]))
            else:
                formatted_messages.append(AIMessage(content=msg["content"]))
        
        context = self._retrieve_context(question, knowledge_base_id, file_content)
        
        file_paths_str = ""
        if file_paths:
            file_paths_str = "\n".join(file_paths)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{question}")
        ])
        
        chain = prompt | self.llm
        
        for chunk in chain.stream({
            "context": context,
            "file_paths": file_paths_str,
            "messages": formatted_messages,
            "question": question
        }):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content
    
    def chat(
        self,
        question: str,
        messages: list,
        knowledge_base_id: Optional[int] = None,
        file_content: Optional[str] = None,
        file_paths: Optional[List[str]] = None
    ) -> str:
        """
        同步聊天
        
        Args:
            question: 用户问题
            messages: 历史消息列表
            knowledge_base_id: 知识库ID
            file_content: 上传文件内容
            file_paths: 上传文件路径列表
        
        Returns:
            str: 完整的回答
        """
        full_response = ""
        for chunk in self.stream_chat(question, messages, knowledge_base_id, file_content, file_paths):
            full_response += chunk
        return full_response
    
    def chat_with_tools(
        self,
        question: str,
        messages: list,
        knowledge_base_id: Optional[int] = None,
        file_content: Optional[str] = None,
        file_paths: Optional[List[str]] = None
    ) -> dict:
        """
        带工具调用的聊天
        
        Args:
            question: 用户问题
            messages: 历史消息列表
            knowledge_base_id: 知识库ID
            file_content: 上传文件内容
            file_paths: 上传文件路径列表
        
        Returns:
            dict: 包含响应和工具调用结果的字典
        """
        formatted_messages = []
        for msg in messages:
            if msg["role"] == "user":
                formatted_messages.append(HumanMessage(content=msg["content"]))
            else:
                formatted_messages.append(AIMessage(content=msg["content"]))
        
        initial_state = {
            "messages": formatted_messages,
            "question": question,
            "knowledge_base_id": knowledge_base_id,
            "file_content": file_content,
            "file_paths": file_paths,
            "context": None
        }
        
        final_state = None
        for event in self.graph.stream(initial_state):
            for key, value in event.items():
                final_state = value
        
        result = {
            "success": True,
            "response": "",
            "tool_calls": [],
            "tool_results": []
        }
        
        if final_state and "messages" in final_state:
            for msg in final_state["messages"]:
                if hasattr(msg, "content") and msg.content:
                    if isinstance(msg, AIMessage):
                        result["response"] = msg.content
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            result["tool_calls"] = msg.tool_calls
                    elif isinstance(msg, ToolMessage):
                        result["tool_results"].append({
                            "tool_call_id": msg.tool_call_id,
                            "content": msg.content
                        })
        
        return result


def create_audit_agent(enable_tools: bool = True) -> AuditAgent:
    """
    创建制度审查智能体的便捷函数
    
    模型提供商由配置文件中的 MODEL_PROVIDER 决定
    
    Args:
        enable_tools: 是否启用工具调用
    
    Returns:
        AuditAgent: 智能体实例
    """
    return AuditAgent(enable_tools=enable_tools)
