import logging
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
            
            # 检查面试是否已经结束
            if record.end_time is not None:
                logger.info(f"面试 {interview_id} 已经结束于 {record.end_time}")
                # 面试已经结束，返回现有记录
                return record.to_dict()
            
            record.end_time = datetime.utcnow()
            
            # 计算平均分
            qa_list = QuestionAnswer.query.filter_by(interview_id=interview_id).all()
            
            if qa_list:
                tech_scores = [qa.tech_score for qa in qa_list if qa.tech_score is not None]
                depth_scores = [qa.depth_score for qa in qa_list if qa.depth_score is not None]
                logic_scores = [qa.logic_score for qa in qa_list if qa.logic_score is not None]
                match_scores = [qa.match_score for qa in qa_list if qa.match_score is not None]
                
                tech_avg = sum(tech_scores) / len(tech_scores) if tech_scores else 0
                depth_avg = sum(depth_scores) / len(depth_scores) if depth_scores else 0
                logic_avg = sum(logic_scores) / len(logic_scores) if logic_scores else 0
                match_avg = sum(match_scores) / len(match_scores) if match_scores else 0
                
                overall_avg = (tech_avg + depth_avg + logic_avg + match_avg) / 4
                record.overall_score = overall_avg
            
            # 生成报告
            report = self.generate_report(interview_id)
            record.report = report
            
            db.session.commit()
            
            # 清理对话历史
            if interview_id in self.conversation_history:
                del self.conversation_history[interview_id]
            
            logger.info(f"面试 {interview_id} 已成功结束")
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
            
            # 计算平均分
            tech_scores = [qa.tech_score for qa in qa_list if qa.tech_score is not None]
            depth_scores = [qa.depth_score for qa in qa_list if qa.depth_score is not None]
            logic_scores = [qa.logic_score for qa in qa_list if qa.logic_score is not None]
            match_scores = [qa.match_score for qa in qa_list if qa.match_score is not None]
            
            tech_avg = sum(tech_scores) / len(tech_scores) if tech_scores else 0
            depth_avg = sum(depth_scores) / len(depth_scores) if depth_scores else 0
            logic_avg = sum(logic_scores) / len(logic_scores) if logic_scores else 0
            match_avg = sum(match_scores) / len(match_scores) if match_scores else 0
            
            overall_avg = (tech_avg + depth_avg + logic_avg + match_avg) / 4
            
            # 计算面试时长（分钟）
            duration_minutes = 0
            if record.start_time and record.end_time:
                duration_seconds = (record.end_time - record.start_time).total_seconds()
                duration_minutes = int(duration_seconds / 60)
            
            # 获取问题数量
            question_count = len(qa_list)
            
            # 生成雷达图数据
            radar_data = [
                {"name": "技术能力", "value": tech_avg},
                {"name": "知识深度", "value": depth_avg},
                {"name": "逻辑表达", "value": logic_avg},
                {"name": "岗位匹配", "value": match_avg}
            ]
            
            # 根据得分生成亮点和待改进项
            strengths = []
            weaknesses = []
            
            if tech_avg >= 7.0:
                strengths.append("技术基础扎实，掌握核心概念")
            else:
                weaknesses.append("技术知识需要进一步加强")
                
            if depth_avg >= 7.0:
                strengths.append("对技术原理有深入理解")
            else:
                weaknesses.append("知识深度有待提升")
                
            if logic_avg >= 7.0:
                strengths.append("表达逻辑清晰，条理性强")
            else:
                weaknesses.append("表达条理性可以更好")
                
            if match_avg >= 7.0:
                strengths.append("与岗位要求匹配度较高")
            else:
                weaknesses.append("需要更深入了解岗位要求")
            
            # 如果没有亮点，添加默认提示
            if not strengths:
                strengths.append("展现了一定的学习潜力")
            
            # 如果没有待改进项，添加鼓励
            if not weaknesses:
                weaknesses.append("继续保持现有优秀表现")
            
            # 生成详细建议
            suggestions_text = self._get_suggestions(tech_avg, depth_avg, logic_avg, match_avg)
            
            # 构建详细建议列表
            detailed_suggestions = []
            if tech_avg < 7.0:
                detailed_suggestions.append({
                    "title": "技术知识提升",
                    "description": "建议系统学习岗位相关的核心技术知识，夯实基础。",
                    "resources": "《技术内幕》系列、官方文档、在线课程"
                })
            if depth_avg < 7.0:
                detailed_suggestions.append({
                    "title": "深入理解原理",
                    "description": "不仅要会用，更要理解背后的原理和设计思想。",
                    "resources": "《深入理解计算机系统》、技术博客、源码阅读"
                })
            if logic_avg < 7.0:
                detailed_suggestions.append({
                    "title": "逻辑表达能力",
                    "description": "练习用清晰的逻辑表达复杂概念，提升沟通效率。",
                    "resources": "《金字塔原理》、技术演讲视频、写作练习"
                })
            if match_avg < 7.0:
                detailed_suggestions.append({
                    "title": "岗位匹配提升",
                    "description": "深入了解目标岗位的具体要求和公司技术栈。",
                    "resources": "岗位JD分析、公司技术博客、行业报告"
                })
            
            # 如果没有详细建议，添加通用建议
            if not detailed_suggestions:
                detailed_suggestions.append({
                    "title": "持续学习成长",
                    "description": "技术领域日新月异，建议保持持续学习的态度。",
                    "resources": "技术社区、行业会议、在线学习平台"
                })
            
            # 生成报告JSON
            import json
            report = {
                "interviewId": interview_id,
                "position": record.position,
                "positionName": record.position,  # 前端期望的字段
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
                "averageScore": overall_avg,  # 前端期望的字段
                "evaluation": self._get_evaluation_text(overall_avg),
                "summary": self._get_evaluation_text(overall_avg),  # 前端期望的字段
                "suggestions": suggestions_text,
                "duration": duration_minutes,
                "questionCount": question_count,
                "radarData": radar_data,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "detailedSuggestions": detailed_suggestions
            }
            
            return json.dumps(report, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"生成报告失败: {str(e)}")
            return json.dumps({"error": str(e)})
    
    def _get_evaluation_text(self, overall_score):
        if overall_score >= 9.0:
            return "优秀：表现非常出色，技术扎实，表达清晰。"
        elif overall_score >= 7.0:
            return "良好：表现良好，具备岗位所需基本能力。"
        elif overall_score >= 5.0:
            return "一般：基本合格，但有提升空间。"
        else:
            return "待提高：需要加强技术学习和表达能力。"
    
    def _get_suggestions(self, tech_score, depth_score, logic_score, match_score):
        suggestions = []
        if tech_score < 7.0:
            suggestions.append("建议加强技术基础知识学习。")
        if depth_score < 7.0:
            suggestions.append("建议深入理解技术原理和底层机制。")
        if logic_score < 7.0:
            suggestions.append("建议提高表达的逻辑性和条理性。")
        if match_score < 7.0:
            suggestions.append("建议更好地理解岗位要求和公司文化。")
        
        return " ".join(suggestions) if suggestions else "继续努力，保持优秀表现。"