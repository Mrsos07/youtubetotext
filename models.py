from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Password reset fields
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    transcripts = db.relationship('Transcript', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        # Use pbkdf2:sha256 with higher iterations for better security
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Transcript(db.Model):
    __tablename__ = 'transcripts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    video_url = db.Column(db.String(500), nullable=False)
    video_title = db.Column(db.String(500))
    introduction = db.Column(db.Text)
    summary = db.Column(db.Text)
    main_points = db.Column(db.Text)
    full_content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'video_url': self.video_url,
            'videoTitle': self.video_title,
            'introduction': self.introduction,
            'summary': self.summary,
            'mainPoints': self.main_points,
            'fullContent': self.full_content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<Transcript {self.video_title}>'
