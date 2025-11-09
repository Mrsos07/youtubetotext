from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db, User, Transcript
import requests
import os
import time
import secrets
import logging
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///youtube_transcripts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
# Only use secure cookies in production (HTTPS)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

# CORS Configuration - Only allow specific origins
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Security Logging
logging.basicConfig(
    filename='security.log',
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

db.init_app(app)

# Security Headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Only use HSTS in production
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://fonts.googleapis.com https://fonts.gstatic.com; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://fonts.googleapis.com; img-src 'self' data:; font-src 'self' https://fonts.gstatic.com data:;"
    return response

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# n8n webhook URLs
N8N_WEBHOOK_URL = "https://n8n.srv968786.hstgr.cloud/webhook/youtube_text"
N8N_CHAT_WEBHOOK_URL = "https://n8n.srv968786.hstgr.cloud/webhook/9e11a381-b5b2-4ff6-97ad-a9a2abd17784/chat"

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')
        remember = data.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Remember me functionality
            login_user(user, remember=remember)
            logging.info(f"Successful login for email: {email} from IP: {request.remote_addr}")
            if request.is_json:
                return jsonify({'success': True, 'message': 'تم تسجيل الدخول بنجاح'})
            return redirect(url_for('index'))
        
        # Log failed login attempt
        logging.warning(f"Failed login attempt for email: {email} from IP: {request.remote_addr}")
        
        if request.is_json:
            return jsonify({'success': False, 'message': 'البريد الإلكتروني أو كلمة المرور غير صحيحة'}), 401
        return render_template('login.html', error='البريد الإلكتروني أو كلمة المرور غير صحيحة')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Input validation
        if not username or len(username) < 3 or len(username) > 50:
            if request.is_json:
                return jsonify({'success': False, 'message': 'اسم المستخدم يجب أن يكون بين 3 و 50 حرف'}), 400
            flash('اسم المستخدم يجب أن يكون بين 3 و 50 حرف')
            return render_template('register.html')
        
        if not email or '@' not in email or len(email) > 120:
            if request.is_json:
                return jsonify({'success': False, 'message': 'البريد الإلكتروني غير صحيح'}), 400
            flash('البريد الإلكتروني غير صحيح')
            return render_template('register.html')
        
        if not password or len(password) < 6:
            if request.is_json:
                return jsonify({'success': False, 'message': 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'}), 400
            flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'success': False, 'message': 'البريد الإلكتروني مستخدم بالفعل'}), 400
            flash('البريد الإلكتروني مستخدم بالفعل')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'success': False, 'message': 'اسم المستخدم مستخدم بالفعل'}), 400
            flash('اسم المستخدم مستخدم بالفعل')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        if request.is_json:
            return jsonify({'success': True, 'message': 'تم إنشاء الحساب بنجاح'})
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/my-files')
@login_required
def my_files():
    transcripts = Transcript.query.filter_by(user_id=current_user.id).order_by(Transcript.created_at.desc()).all()
    return render_template('my_files.html', transcripts=transcripts)

@app.route('/api/my-transcripts')
@login_required
def get_my_transcripts():
    transcripts = Transcript.query.filter_by(user_id=current_user.id).order_by(Transcript.created_at.desc()).all()
    return jsonify([t.to_dict() for t in transcripts])

@app.route('/api/transcript/<int:transcript_id>')
@login_required
def get_single_transcript(transcript_id):
    transcript = Transcript.query.filter_by(id=transcript_id, user_id=current_user.id).first()
    if not transcript:
        return jsonify({'error': 'Transcript not found'}), 404
    return jsonify(transcript.to_dict())

@app.route('/api/transcript', methods=['POST'])
@login_required
def get_transcript():
    try:
        print("=== Received transcript request ===")
        data = request.get_json()
        print(f"Request data: {data}")
        
        url = data.get('url') if data else None
        
        if not url:
            print("ERROR: No URL provided")
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate YouTube URL
        import re
        youtube_regex = r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
        if not re.match(youtube_regex, url):
            print("ERROR: Invalid YouTube URL")
            return jsonify({'error': 'رابط يوتيوب غير صحيح'}), 400
        
        print(f"Video URL: {url}")
        print(f"Sending to n8n: {N8N_WEBHOOK_URL}")
        
        # Send to n8n webhook (using GET as n8n expects)
        response = requests.get(
            N8N_WEBHOOK_URL,
            params={'url': url},
            timeout=300  # 5 minutes timeout
        )
        
        print(f"n8n Response Status: {response.status_code}")
        print(f"n8n Response Headers: {dict(response.headers)}")
        print(f"n8n Response Body: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Parsed JSON: {data}")
                
                # Check if it's just a workflow started message
                if isinstance(data, dict) and data.get('message') == 'Workflow was started':
                    print("WARNING: n8n returned 'Workflow was started' - webhook might be async")
                    return jsonify({
                        'error': 'n8n workflow بدأ لكن لم يرجع البيانات. تأكد من إعدادات Respond to Webhook في n8n'
                    }), 500
                
                # Handle array response from n8n
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
                
                # Save to database
                transcript = Transcript(
                    user_id=current_user.id,
                    video_url=url,
                    video_title=data.get('videoTitle') or data.get('output', {}).get('subject'),
                    introduction=data.get('introduction') or data.get('output', {}).get('introduction'),
                    summary=data.get('summary'),
                    main_points=data.get('mainPoints'),
                    full_content=data.get('fullContent') or data.get('fullcontent')
                )
                db.session.add(transcript)
                db.session.commit()
                print(f"Saved transcript ID: {transcript.id}")
                print(f"Video Title: {transcript.video_title}")
                print(f"Has Introduction: {bool(transcript.introduction)}")
                print(f"Has Summary: {bool(transcript.summary)}")
                print(f"Has Main Points: {bool(transcript.main_points)}")
                
                return jsonify(data)
            except Exception as json_error:
                print(f"JSON Parse Error: {json_error}")
                return jsonify({'fullContent': response.text})
        else:
            print(f"ERROR: n8n returned {response.status_code}")
            return jsonify({
                'error': f'n8n returned status {response.status_code}',
                'details': response.text[:500]
            }), response.status_code
            
    except requests.exceptions.Timeout:
        print("ERROR: Request timeout")
        return jsonify({'error': 'Request timeout - video processing takes too long'}), 504
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        print("=== Received chat request ===")
        data = request.get_json()
        print(f"Chat data: {data}")
        
        message = data.get('message')
        session_id = data.get('sessionId')
        
        if not message:
            print("ERROR: No message provided")
            return jsonify({'error': 'Message is required'}), 400
        
        print(f"Message: {message}")
        print(f"Session ID: {session_id}")
        print(f"Sending to n8n: {N8N_CHAT_WEBHOOK_URL}")
        
        # Send to n8n chat webhook
        payload = {
            'chatInput': message,
            'sessionId': session_id or f'session-{int(time.time())}'
        }
        
        response = requests.post(
            N8N_CHAT_WEBHOOK_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"Chat Response Status: {response.status_code}")
        print(f"Chat Response: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            # Handle array response
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            return jsonify(result)
        else:
            print(f"ERROR: Chat webhook returned {response.status_code}")
            return jsonify({
                'error': f'Chat webhook returned status {response.status_code}',
                'details': response.text[:200]
            }), response.status_code
            
    except Exception as e:
        print(f"Chat Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Password Reset Routes
@app.route('/forgot-password', methods=['GET'])
def forgot_password_page():
    return render_template('forgot_password.html')

@app.route('/api/forgot-password', methods=['POST'])
@limiter.limit("3 per hour")
def forgot_password():
    """Handle forgot password request"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'البريد الإلكتروني مطلوب'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            reset_expiry = datetime.utcnow() + timedelta(hours=1)
            
            # Store token in user record (you'll need to add these fields to User model)
            user.reset_token = reset_token
            user.reset_token_expiry = reset_expiry
            db.session.commit()
            
            # In production, send email here
            reset_link = f"{request.host_url}reset-password/{reset_token}"
            
            # TODO: Send email with reset_link
            # For development only - log the link
            if os.environ.get('FLASK_ENV') != 'production':
                logging.info(f"Password reset link for {email}: {reset_link}")
            
            return jsonify({
                'success': True,
                'message': 'تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني'
            })
        else:
            # Don't reveal if email exists or not (security best practice)
            return jsonify({
                'success': True,
                'message': 'إذا كان البريد الإلكتروني موجوداً، سيتم إرسال رابط إعادة التعيين'
            })
            
    except Exception as e:
        print(f"Forgot password error: {str(e)}")
        return jsonify({'error': 'حدث خطأ، يرجى المحاولة مرة أخرى'}), 500

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset"""
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        return render_template('reset_password.html', error='رابط إعادة التعيين غير صالح أو منتهي الصلاحية', token=token)
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or len(password) < 6:
            return render_template('reset_password.html', error='كلمة المرور يجب أن تكون 6 أحرف على الأقل', token=token)
        
        if password != confirm_password:
            return render_template('reset_password.html', error='كلمتا المرور غير متطابقتين', token=token)
        
        # Update password
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        return render_template('login.html', success='تم تغيير كلمة المرور بنجاح! يمكنك الآن تسجيل الدخول')
    
    return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    app.run(debug=True, host='0.0.0.0', port=5000)
