import io
import logging
import sys
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._register_chinese_fonts()
        self._setup_custom_styles()
    
    def _register_chinese_fonts(self):
        """注册中文字体"""
        import platform
        import os
        
        # 根据操作系统定义字体路径
        system = platform.system()
        font_candidates = []
        
        if system == 'Windows':
            # Windows系统常见中文字体
            font_candidates = [
                ("msyh", "Microsoft YaHei", "C:\\Windows\\Fonts\\msyh.ttc"),
                ("msyhbd", "Microsoft YaHei Bold", "C:\\Windows\\Fonts\\msyhbd.ttc"),
                ("simhei", "SimHei", "C:\\Windows\\Fonts\\simhei.ttf"),
                ("simsun", "SimSun", "C:\\Windows\\Fonts\\simsun.ttc"),
                ("kaiti", "KaiTi", "C:\\Windows\\Fonts\\kaiti.ttf"),
                ("fangsong", "FangSong", "C:\\Windows\\Fonts\\fangsong.ttf"),
            ]
        elif system == 'Linux':
            # Linux系统常见中文字体路径
            linux_font_paths = [
                '/usr/share/fonts/truetype/microsoft/msyh.ttf',
                '/usr/share/fonts/truetype/microsoft/msyhbd.ttf',
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            ]
            for font_path in linux_font_paths:
                if os.path.exists(font_path):
                    font_name = os.path.splitext(os.path.basename(font_path))[0]
                    font_candidates.append((font_name, font_name, font_path))
        elif system == 'Darwin':  # macOS
            # macOS系统常见中文字体路径
            mac_font_paths = [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/System/Library/Fonts/STHeiti Medium.ttc',
                '/Library/Fonts/Microsoft/msyh.ttf',
            ]
            for font_path in mac_font_paths:
                if os.path.exists(font_path):
                    font_name = os.path.splitext(os.path.basename(font_path))[0]
                    font_candidates.append((font_name, font_name, font_path))
        
        registered_font = None
        
        for font_name, font_display_name, font_path in font_candidates:
            try:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    logger.info(f"成功注册字体: {font_display_name} ({font_name})")
                    registered_font = font_name
                    break
                else:
                    logger.debug(f"字体文件不存在: {font_path}")
            except Exception as e:
                logger.debug(f"无法注册字体 {font_display_name}: {str(e)}")
                continue
        
        # 如果找不到任何中文字体，使用ReportLab标准字体（Helvetica）
        if registered_font is None:
            logger.warning("无法注册任何中文字体，将使用标准字体Helvetica（可能导致中文显示问题）")
            # Helvetica是PDF标准字体，不需要注册
            registered_font = "Helvetica"
        
        # 设置默认字体
        self.chinese_font = registered_font
        logger.info(f"PDF服务使用字体: {self.chinese_font}")
    
    def _setup_custom_styles(self):
        """设置自定义样式"""
        # 标题样式
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontName=self.chinese_font,
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#1a237e')
        ))
        
        # 副标题样式
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Heading2'],
            fontName=self.chinese_font,
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#3949ab')
        ))
        
        # 章节标题样式
        self.styles.add(ParagraphStyle(
            name='ReportSectionTitle',
            parent=self.styles['Heading3'],
            fontName=self.chinese_font,
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#303f9f'),
            borderPadding=5,
            borderWidth=1,
            borderColor=colors.HexColor('#c5cae9'),
            borderRadius=3,
            backColor=colors.HexColor('#e8eaf6')
        ))
        
        # 强调文本样式
        self.styles.add(ParagraphStyle(
            name='ReportEmphasis',
            parent=self.styles['Normal'],
            fontName=self.chinese_font,
            fontSize=12,
            textColor=colors.HexColor('#d32f2f'),
            spaceAfter=5
        ))
        
        # 正常文本样式
        self.styles.add(ParagraphStyle(
            name='ReportBodyText',
            parent=self.styles['Normal'],
            fontName=self.chinese_font,
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=10,
            leading=14,  # 行间距
            wordWrap='CJK'
        ))
        
        # 列表项样式
        self.styles.add(ParagraphStyle(
            name='ReportListItem',
            parent=self.styles['ReportBodyText'],
            fontName=self.chinese_font,
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=6,
            leading=14  # 继承行间距
        ))
        
        # 分数样式
        self.styles.add(ParagraphStyle(
            name='ReportScore',
            parent=self.styles['Normal'],
            fontName=self.chinese_font,
            fontSize=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#388e3c'),
            spaceAfter=10
        ))
    
    def generate_interview_report_pdf(self, report_data):
        """
        生成面试报告PDF
        
        Args:
            report_data: 报告数据字典，包含以下字段：
                - interviewId: 面试ID
                - position: 岗位名称
                - startTime: 开始时间
                - endTime: 结束时间
                - scores: 各项得分
                - overallScore: 综合得分
                - evaluation: 评估文本
                - suggestions: 建议
                - duration: 面试时长（分钟）
                - questionCount: 问题数量
                - strengths: 亮点列表
                - weaknesses: 待改进项列表
                - detailedSuggestions: 详细建议列表
                - records: 面试记录列表
        
        Returns:
            bytes: PDF文件内容
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
                embedFonts=True
            )
            
            story = []
            
            # 1. 封面
            story.extend(self._generate_cover_page(report_data))
            story.append(PageBreak())
            
            # 2. 摘要部分
            story.extend(self._generate_summary_section(report_data))
            
            # 3. 能力评估
            story.extend(self._generate_skills_section(report_data))
            
            # 4. 详细评估
            story.extend(self._generate_assessment_section(report_data))
            
            # 5. 提升建议
            story.extend(self._generate_suggestions_section(report_data))
            
            # 6. 面试记录
            story.extend(self._generate_records_section(report_data))
            
            # 构建PDF
            doc.build(story)
            buffer.seek(0)
            
            logger.info(f"成功生成面试报告PDF，面试ID: {report_data.get('interviewId')}")
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"生成PDF失败: {str(e)}")
            raise
    
    def _generate_cover_page(self, data):
        """生成封面页"""
        elements = []
        
        # 标题
        title = Paragraph("面试评估报告", self.styles['ReportTitle'])
        elements.append(Spacer(1, 3*inch))
        elements.append(title)
        
        # 副标题
        subtitle = Paragraph("AI模拟面试系统", self.styles['ReportSubtitle'])
        elements.append(Spacer(1, 1.5*inch))
        elements.append(subtitle)
        
        # 面试信息表格
        info_data = [
            ["面试岗位", data.get('position', '未指定')],
            ["面试ID", str(data.get('interviewId', 'N/A'))],
            ["开始时间", self._format_datetime(data.get('startTime'))],
            ["结束时间", self._format_datetime(data.get('endTime'))],
            ["面试时长", f"{data.get('duration', 0)}分钟"],
            ["问题数量", f"{data.get('questionCount', 0)}个"],
        ]
        
        info_table = Table(info_data, colWidths=[2.2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(Spacer(1, 1.5*inch))
        elements.append(info_table)
        
        # 生成日期
        elements.append(Spacer(1, 2*inch))
        date_text = Paragraph(f"生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}", 
                              self.styles['ReportBodyText'])
        elements.append(date_text)
        
        return elements
    
    def _generate_summary_section(self, data):
        """生成摘要部分"""
        elements = []
        
        # 章节标题
        section_title = Paragraph("报告摘要", self.styles['ReportSectionTitle'])
        elements.append(section_title)
        
        # 综合得分
        overall_score = data.get('overallScore', 0)
        score_text = f"<font size='24' color='#388e3c'><b>{overall_score:.1f}</b></font> / 10.0"
        score_para = Paragraph(f"综合得分: {score_text}", self.styles['ReportBodyText'])
        elements.append(score_para)
        
        # 评估文本
        evaluation = data.get('evaluation', '')
        if evaluation:
            # 包装长文本以改善换行
            wrapped_evaluation = self._wrap_chinese_text(evaluation, max_chars_per_line=40)
            eval_para = Paragraph(f"<b>评估:</b> {wrapped_evaluation}", self.styles['ReportBodyText'])
            elements.append(eval_para)
        
        # 分数详情表格
        scores = data.get('scores', {})
        if scores:
            score_data = [
                ["评估维度", "得分", "评级"],
                ["技术能力", f"{scores.get('technical', 0):.1f}", self._get_rating(scores.get('technical', 0))],
                ["知识深度", f"{scores.get('depth', 0):.1f}", self._get_rating(scores.get('depth', 0))],
                ["逻辑表达", f"{scores.get('logic', 0):.1f}", self._get_rating(scores.get('logic', 0))],
                ["岗位匹配", f"{scores.get('match', 0):.1f}", self._get_rating(scores.get('match', 0))],
            ]
            
            score_table = Table(score_data, colWidths=[2.2*inch, 1.5*inch, 2*inch])
            score_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTWEIGHT', (0, 0), (-1, 0), 'BOLD'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fafafa')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('PADDING', (0, 0), (-1, -1), 10),
            ]))
            
            elements.append(Spacer(1, 0.2*inch))
            elements.append(score_table)
        
        elements.append(Spacer(1, 0.3*inch))
        return elements
    
    def _generate_skills_section(self, data):
        """生成能力评估部分"""
        elements = []
        
        section_title = Paragraph("能力评估", self.styles['ReportSectionTitle'])
        elements.append(section_title)
        
        scores = data.get('scores', {})
        if scores:
            skills_text = (
                "基于您在面试中的表现，我们对您的能力维度进行了评估：<br/>"
                f"• <b>技术能力 ({scores.get('technical', 0):.1f}/10)</b>: 评估您的技术知识掌握程度和实践能力<br/>"
                f"• <b>知识深度 ({scores.get('depth', 0):.1f}/10)</b>: 评估您对技术原理的深入理解程度<br/>"
                f"• <b>逻辑表达 ({scores.get('logic', 0):.1f}/10)</b>: 评估您表达的逻辑性和条理性<br/>"
                f"• <b>岗位匹配 ({scores.get('match', 0):.1f}/10)</b>: 评估您与目标岗位的匹配度<br/>"
            )
            skills_para = Paragraph(skills_text, self.styles['ReportBodyText'])
            elements.append(skills_para)
        else:
            no_data = Paragraph("暂无能力评估数据", self.styles['ReportBodyText'])
            elements.append(no_data)
        
        elements.append(Spacer(1, 0.3*inch))
        return elements
    
    def _generate_assessment_section(self, data):
        """生成详细评估部分"""
        elements = []
        
        section_title = Paragraph("详细评估", self.styles['ReportSectionTitle'])
        elements.append(section_title)
        
        # 亮点与优势
        strengths = data.get('strengths', [])
        if strengths:
            elements.append(Paragraph("<b>亮点与优势:</b>", self.styles['ReportBodyText']))
            for i, strength in enumerate(strengths, 1):
                item = Paragraph(f"• {strength}", self.styles['ReportListItem'])
                elements.append(item)
            elements.append(Spacer(1, 0.1*inch))
        
        # 待改进项
        weaknesses = data.get('weaknesses', [])
        if weaknesses:
            elements.append(Paragraph("<b>待改进项:</b>", self.styles['ReportBodyText']))
            for i, weakness in enumerate(weaknesses, 1):
                item = Paragraph(f"• {weakness}", self.styles['ReportListItem'])
                elements.append(item)
        
        elements.append(Spacer(1, 0.3*inch))
        return elements
    
    def _generate_suggestions_section(self, data):
        """生成提升建议部分"""
        elements = []
        
        section_title = Paragraph("提升建议", self.styles['ReportSectionTitle'])
        elements.append(section_title)
        
        suggestions = data.get('detailedSuggestions', data.get('suggestions', []))
        
        if isinstance(suggestions, list) and suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                if isinstance(suggestion, dict):
                    title = suggestion.get('title', f'建议{i}')
                    description = suggestion.get('description', '')
                    resources = suggestion.get('resources', '')
                    
                    title_para = Paragraph(f"<b>{i}. {title}</b>", self.styles['ReportBodyText'])
                    elements.append(title_para)
                    
                    if description:
                        # 包装描述文本以改善换行
                        wrapped_description = self._wrap_chinese_text(description, max_chars_per_line=50)
                        desc_para = Paragraph(f"{wrapped_description}", self.styles['ReportBodyText'])
                        elements.append(desc_para)
                    
                    if resources:
                        # 包装资源文本以改善换行
                        wrapped_resources = self._wrap_chinese_text(resources, max_chars_per_line=50)
                        res_para = Paragraph(f"<font color='#1976d2'>推荐资源:</font> {wrapped_resources}", 
                                            ParagraphStyle('Resource', parent=self.styles['ReportBodyText'], 
                                                         leftIndent=20, textColor=colors.HexColor('#424242')))
                        elements.append(res_para)
                    
                    elements.append(Spacer(1, 0.1*inch))
                else:
                    # 如果是字符串形式的建议
                    item = Paragraph(f"{i}. {suggestion}", self.styles['ReportListItem'])
                    elements.append(item)
        elif isinstance(suggestions, str):
            # 如果是字符串形式的建议
            wrapped_suggestions = self._wrap_chinese_text(suggestions, max_chars_per_line=50)
            sugg_para = Paragraph(wrapped_suggestions, self.styles['ReportBodyText'])
            elements.append(sugg_para)
        else:
            no_data = Paragraph("暂无提升建议", self.styles['ReportBodyText'])
            elements.append(no_data)
        
        elements.append(Spacer(1, 0.3*inch))
        return elements
    
    def _generate_records_section(self, data):
        """生成面试记录部分"""
        elements = []
        
        section_title = Paragraph("面试记录", self.styles['ReportSectionTitle'])
        elements.append(section_title)
        
        records = data.get('records', [])
        
        if not records:
            no_data = Paragraph("暂无面试记录", self.styles['ReportBodyText'])
            elements.append(no_data)
            return elements
        
        for i, record in enumerate(records, 1):
            # 问题卡片
            question_text = f"<b>第{i}轮: {record.get('question', '问题')}</b>"
            question_para = Paragraph(question_text, self.styles['ReportBodyText'])
            elements.append(question_para)
            
            # 回答
            answer = record.get('answer', '')
            if answer:
                # 包装回答文本以改善换行
                wrapped_answer = self._wrap_chinese_text(answer, max_chars_per_line=50)
                answer_para = Paragraph(f"<font color='#2e7d32'><b>您的回答:</b></font> {wrapped_answer}", 
                                       ParagraphStyle('Answer', parent=self.styles['ReportBodyText'], 
                                                    leftIndent=20, backColor=colors.HexColor('#f1f8e9')))
                elements.append(answer_para)
            
            # 得分
            scores = record.get('scores', [])
            if scores:
                score_texts = []
                for score in scores:
                    if isinstance(score, dict):
                        name = score.get('name', '')
                        value = score.get('value', 0)
                        score_texts.append(f"{name}: {value}/10")
                    else:
                        score_texts.append(str(score))
                
                if score_texts:
                    scores_text = f"<font color='#d84315'><b>评分:</b></font> {', '.join(score_texts)}"
                    scores_para = Paragraph(scores_text, self.styles['ReportBodyText'])
                    elements.append(scores_para)
            
            # 反馈
            feedback = record.get('feedback', '')
            if feedback:
                # 包装反馈文本以改善换行
                wrapped_feedback = self._wrap_chinese_text(feedback, max_chars_per_line=50)
                feedback_para = Paragraph(f"<font color='#1565c0'><b>反馈:</b></font> {wrapped_feedback}", 
                                         ParagraphStyle('Feedback', parent=self.styles['ReportBodyText'], 
                                                      leftIndent=20, backColor=colors.HexColor('#e3f2fd')))
                elements.append(feedback_para)
            
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _format_datetime(self, dt_str):
        """格式化日期时间字符串"""
        if not dt_str:
            return "N/A"
        
        try:
            # 处理ISO格式时间
            if 'T' in dt_str:
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            
            return dt.strftime('%Y年%m月%d日 %H:%M')
        except:
            return dt_str
    
    def _wrap_chinese_text(self, text, max_chars_per_line=None):
        """
        包装中文文本，改善换行
        
        Args:
            text: 要包装的中文文本
            max_chars_per_line: 每行最大字符数（None表示自动）
        
        Returns:
            包装后的文本，包含<br/>标签以改善换行
        """
        if not text:
            return text
        
        # 如果不需要包装，直接返回
        if max_chars_per_line is None or len(text) <= max_chars_per_line:
            return text
        
        import re
        
        # 常见中文标点符号
        punctuation = r'[。！？；：，、]'
        
        # 第一步：在所有标点符号后添加<br/>标签
        # 使用正向预查确保不会重复添加
        wrapped = re.sub(f'({punctuation})(?!<br/>)', r'\1<br/>', text)
        
        # 第二步：在长段落中每10个字符后添加零宽度空格（换行机会）
        # 只对没有标点的长段落进行处理
        lines = wrapped.split('<br/>')
        result_lines = []
        
        for line in lines:
            # 如果一行没有标点且长度超过阈值，添加零宽度空格
            if len(line) > 15 and not re.search(punctuation, line):
                # 每10个字符后添加零宽度空格
                chars = list(line)
                for i in range(len(chars) - 1, 0, -1):
                    if i % 10 == 0:
                        chars.insert(i, '&#8203;')
                line = ''.join(chars)
            result_lines.append(line)
        
        # 重新组合，用<br/>连接所有行
        return '<br/>'.join(result_lines)
    
    def _get_rating(self, score):
        """根据分数获取评级"""
        if score >= 9.0:
            return "优秀"
        elif score >= 7.0:
            return "良好"
        elif score >= 5.0:
            return "一般"
        else:
            return "待提高"