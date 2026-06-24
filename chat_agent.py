"""LangGraph对话图模块，支持多轮对话记忆和上下文压缩"""
import os
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver


MAX_HISTORY = int(os.getenv("MAX_HISTORY", "20"))
COMPRESS_THRESHOLD = int(os.getenv("COMPRESS_THRESHOLD", "15"))
COMPRESS_KEEP_RECENT = int(os.getenv("COMPRESS_KEEP_RECENT", "6"))

# 多模型配置
MODEL_NAMES = [m.strip() for m in os.getenv("MODEL_NAME", "gpt-4o-mini").split(",") if m.strip()]


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


class ChatAgent:
    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.api_key = api_key
        self.base_url = base_url
        self.models = MODEL_NAMES
        self.current_model_index = 0
        self.llm = self._create_llm(self.models[self.current_model_index])
        self.memory = MemorySaver()
        self.graph = self._build_graph()

    def _create_llm(self, model_name: str) -> ChatOpenAI:
        return ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=model_name,
            temperature=0.7,
        )

    def get_current_model(self) -> str:
        return self.models[self.current_model_index]

    def get_model_list(self) -> list[str]:
        return self.models

    def switch_model(self, model_name: str) -> bool:
        for i, m in enumerate(self.models):
            if m.lower() == model_name.lower():
                self.current_model_index = i
                self.llm = self._create_llm(m)
                return True
        return False

    async def _compress_messages(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        if len(messages) <= COMPRESS_THRESHOLD:
            return messages
        
        old_messages = messages[:-COMPRESS_KEEP_RECENT]
        recent_messages = messages[-COMPRESS_KEEP_RECENT:]
        
        history_text = "\n".join([
            f"{'用户' if isinstance(m, HumanMessage) else 'AI'}: {m.content}"
            for m in old_messages
        ])
        
        compress_prompt = [
            SystemMessage(content="请将以下对话压缩成简洁的摘要，保留关键信息（用户需求、重要结论、待办事项等）。"),
            HumanMessage(content=f"对话历史：\n{history_text}\n\n请生成摘要：")
        ]
        
        try:
            summary = await self.llm.ainvoke(compress_prompt)
            compressed = [SystemMessage(content=f"[对话摘要] {summary.content}")]
            return compressed + recent_messages
        except Exception:
            return messages[-MAX_HISTORY:]

    def _trim_messages(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        if len(messages) > MAX_HISTORY:
            return messages[-MAX_HISTORY:]
        return messages

    async def _acall_model(self, state: AgentState):
        messages = state["messages"]
        if len(messages) > COMPRESS_THRESHOLD:
            messages = await self._compress_messages(messages)
        else:
            messages = self._trim_messages(messages)
        
        response = await self.llm.ainvoke(messages)
        return {"messages": [response]}

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", self._acall_model)
        workflow.add_edge(START, "agent")
        workflow.add_edge("agent", END)
        return workflow.compile(checkpointer=self.memory)

    async def chat(self, user_message: str, thread_id: str) -> str:
        config = {"configurable": {"thread_id": thread_id}}
        input_messages = [HumanMessage(content=user_message)]
        result = await self.graph.ainvoke(
            {"messages": input_messages}, 
            config=config,
            recursion_limit=50
        )
        return result["messages"][-1].content
