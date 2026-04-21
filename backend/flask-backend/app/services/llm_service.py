import logging
import json
import os
import random
import requests
from typing import List, Dict, Any
from ..config.default import (
    LLM_PROVIDER, LLM_API_KEY, TONGYI_URL, TONGYI_MODEL,
    RAG_SERVICE_URL, RAG_TOP_K, RAG_ENABLED, RAG_MODE
)

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.provider = LLM_PROVIDER
        self.api_key = LLM_API_KEY
        self.rag_service = None
        
        # 如果RAG启用，初始化RAG服务
        if RAG_ENABLED:
            try:
                from .rag_service import RagService
                self.rag_service = RagService()
                logger.info(f"LLM服务已初始化RAG服务，模式: {self.rag_service.mode}")
            except Exception as e:
                logger.error(f"初始化RAG服务失败: {e}")
                self.rag_service = None
        
    def generate_first_question(self, position: str) -> str:
        try:
            # 调用RAG获取相关题目
            rag_context = ""
            if RAG_ENABLED:
                rag_results = self._search_rag(position + "面试题", self._get_collection_by_position(position))
                if rag_results:
                    rag_context = "参考以下面试题：\n"
                    for result in rag_results[:RAG_TOP_K]:
                        rag_context += f"- {result.get('document', '')}\n"
                    rag_context += "\n"
                    logger.info(f"RAG检索到 {len(rag_results)} 条相关题目")
            
            # 构建提示词
            position_display = self._get_position_display_name(position)
            
            # 定义不同类型的友好开场白
            greeting_templates = [
                f"""同学你好，欢迎参加{position_display}岗位的面试。首先，请简单介绍一下你自己，包括你的技术背景和学习经历。""",
                f"""同学你好，我是今天的{position_display}面试官。可以分享一下你大学期间学过哪些技术栈吗？""",
                f"""同学你好，很高兴见到你。作为{position_display}的面试官，我想先了解一下你大学期间做过哪些相关项目？""",
                f"""同学你好，欢迎来面试{position_display}岗位。首先，请你简单做个自我介绍，然后谈谈你对这个岗位的理解。""",
                f"""同学你好，我是{position_display}岗位的面试官。请先简单介绍一下你的技术背景和为什么对这个岗位感兴趣。"""
            ]
            
            # 随机选择一个开场白
            selected_greeting = random.choice(greeting_templates)
            
            # 构建提示词 - 只生成友好的开场问候
            prompt = f"""你是一个友好而专业的{position_display}面试官，正在面试一位初级开发者。
请用自然、友好的语气开始面试对话。

你的任务：说出以下开场白，不要添加其他内容：
"{selected_greeting}"

请确保你的回复就是上述开场白本身，不要添加"面试官："等前缀，也不要解释。"""
            
            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            response = self._call_llm_api(messages)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"生成首轮问题失败: {str(e)}")
            # 返回默认问题
            position_display = self._get_position_display_name(position)
            return f"同学你好，请简单介绍一下你在{position_display}领域的相关经验。"
    
    def evaluate_answer(self, question: str, answer: str, position: str, history: List[Dict]) -> Dict[str, Any]:
        try:
            # 调用RAG获取参考答案
            rag_context = ""
            if RAG_ENABLED:
                rag_results = self._search_rag(question, self._get_collection_by_position(position), limit=3)
                if rag_results:
                    rag_context = "参考答案：\n"
                    for result in rag_results:
                        rag_context += f"- {result.get('document', '')}\n"
                    rag_context += "\n"
                    logger.info(f"RAG检索到 {len(rag_results)} 条相关知识点")
            
            # 构建评估提示词
            prompt = rag_context + f"""面试问题：{question}
学生回答：{answer}

请根据参考答案评估学生的回答，从以下四个维度打分（0-10分）：
1. 技术正确性：回答的技术内容是否正确
2. 知识深度：回答是否展现了足够的知识深度
3. 逻辑清晰度：回答是否逻辑清晰、条理分明
4. 岗位匹配度：回答是否符合该岗位的要求

请以JSON格式返回评估结果，格式如下：
{{"techScore": 8, "depthScore": 7, "logicScore": 8, "matchScore": 7, "feedback": "评价内容", "nextQuestion": "下一个问题", "endInterview": false}}

如果面试应该结束（如已进行多轮或回答质量很差），请设置endInterview为true。"""
            
            # 调用LLM
            messages = [{"role": "user", "content": prompt}]
            response_text = self._call_llm_api(messages)
            
            # 解析JSON响应
            try:
                # 尝试从响应中提取JSON
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_json = json_match.group()
                    result = json.loads(response_json)
                else:
                    result = json.loads(response_text)
            except json.JSONDecodeError:
                logger.warning(f"LLM返回非JSON格式，使用默认评估: {response_text}")
                result = self._get_default_evaluation(question, position)
            
            # 验证必需的字段
            required_fields = ['techScore', 'depthScore', 'logicScore', 'matchScore', 'feedback', 'nextQuestion', 'endInterview']
            for field in required_fields:
                if field not in result:
                    result[field] = self._get_default_evaluation(question, position)[field]
            
            return result
            
        except Exception as e:
            logger.error(f"评估回答失败: {str(e)}")
            return self._get_default_evaluation(question, position)
    
    def _call_llm_api(self, messages: List[Dict]) -> str:
        # 仅支持千问文本API
        return self._call_tongyi_api(messages)
    
    def _call_tongyi_api(self, messages: List[Dict]) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": TONGYI_MODEL,
                "input": {
                    "messages": messages
                },
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
            
            response = requests.post(TONGYI_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["output"]["text"]
            
        except Exception as e:
            logger.error(f"通义千问API调用失败: {str(e)}")
            raise
    

    
    def _search_rag(self, query: str, collection: str, limit: int = None) -> List[Dict]:
        if not RAG_ENABLED or not self.rag_service or not self.rag_service.enabled:
            logger.info("RAG服务未启用，跳过搜索")
            return []
        
        try:
            # 直接使用RagService进行搜索
            top_k = limit or RAG_TOP_K
            logger.info(f"调用RAG服务: collection={collection}, query长度={len(query)}, top_k={top_k}")
            
            # 使用RagService搜索
            results = self.rag_service.search_questions(query, collection, top_k)
            logger.info(f"RAG服务返回 {len(results)} 条结果")
            
            # 转换结果格式以保持向后兼容
            # RagService返回的格式: {"id": "...", "content": "...", "metadata": {...}, "score": ..., "distance": ...}
            # LLM服务期望的格式: {"document": "...", "metadata": {...}, "score": ..., ...}
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "document": result.get("content", ""),
                    "id": result.get("id", ""),
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", 0.0),
                    "distance": result.get("distance", 0.0)
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"RAG搜索失败: {str(e)}")
            logger.exception("RAG搜索异常详情")
            return []
    
    def _get_collection_by_position(self, position: str) -> str:
        position = position.lower()
        if 'frontend' in position or '前端' in position or 'web' in position:
            return 'web_frontend'
        elif 'backend' in position or '后端' in position or 'java' in position:
            return 'java_backend'
        elif 'fullstack' in position or 'full_stack' in position or '全栈' in position:
            return 'fullstack_engineer'
        elif 'bigdata' in position or 'big_data' in position or '大数据' in position:
            return 'bigdata_engineer'
        else:
            return 'java_backend'
    
    def _get_position_display_name(self, position: str) -> str:
        position = position.lower()
        if 'frontend' in position:
            return '前端'
        elif 'backend' in position:
            return '后端'
        elif 'java' in position:
            return 'Java后端'
        elif 'web' in position:
            return 'Web前端'
        elif 'fullstack' in position or 'full_stack' in position or '全栈' in position:
            return '全栈开发工程师'
        elif 'bigdata' in position or 'big_data' in position or '大数据' in position:
            return '大数据开发工程师'
        else:
            return position
    
    def _get_default_evaluation(self, question: str, position: str) -> Dict[str, Any]:
        return {
            "techScore": 7,
            "depthScore": 7,
            "logicScore": 7,
            "matchScore": 7,
            "feedback": "系统评估完成，请继续。",
            "nextQuestion": self._get_default_question(position),
            "endInterview": False
        }
    
    def _get_default_question(self, position: str) -> str:
        position_display = self._get_position_display_name(position)
        return f"请继续谈谈你在{position_display}领域的其他经验或项目。"