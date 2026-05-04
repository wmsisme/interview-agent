import logging
import time
from datetime import datetime
from ..models import db, InterviewRecord, QuestionAnswer
from .llm_service import LLMService
from .rag_service import RagService

logger = logging.getLogger(__name__)

class InterviewService:
    def __init__(self):
        self.llm_service = LLMService()
        self.rag_service = RagService()
        self.conversation_history = {}  # {interview_id: [messages]}
    
    def start_interview(self, position, user_id=None):
        try:
            # 创建面试记录
            record = InterviewRecord(
                user_id=user_id,
                position=position,
                start_time=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.session.add(record)
            db.session.commit()
            
            # 生成首轮问题
            first_question = self.llm_service.generate_first_question(position)
            
            # 保存首轮问题
            qa = QuestionAnswer(
                interview_id=record.id,
                question=first_question,
                created_at=datetime.utcnow()
            )
            db.session.add(qa)
            db.session.commit()
            
            # 初始化对话历史
            history = [
                {"role": "system", "content": f"你是一个严谨的{position}面试官。"},
                {"role": "assistant", "content": first_question}
            ]
            self.conversation_history[record.id] = history
            
            # 返回响应
            response = {
                "interviewId": record.id,
                "firstQuestion": first_question,
                "firstQuestionId": qa.id,
                "questionAudioUrl": None  # 可扩展：生成语音URL
            }
            
            return response
            
        except Exception as e:
            logger.error(f"开始面试失败: {str(e)}")
            db.session.rollback()
            raise
    
    def process_answer(self, interview_id, question_id, answer_text):
        try:
            # 获取问题和验证
            qa = QuestionAnswer.query.filter_by(
                id=question_id, 
                interview_id=interview_id
            ).first()
            
            if not qa:
                raise ValueError("问题ID无效或不属于该面试")
            
            # 更新回答
            qa.answer = answer_text
            db.session.commit()
            
            # 获取对话历史
            history = self.conversation_history.get(interview_id, [])
            history.append({"role": "user", "content": answer_text})
            
            # 获取面试岗位
            record = InterviewRecord.query.get(interview_id)
            position = record.position if record else "java_backend"
            
            # 调用LLM评估
            evaluation_result = self.llm_service.evaluate_answer(
                question=qa.question,
                answer=answer_text,
                position=position,
                history=history
            )
            
            # 更新评分
            qa.tech_score = evaluation_result.get('techScore')
            qa.depth_score = evaluation_result.get('depthScore')
            qa.logic_score = evaluation_result.get('logicScore')
            qa.match_score = evaluation_result.get('matchScore')
            qa.feedback = evaluation_result.get('feedback')
            qa.next_question = evaluation_result.get('nextQuestion')
            db.session.commit()
            
            # 如果LLM生成下一问题，保存并添加到历史
            next_question = evaluation_result.get('nextQuestion')
            next_question_id = None
            if next_question and next_question.strip():
                next_qa = QuestionAnswer(
                    interview_id=interview_id,
                    question=next_question,
                    created_at=datetime.utcnow()
                )
                db.session.add(next_qa)
                db.session.commit()
                next_question_id = next_qa.id
                
                # 添加助手回复到历史
                history.append({"role": "assistant", "content": next_question})
            
            # 保存更新的历史
            self.conversation_history[interview_id] = history
            
            # 如果面试结束
            if evaluation_result.get('endInterview'):
                self.end_interview(interview_id)
            
            # 返回增强的评估结果
            result = dict(evaluation_result)
            if next_question_id:
                result['nextQuestionId'] = next_question_id
            
            return result
            
        except Exception as e:
            logger.error(f"处理回答失败: {str(e)}")
            db.session.rollback()
            raise
    
    def process_audio_answer(self, interview_id, question_id, audio_data):
        # 语音识别服务已移除，仅支持视频面试模式
        # 在视频面试中，音频由Qwen-Omni实时模型直接处理
        raise NotImplementedError("语音识别服务已移除。请使用视频面试模式，音频将由Qwen-Omni实时模型直接处理。")

    def save_conversation(self, interview_id, conversation):
        try:
            interview_id = int(interview_id)
            
            if not conversation:
                logger.warning(f"[InterviewService] 对话数据为空，跳过保存: interview_id={interview_id}")
                return
            
            qa_pairs = []
            i = 0
            while i < len(conversation) - 1:
                entry = conversation[i]
                next_entry = conversation[i + 1]
                if entry.get('role') == 'ai' and next_entry.get('role') == 'user':
                    qa_pairs.append((entry.get('content', ''), next_entry.get('content', '')))
                    i += 2
                else:
                    i += 1
            
            if not qa_pairs:
                logger.warning(f"[InterviewService] 无有效QA对: interview_id={interview_id}, messages={len(conversation)}")
                return
            
            existing_qas = QuestionAnswer.query.filter_by(interview_id=interview_id).all()
            existing_scored = {qa.question: qa for qa in existing_qas if qa.tech_score is not None}

            unscored_to_delete = [qa for qa in existing_qas if qa.tech_score is None]
            if unscored_to_delete:
                for qa in unscored_to_delete:
                    db.session.delete(qa)
                db.session.flush()

            for question, answer in qa_pairs:
                if question in existing_scored:
                    existing = existing_scored[question]
                    if not existing.answer or existing.answer.strip() != answer.strip():
                        existing.answer = answer
                    continue

                qa = QuestionAnswer(
                    interview_id=interview_id,
                    question=question,
                    answer=answer,
                    created_at=datetime.utcnow()
                )
                db.session.add(qa)
            
            db.session.commit()
            logger.info(f"[InterviewService] 保存对话记录: interview_id={interview_id}, QA对={len(qa_pairs)}, 已评分保留={len(existing_scored)}, 总消息={len(conversation)}")
            
        except (ValueError, TypeError) as e:
            logger.error(f"保存对话失败(参数错误): {str(e)}")
        except Exception as e:
            logger.error(f"保存对话失败: {str(e)}")
            db.session.rollback()

    def save_answer(self, interview_id, question_text, answer_text, audio_url=None):
        try:
            interview_id = int(interview_id)
            
            # 优先查找最近一条未回答的记录（save_question已创建）
            qa = QuestionAnswer.query.filter_by(
                interview_id=interview_id
            ).filter(
                QuestionAnswer.answer.is_(None)
            ).order_by(QuestionAnswer.created_at.desc()).first()

            if qa:
                qa.answer = answer_text
                if audio_url:
                    qa.audio_url = audio_url
                db.session.commit()
                logger.info(f"[InterviewService] 保存用户回答: interview_id={interview_id}, qa_id={qa.id}")
            else:
                # 没有待回答的记录，创建新的完整QA记录
                qa = QuestionAnswer(
                    interview_id=interview_id,
                    question=question_text or "语音回答",
                    answer=answer_text,
                    audio_url=audio_url,
                    created_at=datetime.utcnow()
                )
                db.session.add(qa)
                db.session.commit()
                logger.info(f"[InterviewService] 创建新QA记录并保存回答: interview_id={interview_id}, qa_id={qa.id}")
        except (ValueError, TypeError) as e:
            logger.error(f"保存回答失败(参数类型错误): interview_id={interview_id}, error={str(e)}")
        except Exception as e:
            logger.error(f"保存回答失败: {str(e)}")
            db.session.rollback()

    def save_question(self, interview_id, question_text):
        try:
            interview_id = int(interview_id)
            qa = QuestionAnswer(
                interview_id=interview_id,
                question=question_text,
                created_at=datetime.utcnow()
            )
            db.session.add(qa)
            db.session.commit()
            logger.info(f"[InterviewService] 保存AI问题: interview_id={interview_id}, qa_id={qa.id}")
        except (ValueError, TypeError) as e:
            logger.error(f"保存问题失败(参数类型错误): interview_id={interview_id}, error={str(e)}")
        except Exception as e:
            logger.error(f"保存问题失败: {str(e)}")
            db.session.rollback()

    def get_interview_record(self, interview_id):
        """根据ID获取面试记录"""
        try:
            record = InterviewRecord.query.get(interview_id)
            if not record:
                return None
            return record.to_dict()
        except Exception as e:
            logger.error(f"获取面试记录失败: {str(e)}")
            return None

    def create_interview_record(self, user_id=None, position=None, start_time=None):
        """创建新的面试记录"""
        try:
            if not position:
                position = 'java_backend'
            record = InterviewRecord(
                user_id=user_id,
                position=position,
                start_time=start_time or datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.session.add(record)
            db.session.commit()
            return record.to_dict()
        except Exception as e:
            logger.error(f"创建面试记录失败: {str(e)}")
            db.session.rollback()
            raise
    
    def end_interview(self, interview_id):
        try:
            record = InterviewRecord.query.get(interview_id)
            if not record:
                raise ValueError("面试记录不存在")
            
            if record.end_time is None:
                record.end_time = datetime.utcnow()
            
            report = self.generate_report(interview_id)
            import json
            record.report = json.dumps(report, ensure_ascii=False)
            
            db.session.commit()
            
            if interview_id in self.conversation_history:
                del self.conversation_history[interview_id]
            
            logger.info(f"面试 {interview_id} 已成功结束，报告已生成")
            return record.to_dict()
            
        except Exception as e:
            logger.error(f"结束面试失败: {str(e)}")
            db.session.rollback()
            raise
    
    def update_interview_end_time(self, interview_id):
        """更新面试记录的结束时间"""
        try:
            record = InterviewRecord.query.get(interview_id)
            if not record:
                logger.warning(f"面试记录不存在: {interview_id}")
                return False
            
            # 如果已经设置了结束时间，不再更新
            if record.end_time is not None:
                logger.info(f"面试 {interview_id} 已经结束于 {record.end_time}")
                return True
            
            record.end_time = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"面试结束时间已更新: {interview_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新面试结束时间失败: {str(e)}")
            db.session.rollback()
            return False
    
    def generate_report(self, interview_id):
        try:
            record = InterviewRecord.query.get(interview_id)
            if not record:
                raise ValueError("面试记录不存在")
            
            qa_list = QuestionAnswer.query.filter_by(interview_id=interview_id).all()
            
            position_display = self._get_position_display_name(record.position)
            
            duration_minutes = 0
            if record.start_time and record.end_time:
                duration_seconds = (record.end_time - record.start_time).total_seconds()
                duration_minutes = int(duration_seconds / 60)
            
            question_count = len(qa_list)
            
            qa_pairs_for_llm = []
            for qa in qa_list:
                qa_pairs_for_llm.append({
                    "question": qa.question,
                    "answer": qa.answer or "",
                    "feedback": qa.feedback or "",
                    "tech_score": qa.tech_score,
                    "depth_score": qa.depth_score,
                    "logic_score": qa.logic_score,
                    "match_score": qa.match_score
                })

            llm_report = self.llm_service.generate_comprehensive_report(
                qa_pairs=qa_pairs_for_llm,
                position=record.position
            )

            per_round = llm_report.get('perRound', [])

            tech_avg = 0
            depth_avg = 0
            logic_avg = 0
            match_avg = 0

            if per_round and len(per_round) == len(qa_list):
                tech_scores = [r.get('techScore', 0) or 0 for r in per_round]
                depth_scores = [r.get('depthScore', 0) or 0 for r in per_round]
                logic_scores = [r.get('logicScore', 0) or 0 for r in per_round]
                match_scores = [r.get('matchScore', 0) or 0 for r in per_round]
                tech_avg = sum(tech_scores) / len(tech_scores)
                depth_avg = sum(depth_scores) / len(depth_scores)
                logic_avg = sum(logic_scores) / len(logic_scores)
                match_avg = sum(match_scores) / len(match_scores)

                for i, qa in enumerate(qa_list):
                    if i < len(per_round):
                        pr = per_round[i]
                        qa.tech_score = int(pr.get('techScore', 0) or 0)
                        qa.depth_score = int(pr.get('depthScore', 0) or 0)
                        qa.logic_score = int(pr.get('logicScore', 0) or 0)
                        qa.match_score = int(pr.get('matchScore', 0) or 0)
                        qa.feedback = pr.get('feedback', '') or ''
                db.session.commit()
                logger.info(f"[InterviewService] 已保存 DeepSeek 评分到 {len(per_round)} 条 Q&A")
            else:
                estimated = llm_report.get('estimatedScores', {})
                tech_avg = float(estimated.get('technical', 7.0))
                depth_avg = float(estimated.get('depth', 7.0))
                logic_avg = float(estimated.get('logic', 7.0))
                match_avg = float(estimated.get('match', 7.0))

            overall_avg = (tech_avg + depth_avg + logic_avg + match_avg) / 4
            record.overall_score = overall_avg
            db.session.commit()

            radar_data = [
                {"name": "技术能力", "value": tech_avg},
                {"name": "知识深度", "value": depth_avg},
                {"name": "逻辑表达", "value": logic_avg},
                {"name": "岗位匹配", "value": match_avg}
            ]

            summary = llm_report.get('summary', '')
            evaluation = llm_report.get('evaluation', '')
            strengths = llm_report.get('strengths', [])
            weaknesses = llm_report.get('weaknesses', [])
            detailed_suggestions = llm_report.get('detailedSuggestions', [])

            records = []
            for i, qa in enumerate(qa_list, 1):
                if i <= len(per_round):
                    pr = per_round[i - 1]
                    scores = [
                        {"name": "技术", "value": pr.get('techScore', 0) or 0},
                        {"name": "深度", "value": pr.get('depthScore', 0) or 0},
                        {"name": "逻辑", "value": pr.get('logicScore', 0) or 0},
                        {"name": "匹配", "value": pr.get('matchScore', 0) or 0}
                    ]
                    feedback = pr.get('feedback', '') or qa.feedback or "暂无反馈"
                else:
                    scores = [
                        {"name": "技术", "value": qa.tech_score or 0},
                        {"name": "深度", "value": qa.depth_score or 0},
                        {"name": "逻辑", "value": qa.logic_score or 0},
                        {"name": "匹配", "value": qa.match_score or 0}
                    ]
                    feedback = qa.feedback or "暂无反馈"

                records.append({
                    "round": i,
                    "question": qa.question,
                    "answer": qa.answer or "（未回答）",
                    "scores": scores,
                    "feedback": feedback
                })

            report = {
                "interviewId": interview_id,
                "position": record.position,
                "positionName": position_display,
                "startTime": record.start_time.isoformat() if record.start_time else None,
                "endTime": record.end_time.isoformat() if record.end_time else None,
                "interviewDate": record.start_time.isoformat() if record.start_time else None,
                "scores": {
                    "technical": tech_avg,
                    "depth": depth_avg,
                    "logic": logic_avg,
                    "match": match_avg
                },
                "overallScore": overall_avg,
                "averageScore": overall_avg,
                "evaluation": evaluation,
                "summary": summary,
                "suggestions": detailed_suggestions,
                "duration": duration_minutes,
                "questionCount": question_count,
                "radarData": radar_data,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "detailedSuggestions": detailed_suggestions,
                "records": records
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成报告失败: {str(e)}")
            return {"error": str(e)}
    
    def _get_evaluation_text(self, overall_score, qa_pairs=None, position_display=None):
        total = len(qa_pairs) if qa_pairs else 0
        answered = sum(1 for qa in (qa_pairs or []) if qa.get('answer', '').strip() and qa.get('answer', '') != '（未回答）')

        if total == 0:
            return "本次面试未记录到有效的问答数据，无法生成评估。"

        level = "优秀" if overall_score >= 9.0 else ("良好" if overall_score >= 7.0 else ("一般" if overall_score >= 5.0 else "待提高"))

        text = f"综合评估：{level}（{overall_score:.1f}/10.0）。"

        if qa_pairs:
            topics = []
            for qa in qa_pairs:
                q = qa.get('question', '')
                short = q[:60] + '...' if len(q) > 60 else q
                topics.append(short)
            text += f"面试共{total}轮，涉及话题：{'；'.join(topics[:5])}。"

        if answered < total and total > 1:
            text += f"其中{total - answered}个问题未获得有效回答。"

        if overall_score >= 9.0:
            text += "候选人在面试中展现出扎实的技术功底和优秀的表达能力，各轮回答均有具体技术细节支撑。"
        elif overall_score >= 7.0:
            text += "候选人具备岗位所需的基本能力，部分回答有深度，但仍有提升空间。"
        elif overall_score >= 5.0:
            text += "候选人基本合格，但需要在核心技术理解和表达方面进一步加强。"
        else:
            text += "建议候选人加强核心技术学习，提升表达的逻辑性和条理性。"

        return text

    def _get_position_display_name(self, position):
        position_map = {
            'java_backend': 'Java后端开发工程师',
            'web_frontend': 'Web前端开发工程师',
            'fullstack_engineer': '全栈工程师',
            'bigdata_engineer': '大数据工程师'
        }
        return position_map.get(position, position or '技术面试')

    def _get_suggestions(self, tech_score, depth_score, logic_score, match_score, qa_pairs=None, position_display=None):
        suggestions = []

        if qa_pairs:
            unanswered = [qa for qa in qa_pairs if not qa.get('answer', '').strip() or qa.get('answer', '') == '（未回答）']
            if unanswered:
                missed_topics = [qa.get('question', '')[:50] for qa in unanswered[:3]]
                suggestions.append(f"需要补充回答以下问题：{'；'.join(missed_topics)}。")

        if tech_score < 7.0:
            suggestions.append("建议加强技术基础知识学习，重点掌握核心概念和原理。")
        if depth_score < 7.0:
            suggestions.append("建议深入理解技术原理和底层机制，不仅回答\"是什么\"，还要解释\"为什么\"。")
        if logic_score < 7.0:
            suggestions.append("建议提高表达的逻辑性和条理性，可使用STAR法则组织回答。")
        if match_score < 7.0:
            suggestions.append("建议更好地理解岗位要求，在回答中体现与岗位的匹配度。")

        if not suggestions:
            suggestions.append("整体表现良好，建议持续学习和实践，保持技术竞争力。")

        return " ".join(suggestions)