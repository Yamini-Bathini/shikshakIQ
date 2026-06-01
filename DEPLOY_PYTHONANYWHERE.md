# Deploy ShikshakIQ on PythonAnywhere (Free, No Credit Card)

[PythonAnywhere](https://www.pythonanywhere.com/) has a free "Beginner" plan that runs Flask apps with **no credit card required**. This guide walks you through deploying the full app (React frontend + Flask backend) in one place.

---

## Step 1: Push your code to GitHub

If you haven't already:

```bash
cd "C:/ShikShak IQ"
git init
git add .
git commit -m "Initial commit"
# Create a repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/shikshak-iq.git
git push -u origin main
```

---

## Step 2: Sign up for PythonAnywhere

1. Go to https://www.pythonanywhere.com/plans/
2. Click **"Create a Beginner account"** (free, no credit card)
3. Sign up with your email and choose a username (e.g. `shikshakiq`)
4. Verify your email address

---

## Step 3: Open a Bash console on PythonAnywhere

1. Log in to PythonAnywhere
2. Click **"Dashboard"** → **"Bash"** (or "Open a Bash console here")
3. Clone your repo:
```bash
git clone https://github.com/YOUR_USERNAME/shikshak-iq.git
cd shikshak-iq
```

---

## Step 4: Build the frontend

```bash
cd shikshak-iq  # Enter the React frontend directory
npm install
npm run build
cd ..

# IMPORTANT: Copy dist/ to the project root so Flask can find it.
# Flask expects dist/ at the same level as the backend/ folder.
cp -r shikshak-iq/dist ./dist
```

This creates `dist/` at the project root level, which is where Flask looks for it (via `static_folder='../dist'` in `app.py`).

---

## Step 5: Create a Python virtual environment

```bash
# Go to the project root
cd ~/shikshak-iq

# Create a virtualenv (PythonAnywhere uses Python 3.10)
python3.10 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies (from the backend folder)
pip install -r backend/requirements.txt
```

---

## Step 6: Set up the Web App

1. Go to the PythonAnywhere **"Web"** tab
2. Click **"Add a new web app"**
3. Click **"Next"** → **"Manual configuration"** → **"Python 3.10"** → **"Next"**
4. Your app is now created at `yourusername.pythonanywhere.com`

### Configure the WSGI file

5. In the **"Code"** section, click on the **"WSGI configuration file"** link
6. Replace the entire contents with this:

```python
import os
import sys

# Path to the backend directory
path = '/home/YOUR_USERNAME/shikshak-iq/backend'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables (replace with YOUR values)
os.environ['SECRET_KEY'] = 'shikshak-iq-secret-change-me'
os.environ['JWT_SECRET_KEY'] = 'shikshak-iq-jwt-secret-change-me'
os.environ['GEMINI_API_KEY'] = 'AIzaSyACgAQ0pjjc0tb1nOJCatglnUwLs5Vfo90'
os.environ['GEMINI_API_KEYS'] = 'AIzaSyACgAQ0pjjc0tb1nOJCatglnUwLs5Vfo90,AIzaSyC0esZyMddVqWjQ0V_mgJrSylbAa8Pr_3o'

# Import and create the Flask app
from app import create_app
application = create_app()
```

**IMPORTANT:** Replace `YOUR_USERNAME` with your actual PythonAnywhere username.

### Configure static files

7. In the **"Static files"** section, add this entry:

| URL | Directory |
|-----|-----------|
| `/` | `/home/YOUR_USERNAME/shikshak-iq/dist` |

---

## Step 7: Reload and test

1. Go back to the **"Web"** tab
2. Click the **"Reload"** button
3. Wait 10 seconds

Your app is now live at: **https://YOUR_USERNAME.pythonanywhere.com**

---

## Step 8: Log in with demo credentials

| Role | Email / Username | Password |
|------|------------------|----------|
| **Principal** | `principal@shikshakiq.com` | `Principal@123` |
| **Teacher** | `lakshmi@shikshakiq.com` | `Teacher@123` |
| **Student** | `student.aarav` | `student123` |

---

## Troubleshooting

### "Internal Server Error"
Check the error log in the **"Web"** tab → **"Error log"** link.

### "Module not found" errors
Make sure you activated the virtualenv and installed `backend/requirements.txt`:
```bash
cd ~/shikshak-iq
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Static files not loading (white page with no UI)
Make sure you ran `npm run build` in the `shikshak-iq/` (frontend) folder, then copied it with `cp -r shikshak-iq/dist ./dist`. The static files section should point to `/home/YOUR_USERNAME/shikshak-iq/dist`.

### Database errors
If you see database errors, delete the old SQLite database and let it recreate:
```bash
cd ~/shikshak-iq/backend
rm -f instance/shikshakiq.db
# Then reload the web app
```
