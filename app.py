from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Transcript
import requests
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///youtube_transcripts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db.init_app(app)

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
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            if request.is_json:
                return jsonify({'success': True, 'message': 'تم تسجيل الدخول بنجاح'})
            return redirect(url_for('index'))
        
        if request.is_json:
            return jsonify({'success': False, 'message': 'البريد الإلكتروني أو كلمة المرور غير صحيحة'}), 401
        flash('البريد الإلكتروني أو كلمة المرور غير صحيحة')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    app.run(debug=True, host='0.0.0.0', port=5000)
