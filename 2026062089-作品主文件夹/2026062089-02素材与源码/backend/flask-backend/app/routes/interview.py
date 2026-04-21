import logging
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
        result = interview_service.end_interview(interview_id)
        return success(result)
    except Exception as e:
        return error(str(e))

@bp.route('/report/<int:interview_id>', methods=['GET'])
def get_report(interview_id):
    try:
        report = interview_service.generate_report(interview_id)
        return success(report)
    except Exception as e:
        return error(str(e))

@bp.route('/report/pdf/<int:interview_id>', methods=['GET'])
def download_report_pdf(interview_id):
    """下载面试报告PDF"""
    try:
        # 生成报告数据
        report_json = interview_service.generate_report(interview_id)
        
        # 如果是字符串形式的JSON，解析为字典
        if isinstance(report_json, str):
            import json
            report_data = json.loads(report_json)
        else:
            report_data = report_json
        
        # 获取面试记录，填充更多数据
        record = InterviewRecord.query.get(interview_id)
        if record:
            # 计算面试时长（分钟）
            if record.start_time and record.end_time:
                duration_seconds = (record.end_time - record.start_time).total_seconds()
                duration_minutes = int(duration_seconds / 60)
                report_data['duration'] = duration_minutes
            else:
                report_data['duration'] = 0
            
            # 获取问题数量
            question_count = QuestionAnswer.query.filter_by(interview_id=interview_id).count()
            report_data['questionCount'] = question_count
            
            # 获取详细建议（如果有）
            if 'suggestions' in report_data and isinstance(report_data['suggestions'], str):
                report_data['detailedSuggestions'] = [
                    {"title": "技术提升", "description": report_data['suggestions'], "resources": "相关学习资源"}
                ]
        
        # 设置默认值
        if 'strengths' not in report_data:
            # 根据得分生成亮点
            scores = report_data.get('scores', {})
            strengths = []
            if scores.get('technical', 0) >= 7.0:
                strengths.append("技术基础扎实")
            if scores.get('logic', 0) >= 7.0:
                strengths.append("表达逻辑清晰")
            if scores.get('match', 0) >= 7.0:
                strengths.append("岗位匹配度较高")
            report_data['strengths'] = strengths
        
        if 'weaknesses' not in report_data:
            # 根据得分生成待改进项
            scores = report_data.get('scores', {})
            weaknesses = []
            if scores.get('technical', 0) < 7.0:
                weaknesses.append("技术知识需要进一步加强")
            if scores.get('depth', 0) < 7.0:
                weaknesses.append("知识深度有待提升")
            if scores.get('logic', 0) < 7.0:
                weaknesses.append("表达条理性可以更好")
            if scores.get('match', 0) < 7.0:
                weaknesses.append("需要更深入了解岗位要求")
            report_data['weaknesses'] = weaknesses
        
        # 获取面试记录详情
        qa_list = QuestionAnswer.query.filter_by(interview_id=interview_id).all()
        records = []
        for i, qa in enumerate(qa_list, 1):
            record_item = {
                'question': qa.question,
                'answer': qa.answer or "暂无回答",
                'scores': [
                    {'name': '技术', 'value': qa.tech_score or 0},
                    {'name': '深度', 'value': qa.depth_score or 0},
                    {'name': '逻辑', 'value': qa.logic_score or 0},
                    {'name': '匹配', 'value': qa.match_score or 0}
                ],
                'feedback': qa.feedback or "暂无反馈"
            }
            records.append(record_item)
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