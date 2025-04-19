# My Portfolio Blog

Hey there! 👋 This is my Flask-powered portfolio blog with a simple admin panel (You can change all elements from admin page). I built it to showcase my work and share my thoughts.

## What's Cool About It

### The Blog
- Clean design that works on all devices
- Super easy admin panel to manage content
- Multiple themes to match my style
- Social links and custom website integration
- Quick blog post creation and editing

### The Tech Magic
- Built with Flask and SQLite (keeping it simple!)
- Terraform deploys everything to AWS automatically
- GitHub Actions handles the CI/CD pipeline
- Nginx serves it up nice and fast

## Quick Start

1. Clone and install:
   ```
   pip install -r requirements.txt
   python app.py
   ```
2. Login at /login with:
   - Username: poyan
   - Password: StrongPaas4 (change this ASAP!)
## Deployment
I've automated everything:

1. Add your AWS secrets to GitHub:
   
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_REGION
   - SSH_KEY_NAME
   - EC2_SSH_KEY
2. Push to GitHub and watch the magic happen!
Your site will be live on the EC2 IP that shows up in the GitHub Actions output.

You can use it as a prsonal blog or deploy on AWS with terraform files, Happy blogging! ✨
