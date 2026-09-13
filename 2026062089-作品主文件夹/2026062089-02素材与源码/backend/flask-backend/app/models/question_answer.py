from .database import db
from datetime import datetime

class QuestionAnswer(db.Model):
    __tablename__ = 'qa_detail'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interview_record.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=True)
    audio_url = db.Column(db.String(500), nullable=True)
    tech_score = db.Column(db.Integer, nullable=True)
    depth_score = db.Column(db.Integer, nullable=True)
    logic_score = db.Column(db.Integer, nullable=True)
    match_score = db.Column(db.Integer, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    next_question = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'interviewId': self.interview_id,
            'question': self.question,
            'answer': self.answer,
            'audioUrl': self.audio_url,
            'techScore': self.tech_score,
            'depthScore': self.depth_score,
            'logicScore': self.logic_score,
            'matchScore': self.match_score,
            'feedback': self.feedback,
            'nextQuestion': self.next_question,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }