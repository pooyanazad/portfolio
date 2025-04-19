from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'images', 'uploads')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_title = db.Column(db.String(100), nullable=False, default="My Portfolio Blog")
    about_me = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True)
    cover_photo = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    github = db.Column(db.String(255), nullable=True)
    linkedin = db.Column(db.String(255), nullable=True)
    twitter = db.Column(db.String(255), nullable=True)
    custom_link_name = db.Column(db.String(50), nullable=True)
    custom_link_url = db.Column(db.String(255), nullable=True)
    theme = db.Column(db.String(20), default="happy-green")
    custom_css = db.Column(db.Text, nullable=True)

# Initialize database and create admin user
def create_tables():
    with app.app_context():
        # First check if the database file exists
        db_exists = os.path.exists('instance/blog.db')
        
        # If database doesn't exist, just create all tables
        if not db_exists:
            db.create_all()
        else:
            # Database exists, check if we need to update schema
            try:
                inspector = db.inspect(db.engine)
                # Check if site_settings table exists
                if 'site_settings' in inspector.get_table_names():
                    # Check if the new columns exist
                    has_custom_link_columns = all(
                        column in [c['name'] for c in inspector.get_columns('site_settings')]
                        for column in ['custom_link_name', 'custom_link_url']
                    )
                    
                    # If the custom link columns don't exist, we need to recreate the database
                    if not has_custom_link_columns:
                        # Backup existing data
                        existing_settings = None
                        existing_users = []
                        existing_posts = []
                        
                        try:
                            # Try to get existing data before schema change
                            existing_settings = db.session.query(SiteSettings).first()
                            existing_users = db.session.query(User).all()
                            existing_posts = db.session.query(Post).all()
                            
                            # Convert to dictionaries to preserve data
                            if existing_settings:
                                existing_settings = {c.name: getattr(existing_settings, c.name) 
                                                for c in existing_settings.__table__.columns 
                                                if c.name not in ['custom_link_name', 'custom_link_url']}
                            
                            existing_users = [{c.name: getattr(user, c.name) for c in user.__table__.columns} 
                                            for user in existing_users]
                            
                            existing_posts = [{c.name: getattr(post, c.name) for c in post.__table__.columns} 
                                            for post in existing_posts]
                            
                        except Exception as e:
                            print(f"Error backing up data: {e}")
                        
                        # Close session and drop all tables
                        db.session.close()
                        db.drop_all()
                        
                        # Recreate tables with new schema
                        db.create_all()
                        
                        # Restore data
                        if existing_settings:
                            settings = SiteSettings(**existing_settings)
                            db.session.add(settings)
                        
                        for user_data in existing_users:
                            user = User(**user_data)
                            db.session.add(user)
                        
                        for post_data in existing_posts:
                            post = Post(**post_data)
                            db.session.add(post)
                        
                        db.session.commit()
                        print("Database schema updated successfully!")
                else:
                    # Table doesn't exist, create all tables
                    db.create_all()
            except Exception as e:
                print(f"Error checking schema: {e}")
                # If any error occurs during inspection, just create all tables
                db.create_all()
        
        # Check if admin user exists, if not create one
        if not User.query.filter_by(username="pooyan").first():
            admin = User(
                username="pooyan",
                password_hash=generate_password_hash("StrongPaas4")
            )
            db.session.add(admin)
            
            # Add default site settings
            if not SiteSettings.query.first():
                settings = SiteSettings(
                    site_title="Pooyan's Portfolio",
                    about_me="I'm a passionate developer who loves creating beautiful web applications.",
                    theme="happy-green"
                )
                db.session.add(settings)
            
            db.session.commit()

# Pass current datetime to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Add this function to ensure settings are always available
@app.context_processor
def inject_settings():
    settings = SiteSettings.query.first()
    if not settings:
        # Create default settings if none exist
        settings = SiteSettings(
            site_title="My Portfolio Blog",
            about_me="Welcome to my portfolio blog.",
            theme="happy-green"
        )
        db.session.add(settings)
        db.session.commit()
    return {'settings': settings}

@app.route('/')
def home():
    settings = SiteSettings.query.first()
    posts = Post.query.filter_by(is_published=True).order_by(Post.date_posted.desc()).all()
    return render_template('index.html', settings=settings, posts=posts)

@app.route('/post/<int:post_id>')
def post(post_id):
    settings = SiteSettings.query.first()
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', settings=settings, post=post)

@app.route('/login', methods=['GET', 'POST'])
def login():
    settings = SiteSettings.query.first()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', settings=settings)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

# Admin routes
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/admin')
@login_required
def admin_dashboard():
    settings = SiteSettings.query.first()
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('admin/dashboard.html', settings=settings, posts=posts)

@app.route('/admin/posts/new', methods=['GET', 'POST'])
@login_required
def new_post():
    settings = SiteSettings.query.first()
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        is_published = True if request.form.get('is_published') else False
        
        post = Post(title=title, content=content, is_published=is_published)
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/post_form.html', settings=settings)

@app.route('/admin/posts/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    settings = SiteSettings.query.first()
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.is_published = True if request.form.get('is_published') else False
        
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/post_form.html', settings=settings, post=post)

@app.route('/admin/posts/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def edit_settings():
    settings = SiteSettings.query.first()
    
    if request.method == 'POST':
        settings.site_title = request.form.get('site_title')
        settings.about_me = request.form.get('about_me')
        settings.email = request.form.get('email') or None
        settings.github = request.form.get('github') or None
        settings.linkedin = request.form.get('linkedin') or None
        settings.twitter = request.form.get('twitter') or None
        settings.custom_link_name = request.form.get('custom_link_name') or None
        settings.custom_link_url = request.form.get('custom_link_url') or None
        settings.theme = request.form.get('theme')
        settings.custom_css = request.form.get('custom_css')
        
        # Handle profile picture upload
        if 'profile_pic' in request.files and request.files['profile_pic'].filename:
            profile_pic = request.files['profile_pic']
            filename = secure_filename(profile_pic.filename)
            profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_pic.save(profile_pic_path)
            settings.profile_pic = f'images/uploads/{filename}'
        
        # Handle cover photo upload
        if 'cover_photo' in request.files and request.files['cover_photo'].filename:
            cover_photo = request.files['cover_photo']
            filename = secure_filename(cover_photo.filename)
            cover_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cover_photo.save(cover_photo_path)
            settings.cover_photo = f'images/uploads/{filename}'
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('edit_settings'))
    
    return render_template('admin/settings.html', settings=settings)

if __name__ == '__main__':
    create_tables()  # Call the function to initialize database before running the app
    app.run(debug=True)
