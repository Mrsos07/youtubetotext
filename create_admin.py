from app import app, db
from models import User

def create_admin():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@admin.com').first()
        
        if admin:
            print("Admin user already exists!")
            print(f"Email: admin@admin.com")
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@admin.com'
        )
        admin.set_password('Ss@0011')
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin user created successfully!")
        print(f"Email: admin@admin.com")
        print(f"Password: Ss@0011")
        print(f"Username: admin")

if __name__ == '__main__':
    create_admin()
