"""
制度审查智能体模块
基于LangGraph实现智能问答和审查功能，支持文件操作工具调用
"""

import json
import logging
from typing import TypedDict, Annotated, Sequence, Optional, List, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from config import settings
from agent.tools import get_file_tools, current_conversation_id

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
    rules_context: Optional[str]
    knowledge_base_id: Optional[int]
    conversation_id: Optional[int]
    file_content: Optional[str]
    file_paths: Optional[List[str]]
    iteration_count: int


SYSTEM_PROMPT = """你是制度审查智能助手，专门帮助企业审查制度文件。

你拥有以下工具可以调用：

**文件操作工具：**
1. read_file: 读取文件内容，只需输入文件名（如：document.pdf）
2. highlight_text_in_pdf: 在PDF中标注文字（标红显示）
3. modify_text_in_pdf: 修改PDF中的文字内容
4. highlight_text_in_docx: 在Word中标注文字（标红显示）
5. modify_text_in_docx: 修改Word中的文字内容
6. add_review_comments: 生成审查报告

**规则管理工具：**
7. add_rule: 添加用户明确表达的规章或规则到数据库
   - 【重要】只能添加用户在【输入框中直接输入的文字】作为规则
   - 【禁止】绝对不能把用户上传的文件内容（PDF、Word等）当成规则添加
   - 参数：title（规则标题）、content（规则内容）、rule_type（类型：global全局规则/conversation对话规则）、category（分类）、priority（优先级）
   - 全局规则对所有对话生效，对话规则仅对当前对话生效

8. add_rules: 批量添加多条规章或规则到数据库
   - 【重要】只能添加用户在输入框中明确表达的规定、要求
   - 【禁止】不能把文件内容添加到规则中
   - 参数：rules（规则列表）、conversation_id（对话ID）

重要规则：
- 工具参数中的 filename 只需要输入文件名，不要输入路径
- 例如：如果文件是 "uploads/temp/新法律法规.pdf"，你只需要输入 "新法律法规.pdf"
- 当用户要求添加规章、规则时，主动调用 add_rule 或 add_rules 工具
- 完成任务后，直接告诉用户结果，不要重复调用工具
- 【关键】add_rule 和 add_rules 只能用于添加用户主动表达的规定、要求，禁止用于添加文件内容

【重要】内容优先级说明：
- 规则库内容（全局规则和对话规则）的优先级最高，必须优先遵守
- 当规则库内容与向量库检索内容存在冲突或歧义时，以规则库内容为准
- 规则库内容是用户明确制定的规定，具有最高权威性
- 对话规则和全局规则冲突的时候，以对话规则优先级更高

{rules_context}

【注意】以下上下文信息来自向量库检索，仅供参考，如有冲突请以规则库内容为准：
{context}

当前可用的文件名：
{file_paths}"""


class ConversationAwareToolNode:
    """
    自定义工具节点，确保在工具执行时 conversation_id 可用
    
    解决 LangGraph 默认 ToolNode 在执行工具时 ContextVar 无法正确传递的问题
    """
    
    def __init__(self, tools: list):
        self.tools = {tool.name: tool for tool in tools}
    
    def __call__(self, state: dict, config: RunnableConfig = None) -> dict:
        messages = state.get("messages", [])
        if not messages:
            return {"messages": []}
        
        last_message = messages[-1]
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return {"messages": []}
        
        conversation_id = state.get("conversation_id")
        if conversation_id:
            current_conversation_id.set(conversation_id)
            logger.info(f"ToolNode 设置 conversation_id: {conversation_id}")
        
        tool_messages = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id")
            
            if tool_name not in self.tools:
                tool_messages.append(ToolMessage(
                    content=f"工具 {tool_name} 不存在",
                    tool_call_id=tool_id
                ))
                continue
            
            tool = self.tools[tool_name]
            try:
                result = tool.invoke(tool_args)
                tool_messages.append(ToolMessage(
                    content=result,
                    tool_call_id=tool_id
                ))
                logger.info(f"工具 {tool_name} 执行成功")
            except Exception as e:
                logger.error(f"工具 {tool_name} 执行失败: {str(e)}", exc_info=True)
                tool_messages.append(ToolMessage(
                    content=f"工具执行失败: {str(e)}",
                    tool_call_id=tool_id
                ))
        
        return {"messages": tool_messages}


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
            workflow.add_node("tools", ConversationAwareToolNode(self.tools))
        
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
        rules_context = ""
        
        from db import get_db
        from services.rule_service import RuleService
        
        try:
            db = next(get_db())
            rule_service = RuleService(db)
            
            conversation_id = state.get("conversation_id")
            active_rules = rule_service.get_active_rules_for_conversation(conversation_id)
            
            if active_rules:
                global_rules = [r for r in active_rules if r.rule_type.value == "global"]
                conversation_rules = [r for r in active_rules if r.rule_type.value == "conversation"]
                
                if global_rules:
                    rules_context += "【全局规则】（适用于所有对话）：\n"
                    for rule in global_rules:
                        rules_context += f"- {rule.title}: {rule.content}\n"
                    rules_context += "\n"
                
                if conversation_rules:
                    rules_context += "【对话规则】（仅适用于当前对话）：\n"
                    for rule in conversation_rules:
                        rules_context += f"- {rule.title}: {rule.content}\n"
                    rules_context += "\n"
                
                logger.info(f"检索到 {len(active_rules)} 条活跃规则（全局: {len(global_rules)}, 对话: {len(conversation_rules)}")
        except Exception as e:
            logger.error(f"检索规则失败: {str(e)}", exc_info=True)
        
        if state.get("knowledge_base_id"):
            from db.postgres_session import vector_store_manager
            
            collection_name = f"kb_{state['knowledge_base_id']}"
            try:
                vector_store = vector_store_manager.get_vector_store(collection_name)
                docs = vector_store.similarity_search(state["question"], k=4)
                context = "\n\n".join([doc.page_content for doc in docs])
                logger.info(f"从向量库检索到 {len(docs)} 条相关文档")
            except Exception as e:
                logger.error(f"向量库检索失败: {str(e)}")
                context = ""
        
        if state.get("file_content"):
            context = f"{context}\n\n上传文件内容：\n{state['file_content']}" if context else f"上传文件内容：\n{state['file_content']}"
        
        return {"context": context, "rules_context": rules_context}
    
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
        
        full_prompt = prompt.format(
            context=state.get("context", ""),
            rules_context=state.get("rules_context", ""),
            file_paths=file_paths_str,
            messages=state.get("messages", []),
            question=state["question"]
        )
        
        logger.info("=" * 80)
        logger.info("完整提示词内容：")
        logger.info("=" * 80)
        print("\n" + "=" * 80)
        print("完整提示词内容：")
        print("=" * 80)
        
        if isinstance(full_prompt, list):
            for i, msg in enumerate(full_prompt):
                msg_type = type(msg).__name__
                content = msg.content if hasattr(msg, 'content') else str(msg)
                logger.info(f"\n--- 消息 {i+1} [{msg_type}] ---")
                logger.info(content)
                print(f"\n--- 消息 {i+1} [{msg_type}] ---")
                print(content)
        else:
            logger.info(full_prompt)
            print(full_prompt)
        
        logger.info("=" * 80)
        print("=" * 80 + "\n")
        
        response = chain.invoke({
            "context": state.get("context", ""),
            "rules_context": state.get("rules_context", ""),
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
        file_paths: Optional[List[str]] = None,
        conversation_id: Optional[int] = None
    ) -> dict:
        current_conversation_id.set(conversation_id)
        logger.info(f"设置 current_conversation_id: {conversation_id}")
        
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
            "conversation_id": conversation_id,
            "file_content": file_content,
            "file_paths": file_paths,
            "context": None,
            "rules_context": None,
            "iteration_count": 0
        }
        
        logger.info(f"开始执行 chat_with_tools, question: {question}")
        logger.info(f"conversation_id: {conversation_id}")
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
