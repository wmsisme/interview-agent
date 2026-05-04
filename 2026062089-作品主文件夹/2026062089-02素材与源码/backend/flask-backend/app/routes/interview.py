import logging
import json
import urllib.parse
from flask import Blueprint, request, jsonify, Response
from ..utils.response import success, error, bad_request
from ..models import db, InterviewRecord, QuestionAnswer
from ..services.interview_service import InterviewService
from ..services.pdf_service import PDFService

logger = logging.getLogger(__name__)
bp = Blueprint('interview', __name__, url_prefix='/api/interview')
interview_service = InterviewService()
pdf_service = PDFService()

@bp.route('/start', methods=['POST'])
def start_interview():
    try:
        data = request.get_json()
        if not data or 'position' not in data:
            return bad_request('Position is required')
        
        position = data.get('position')
        user_id = data.get('userId')
        
        # 调用服务层开始面试
        result = interview_service.start_interview(position, user_id)
        
        return success(result)
    except Exception as e:
        return error(str(e))

@bp.route('/answer', methods=['POST'])
def submit_answer():
    try:
        data = request.get_json()
        if not data:
            return bad_request('Request body is required')
        
        interview_id = data.get('interviewId')
        question_id = data.get('questionId')
        answer_text = data.get('answerText')
        
        if not interview_id or not question_id or not answer_text:
            return bad_request('interviewId, questionId, and answerText are required')
        
        # 调用服务层处理回答
        result = interview_service.process_answer(interview_id, question_id, answer_text)
        
        return success(result)
    except Exception as e:
        return error(str(e))

@bp.route('/answer/audio', methods=['POST'])
def submit_audio_answer():
    try:
        # 语音识别服务已移除，仅支持视频面试模式
        # 在视频面试中，音频由Qwen-Omni实时模型直接处理
        return error('语音识别服务已移除。请使用视频面试模式，音频将由Qwen-Omni实时模型直接处理。', code=410)
    except Exception as e:
        return error(str(e))

@bp.route('/end/<int:interview_id>', methods=['POST'])
def end_interview(interview_id):
    try:
        data = request.get_json(silent=True) or {}
        conversation = data.get('conversation', [])
        if conversation:
            interview_service.save_conversation(interview_id, conversation)
        result = interview_service.end_interview(interview_id)
        return success(result)
    except Exception as e:
        return error(str(e))

@bp.route('/conversation/<int:interview_id>', methods=['POST'])
def save_conversation(interview_id):
    try:
        data = request.get_json()
        if not data:
            return bad_request('Request body is required')
        conversation = data.get('conversation', [])
        if not conversation:
            return bad_request('conversation is required')
        interview_service.save_conversation(interview_id, conversation)
        return success({'saved': len(conversation)})
    except Exception as e:
        return error(str(e))

@bp.route('/report/<int:interview_id>', methods=['GET'])
def get_report(interview_id):
    try:
        record = InterviewRecord.query.get(interview_id)
        if not record:
            return error('面试记录不存在')
        
        if record.report:
            try:
                report = json.loads(record.report)
                logger.info(f"[Report] 使用缓存的面试报告: interview_id={interview_id}")
                return success(report)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"[Report] 缓存报告JSON解析失败，重新生成: interview_id={interview_id}")
        
        report = interview_service.generate_report(interview_id)
        return success(report)
    except Exception as e:
        return error(str(e))

@bp.route('/report/pdf/<int:interview_id>', methods=['GET'])
def download_report_pdf(interview_id):
    """下载面试报告PDF"""
    try:
        record = InterviewRecord.query.get(interview_id)
        if not record:
            return error('面试记录不存在')
        
        report_data = None
        if record.report:
            try:
                report_data = json.loads(record.report)
                logger.info(f"[PDF] 使用缓存的面试报告: interview_id={interview_id}")
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"[PDF] 缓存报告JSON解析失败，重新生成: interview_id={interview_id}")
        
        if not report_data:
            report_data = interview_service.generate_report(interview_id)
        
        if record.start_time and record.end_time:
            duration_seconds = (record.end_time - record.start_time).total_seconds()
            duration_minutes = int(duration_seconds / 60)
            report_data['duration'] = duration_minutes
        elif 'duration' not in report_data:
            report_data['duration'] = 0

        if 'questionCount' not in report_data or not report_data.get('questionCount'):
            question_count = QuestionAnswer.query.filter_by(interview_id=interview_id).count()
            report_data['questionCount'] = question_count

        if 'records' not in report_data or not report_data.get('records'):
            qa_list = QuestionAnswer.query.filter_by(interview_id=interview_id).all()
            records = []
            for i, qa in enumerate(qa_list, 1):
                records.append({
                    'round': i,
                    'question': qa.question,
                    'answer': qa.answer or "暂无回答",
                    'scores': [
                        {'name': '技术', 'value': qa.tech_score or 0},
                        {'name': '深度', 'value': qa.depth_score or 0},
                        {'name': '逻辑', 'value': qa.logic_score or 0},
                        {'name': '匹配', 'value': qa.match_score or 0}
                    ],
                    'feedback': qa.feedback or "暂无反馈"
                })
            report_data['records'] = records
        
        # 生成PDF
        pdf_content = pdf_service.generate_interview_report_pdf(report_data)
        
        # 返回PDF文件
        position_name = record.position if record else 'Unknown'
        # 创建安全的文件名（避免中文字符问题）
        safe_filename = f"Interview_Report_{position_name.replace(' ', '_')}_{interview_id}.pdf"
        # 创建UTF-8编码的文件名（用于现代浏览器）
        utf8_filename = f"面试报告_{position_name}_{interview_id}.pdf"
        encoded_filename = urllib.parse.quote(utf8_filename, safe='')
        
        # 设置Content-Disposition头，支持ASCII文件名和UTF-8编码文件名
        headers = {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'attachment; filename="{safe_filename}"; filename*=UTF-8\'\'{encoded_filename}'
        }
        
        return Response(pdf_content, headers=headers)
        
    except Exception as e:
        logger.error(f"生成PDF报告失败: {str(e)}")
        return error(f"生成PDF报告失败: {str(e)}")