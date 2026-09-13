from .database import db
from datetime import datetime

class InterviewRecord(db.Model):
    __tablename__ = 'interview_record'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=True)
    position = db.Column(db.String(100), nullable=False)
    is_video_interview = db.Column(db.Boolean, nullable=False, default=False)
    video_session_id = db.Column(db.String(200), nullable=True)
    video_recording_url = db.Column(db.String(500), nullable=True)
    video_chat_model = db.Column(db.String(100), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    overall_score = db.Column(db.Numeric(5, 2), nullable=True)
    report = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    question_answers = db.relationship('QuestionAnswer', backref='interview', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'position': self.position,
            'isVideoInterview': self.is_video_interview,
            'videoSessionId': self.video_session_id,
            'videoRecordingUrl': self.video_recording_url,
            'videoChatModel': self.video_chat_model,
            'startTime': self.start_time.isoformat() if self.start_time else None,
            'endTime': self.end_time.isoformat() if self.end_time else None,
            'overallScore': float(self.overall_score) if self.overall_score else None,
            'report': self.report,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }