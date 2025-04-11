import unittest
from app import app, db, User, Post, SiteSettings
import os
import tempfile

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            # Create test user
            user = User(username="testuser", password_hash="pbkdf2:sha256:150000$abc123")
            db.session.add(user)
            # Create test settings
            settings = SiteSettings(site_title="Test Blog")
            db.session.add(settings)
            # Create test post
            post = Post(title="Test Post", content="This is a test post", is_published=True)
            db.session.add(post)
            db.session.commit()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Blog', response.data)

    def test_post_page(self):
        response = self.client.get('/post/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Post', response.data)

    def test_login_page(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

if __name__ == '__main__':
    unittest.main()
