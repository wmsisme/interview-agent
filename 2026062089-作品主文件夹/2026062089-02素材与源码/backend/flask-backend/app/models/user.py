from .database import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    open_id = db.Column(db.String(100), nullable=True, unique=True)
    nickname = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # interviews = db.relationship('InterviewRecord', primaryjoin='User.id == InterviewRecord.user_id', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'openId': self.open_id,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }