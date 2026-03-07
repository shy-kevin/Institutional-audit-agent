"""
制度审查智能体模块
基于LangGraph实现智能问答和审查功能，支持文件操作工具调用
"""

import json
import logging
from typing import TypedDict, Annotated, Sequence, Optional, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from config import settings
from agent.tools import get_file_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_ITERATIONS = 10


class AgentState(TypedDict):
    """
    智能体状态定义
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: str
    context: Optional[str]
    knowledge_base_id: Optional[int]
    file_content: Optional[str]
    file_paths: Optional[List[str]]
    iteration_count: int


SYSTEM_PROMPT = """你是制度审查智能助手，专门帮助企业审查制度文件。

你拥有以下工具可以调用：
1. read_file: 读取文件内容，只需输入文件名（如：document.pdf）
2. highlight_text_in_pdf: 在PDF中标注文字（标红显示）
3. modify_text_in_pdf: 修改PDF中的文字内容
4. highlight_text_in_docx: 在Word中标注文字（标红显示）
5. modify_text_in_docx: 修改Word中的文字内容
6. add_review_comments: 生成审查报告

重要规则：
- 工具参数中的 filename 只需要输入文件名，不要输入路径
- 例如：如果文件是 "uploads/temp/新法律法规.pdf"，你只需要输入 "新法律法规.pdf"
- 完成任务后，直接告诉用户结果，不要重复调用工具

当前上下文信息：
{context}

当前可用的文件名：
{file_paths}"""


class AuditAgent:
    """
    制度审查智能体
    """
    
    def __init__(self, enable_tools: bool = True):
        self.tools = get_file_tools() if enable_tools else []
        self.enable_tools = enable_tools
        self.llm = self._init_llm()
        self.graph = self._build_graph()
    
    def _init_llm(self):
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
        iteration_count = state.get("iteration_count", 0)
        
        if iteration_count >= MAX_ITERATIONS:
            logger.warning(f"达到最大迭代次数 {MAX_ITERATIONS}，强制结束")
            return "end"
        
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "continue"
        return "end"
    
    def _retrieve_node(self, state: AgentState) -> dict:
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
        iteration_count = state.get("iteration_count", 0)
        
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
        
        logger.info(f"迭代 {iteration_count + 1}: response content = {response.content[:100] if response.content else 'None'}...")
        if hasattr(response, "tool_calls"):
            logger.info(f"迭代 {iteration_count + 1}: tool_calls = {response.tool_calls}")
        
        return {
            "messages": [response],
            "iteration_count": iteration_count + 1
        }
    
    def chat_with_tools(
        self,
        question: str,
        messages: list,
        knowledge_base_id: Optional[int] = None,
        file_content: Optional[str] = None,
        file_paths: Optional[List[str]] = None
    ) -> dict:
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
            "context": None,
            "iteration_count": 0
        }
        
        logger.info(f"开始执行 chat_with_tools, question: {question}")
        logger.info(f"file_paths: {file_paths}")
        
        final_state = None
        for event in self.graph.stream(initial_state):
            logger.info(f"Graph event: {list(event.keys())}")
            for key, value in event.items():
                final_state = value
        
        result = {
            "success": True,
            "response": "",
            "tool_calls": [],
            "tool_results": []
        }
        
        if final_state and "messages" in final_state:
            logger.info(f"Final state has {len(final_state['messages'])} messages")
            
            for msg in final_state["messages"]:
                msg_type = type(msg).__name__
                logger.info(f"Processing message type: {msg_type}")
                
                if isinstance(msg, AIMessage):
                    if msg.content:
                        result["response"] = msg.content
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            result["tool_calls"].append({
                                "name": tc.get("name", ""),
                                "args": tc.get("args", {}),
                                "id": tc.get("id", "")
                            })
                        logger.info(f"Added {len(msg.tool_calls)} tool_calls to result")
                
                elif isinstance(msg, ToolMessage):
                    tool_result = {
                        "tool_call_id": msg.tool_call_id,
                        "content": msg.content
                    }
                    result["tool_results"].append(tool_result)
                    logger.info(f"Added ToolMessage to result: {msg.content[:200]}...")
        
        logger.info(f"Final result: tool_calls={len(result['tool_calls'])}, tool_results={len(result['tool_results'])}")
        return result


def create_audit_agent(enable_tools: bool = True) -> AuditAgent:
    return AuditAgent(enable_tools=enable_tools)
