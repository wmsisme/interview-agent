import logging
import json
import os
import random
import requests
from typing import List, Dict, Any
from ..config.default import (
    LLM_PROVIDER, LLM_API_KEY, TONGYI_URL, TONGYI_MODEL,
    RAG_SERVICE_URL, RAG_TOP_K, RAG_ENABLED, RAG_MODE,
    REPORT_MODEL, DEEPSEEK_MODEL, COMPATIBLE_URL
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
                if self.rag_service.enabled:
                    logger.info(f"LLM服务已初始化RAG服务，模式: {self.rag_service.mode}")
                else:
                    logger.info("LLM服务检测到RAG已禁用，继续使用纯LLM模式")
            except Exception as e:
                logger.error(f"初始化RAG服务失败: {e}")
                self.rag_service = None
        else:
            logger.info("LLM服务以纯LLM模式启动，RAG_ENABLED=False")
        
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
            position_display = self._get_position_display_name(position)

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

            # 构建对话历史摘要（用于LLM理解上下文）
            history_summary = ""
            if history and len(history) > 2:
                history_summary = "对话历史摘要：\n"
                for msg in history:
                    role_label = "面试官" if msg.get("role") == "assistant" else "候选人"
                    content = msg.get("content", "")
                    if content and len(content) > 200:
                        content = content[:200] + "..."
                    history_summary += f"{role_label}：{content}\n"
                history_summary += "\n"

            # 构建评估提示词
            prompt = rag_context + history_summary + f"""面试问题：{question}
学生回答：{answer}

请仔细阅读学生的回答，根据参考答案从以下四个维度进行严格打分（0-10分）：
1. 技术正确性：回答的技术内容是否正确、准确
2. 知识深度：回答是否展现了足够的知识深度和原理理解
3. 逻辑清晰度：回答是否逻辑清晰、条理分明、重点突出
4. 岗位匹配度：回答是否符合该岗位的能力要求

请以JSON格式返回评估结果：
{{
    "techScore": 8,
    "depthScore": 7,
    "logicScore": 8,
    "matchScore": 7,
    "feedback": "针对该回答的具体点评，必须引用回答中的具体内容，指出哪里说得好、哪里不足、如何改进（80-150字）",
    "nextQuestion": "基于当前回答暴露的不足或引申，提出一个自然的追问问题",
    "endInterview": false
}}

重要要求：
- feedback必须针对这次回答的具体内容，明确指出回答中的优点和不足，给出改进方向，不要使用"回答得很好"等空泛评价
- nextQuestion应该是基于当前对话的自然追问，引导候选人深入思考或弥补不足，不要问与前一轮重复的问题
- 【严禁自问自答】nextQuestion只能是纯问题，绝对不能包含问题的答案、解释或任何分析内容。不要替候选人回答问题
- 如果已经进行了多轮（4轮以上）或候选人回答质量持续很差，可以设置endInterview为true"""

            # 构建消息列表，包含系统消息和对话历史
            system_prompt = f"""你是一个专业的{position_display}面试官。你的职责是：
1. 评估候选人的回答质量
2. 根据评估结果生成下一个面试问题
3. 严格保持面试官的角色，只提问和评估，绝不代替候选人回答问题

核心原则：
- 你只负责提问，候选人的任务是回答。绝对不要在自己的回复中回答自己提出的问题
- nextQuestion必须是简洁的纯问题，不包含任何解释、分析或答案
- 不要在问题中暗示答案或给出选项让候选人选择
- 保持专业、公正的面试态度"""

            messages = [
                {"role": "system", "content": system_prompt}
            ]
            if history:
                messages.extend(history[-10:])
            messages.append({"role": "user", "content": prompt})

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
        return self._call_tongyi_sdk(messages, model=TONGYI_MODEL, max_tokens=2000, temperature=0.7)

    def _call_tongyi_sdk(self, messages: List[Dict], model: str = None, max_tokens: int = 2000, temperature: float = 0.7, enable_thinking: bool = False) -> str:
        try:
            import dashscope
            dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
            from dashscope import Generation

            logger.info(f"[LLMService] SDK调用 {model or TONGYI_MODEL}, thinking={enable_thinking}, key={self.api_key[:12]}...")
            response = Generation.call(
                api_key=self.api_key,
                model=model or TONGYI_MODEL,
                messages=messages,
                result_format="message",
                enable_thinking=enable_thinking,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if response.status_code != 200:
                logger.error(f"[LLMService] SDK返回非200: status={response.status_code}, code={response.code}, msg={response.message}")
                raise Exception(f"SDK error {response.code}: {response.message}")

            return response.output.choices[0].message.content

        except ImportError:
            logger.warning("[LLMService] dashscope SDK不可用，降级HTTP")
            return self._call_tongyi_api_http(messages, model, max_tokens, temperature)
        except Exception as e:
            logger.error(f"SDK调用失败: {str(e)}")
            raise

    def _call_tongyi_api(self, messages: List[Dict], model: str = None, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        return self._call_tongyi_sdk(messages, model, max_tokens, temperature)

    def _call_tongyi_api_http(self, messages: List[Dict], model: str = None, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model or TONGYI_MODEL,
                "input": {
                    "messages": messages
                },
                "parameters": {
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            }
            
            response = requests.post(TONGYI_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result["output"]["text"]
            
        except Exception as e:
            logger.error(f"通义千问API调用失败: {str(e)}")
            raise

    def _call_compatible_api(self, messages: List[Dict], model: str = None, max_tokens: int = 4000, temperature: float = 0.5) -> str:
        return self._call_tongyi_sdk(messages, model=model or REPORT_MODEL, max_tokens=max_tokens, temperature=temperature)

    def _call_deepseek_api(self, messages: List[Dict], max_tokens: int = 4000, temperature: float = 0.3) -> str:
        return self._call_tongyi_sdk(messages, model=DEEPSEEK_MODEL, max_tokens=max_tokens, temperature=temperature, enable_thinking=False)

    
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
            "feedback": "系统未能对该回答进行详细评估，请参考综合报告中的整体分析。",
            "nextQuestion": self._get_default_question(position),
            "endInterview": False
        }
    
    def generate_report_summary(self, qa_pairs: List[Dict[str, Any]], position: str, scores: Dict[str, float], has_scores: bool = True) -> Dict[str, Any]:
        return self.generate_comprehensive_report(qa_pairs, position)

    def generate_comprehensive_report(self, qa_pairs: List[Dict[str, Any]], position: str) -> Dict[str, Any]:
        try:
            position_display = self._get_position_display_name(position)

            if not qa_pairs:
                return {
                    "summary": "本次面试未记录到有效的问答数据。",
                    "evaluation": "无法生成评估，面试记录中无有效问答内容。",
                    "strengths": [],
                    "weaknesses": [],
                    "detailedSuggestions": [],
                    "estimatedScores": {"technical": 5.0, "depth": 5.0, "logic": 5.0, "match": 5.0},
                    "perRound": []
                }

            qa_text_parts = []
            for i, qa in enumerate(qa_pairs, 1):
                question = qa.get('question', '')
                answer = qa.get('answer', '') or ''
                if not answer.strip() or answer == '（未回答）':
                    answer = '（未回答）'
                qa_text_parts.append(f"### 第{i}轮\n**面试官提问**：{question}\n**候选人回答**：{answer}")

            qa_text = "\n\n".join(qa_text_parts)

            system_prompt = f"""你是资深技术面试评估专家。你的任务是根据面试对话记录，生成专业、精准、个性化的面试评估报告。

核心要求：
1. 所有评价必须基于候选人的实际回答内容，引用具体细节
2. 严禁使用"技术扎实""表达清晰""表现良好""有待提升"等空泛表述
3. 每条strengths/weaknesses必须指向具体轮次，并引用候选人的实际回答
4. 评分必须有据可依，基于回答的技术正确性、深度、逻辑和岗位匹配度"""

            prompt = f"""请仔细分析以下{position_display}岗位的面试对话记录，完成两项任务：

【面试对话记录】
{qa_text}

## 任务一：逐轮评分与点评
对每一轮面试，基于候选人的具体回答内容，从四个维度打分（0-10分）并给出具体点评：
- techScore: 技术正确性
- depthScore: 知识深度
- logicScore: 逻辑清晰度
- matchScore: 岗位匹配度
- feedback: 80-150字的具体点评，引用回答中的内容，指出好在哪里、不足在哪里

## 任务二：综合报告
基于全部问答，生成：
- summary: 150-300字总结，提及具体技术话题，哪些回答得好/不足，引用具体轮次
- evaluation: 150-300字详细评估，逐轮引用回答内容分析
- strengths: 3-5条优势，每条必须指向具体轮次和回答内容（格式：第X轮：在回答【XX问题】时，候选人...）
- weaknesses: 3-5条不足，每条必须指向具体轮次（格式：第X轮：在回答【XX问题】时，候选人未能...）
- detailedSuggestions: 3-5条学习建议，每条含title/description/resources三字段

## 返回格式（纯JSON，不加markdown标记）
{{
    "perRound": [
        {{
            "round": 1,
            "techScore": 7,
            "depthScore": 6,
            "logicScore": 7,
            "matchScore": 6,
            "feedback": "在回答XX问题时，候选人提到了...，这一点正确，但未能深入解释...，建议..."
        }}
    ],
    "summary": "基于实际对话的总结...",
    "evaluation": "逐轮详细评估...",
    "strengths": ["第X轮：在回答【具体问题】时，候选人准确地..."],
    "weaknesses": ["第X轮：在回答【具体问题】时，候选人未能..."],
    "detailedSuggestions": [
        {{"title": "针对XX的学习建议", "description": "具体知识点", "resources": "推荐资源"}}
    ]
}}

重要：perRound数组长度必须等于面试轮数，strengths/weaknesses/detailedSuggestions各至少2条。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            logger.info(f"[LLMService] 使用DeepSeek {DEEPSEEK_MODEL} 生成综合报告，共{len(qa_pairs)}轮问答")
            response_text = self._call_deepseek_api(
                messages=messages,
                max_tokens=4000,
                temperature=0.3
            )
            logger.info(f"[LLMService] DeepSeek 报告返回长度: {len(response_text)} 字符")

            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)

            if not isinstance(result, dict):
                raise ValueError(f"DeepSeek返回非dict类型: {type(result)}")

            per_round = result.get('perRound', [])
            if per_round and len(per_round) == len(qa_pairs):
                tech_list = [r.get('techScore', 0) or 0 for r in per_round]
                depth_list = [r.get('depthScore', 0) or 0 for r in per_round]
                logic_list = [r.get('logicScore', 0) or 0 for r in per_round]
                match_list = [r.get('matchScore', 0) or 0 for r in per_round]
                result['estimatedScores'] = {
                    'technical': sum(tech_list) / len(tech_list),
                    'depth': sum(depth_list) / len(depth_list),
                    'logic': sum(logic_list) / len(logic_list),
                    'match': sum(match_list) / len(match_list)
                }
            elif 'estimatedScores' not in result:
                result['estimatedScores'] = {'technical': 7.0, 'depth': 7.0, 'logic': 7.0, 'match': 7.0}

            for field in ['summary', 'evaluation']:
                if field not in result:
                    result[field] = ""
            for field in ['strengths', 'weaknesses', 'detailedSuggestions', 'perRound']:
                if field not in result:
                    result[field] = []

            return result

        except Exception as e:
            logger.error(f"[LLMService] DeepSeek {DEEPSEEK_MODEL} 调用失败: {str(e)}，尝试降级到 {REPORT_MODEL}")
            try:
                response_text = self._call_compatible_api(
                    messages=messages,
                    model=REPORT_MODEL,
                    max_tokens=4000,
                    temperature=0.3
                )
                logger.info(f"[LLMService] 降级模型 {REPORT_MODEL} 返回长度: {len(response_text)} 字符")

                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(response_text)

                if not isinstance(result, dict):
                    raise ValueError(f"降级模型返回非dict: {type(result)}")

                per_round = result.get('perRound', [])
                if per_round and len(per_round) == len(qa_pairs):
                    tech_list = [r.get('techScore', 0) or 0 for r in per_round]
                    depth_list = [r.get('depthScore', 0) or 0 for r in per_round]
                    logic_list = [r.get('logicScore', 0) or 0 for r in per_round]
                    match_list = [r.get('matchScore', 0) or 0 for r in per_round]
                    result['estimatedScores'] = {
                        'technical': sum(tech_list) / len(tech_list),
                        'depth': sum(depth_list) / len(depth_list),
                        'logic': sum(logic_list) / len(logic_list),
                        'match': sum(match_list) / len(match_list)
                    }
                elif 'estimatedScores' not in result:
                    result['estimatedScores'] = {'technical': 7.0, 'depth': 7.0, 'logic': 7.0, 'match': 7.0}

                for field in ['summary', 'evaluation']:
                    if field not in result:
                        result[field] = ""
                for field in ['strengths', 'weaknesses', 'detailedSuggestions', 'perRound']:
                    if field not in result:
                        result[field] = []

                return result

            except Exception as e2:
                logger.error(f"[LLMService] 降级模型 {REPORT_MODEL} 也失败: {str(e2)}，使用最终兜底")
                return self._generate_fallback_report(qa_pairs, position)

    def _generate_fallback_report(self, qa_pairs: List[Dict[str, Any]], position: str) -> Dict[str, Any]:
        position_display = self._get_position_display_name(position)
        total = len(qa_pairs)
        answered = sum(1 for qa in qa_pairs if qa.get('answer', '').strip() and qa.get('answer', '') != '（未回答）')

        per_round = []
        for i, qa in enumerate(qa_pairs, 1):
            answer = qa.get('answer', '') or ''
            question = qa.get('question', '')[:60]
            has_answer = answer.strip() and answer != '（未回答）'
            if has_answer:
                feedback = f"第{i}轮「{question}」：候选人给出了回答（{len(answer)}字）。请启动后端服务并确保 DeepSeek API 可用以获取详细 AI 评估。"
            else:
                feedback = f"第{i}轮「{question}」：候选人未提供有效回答。"
            per_round.append({
                "round": i,
                "techScore": 0,
                "depthScore": 0,
                "logicScore": 0,
                "matchScore": 0,
                "feedback": feedback
            })

        question_briefs = []
        for qa in qa_pairs:
            q = qa.get('question', '')
            brief = q[:50] + '...' if len(q) > 50 else q
            question_briefs.append(brief)

        summary = (
            f"【注意：此为兜底报告，LLM 评估服务暂不可用】\n"
            f"本次{position_display}岗位面试共进行{total}轮问答，"
            f"{'全部获得有效回答' if answered == total else f'{answered}轮有效回答、{total - answered}轮未回答'}。\n"
            f"涉及问题：{'；'.join(question_briefs)}\n"
            f"请确保 DeepSeek API (deepseek-v4-flash) 已正确配置并可用，以获取完整的 AI 评估报告。"
        )
        evaluation = summary

        strengths = []
        weaknesses = []
        for i, qa in enumerate(qa_pairs, 1):
            q_brief = qa.get('question', '')[:50]
            answer = qa.get('answer', '') or ''
            if answer.strip() and answer != '（未回答）':
                strengths.append(f"第{i}轮「{q_brief}」：候选人给出了回答，内容长度{len(answer)}字")
            else:
                weaknesses.append(f"第{i}轮「{q_brief}」：候选人未提供回答")

        if not strengths:
            strengths = ["候选人参与了本次面试"]
        if not weaknesses:
            weaknesses = ["无具体评估数据，建议重新生成报告"]

        suggestions = [{
            "title": "确保 AI 评估服务可用",
            "description": "当前报告为兜底数据。请检查 backend 日志确认 DeepSeek API 调用是否成功，确保 API Key 和模型名称配置正确。",
            "resources": "查看 backend 终端日志排查 API 调用错误"
        }]

        return {
            "perRound": per_round,
            "summary": summary,
            "evaluation": evaluation,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "detailedSuggestions": suggestions,
            "estimatedScores": {'technical': 0, 'depth': 0, 'logic': 0, 'match': 0}
        }

    def _get_default_question(self, position: str) -> str:
        position_display = self._get_position_display_name(position)
        return f"请继续谈谈你在{position_display}领域的其他经验或项目。"
