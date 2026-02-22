import json
import time
from datetime import datetime
from flask import Response

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename 
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'secret-key-123' 
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_NAME = os.path.abspath(os.path.join(BASE_DIR, '..', 'database', 'forum.db'))

# Ensure upload folder exists
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # 1. Create users table with the correct columns
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL, 
            password TEXT NOT NULL, 
            role TEXT NOT NULL DEFAULT 'user',
            points INTEGER DEFAULT 0)""")
        
        # 2. Create posts table
        conn.execute("""CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            author TEXT DEFAULT 'Anonymous',
            title TEXT NOT NULL, 
            content TEXT NOT NULL, 
            category TEXT NOT NULL,
            likes INTEGER DEFAULT 0, 
            created_at TEXT NOT NULL)""")
        
        # 3. Create comments table
        conn.execute("""CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            post_id INTEGER NOT NULL,
            author TEXT DEFAULT 'Anonymous', 
            content TEXT NOT NULL, 
            created_at TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts(id))""")

        # 4. Create post_likes table
        # Fetch posts with an accurate comment count for each
        conn.execute("""CREATE TABLE IF NOT EXISTS post_likes (
            user_id TEXT NOT NULL,
            post_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, post_id),
            FOREIGN KEY (post_id) REFERENCES posts(id))""")

        # 5. Create challenges table
        conn.execute("""CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL)""")

        # 6. Create submissions table
        conn.execute("""CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            image_path TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(challenge_id, author),
            FOREIGN KEY (challenge_id) REFERENCES challenges(id))""")
        
        # 7. FORCE RE-INSERT/UPDATE DEFAULT USERS
        
        users_to_load = [
            ('admin', '1234', 'admin'),
            ('user', 'pass', 'user'),
            ('sarah', 'sarah123', 'user')
        ]
        
        for username, password, role in users_to_load:
            # Add them if they are missing
            conn.execute("INSERT OR IGNORE INTO users (username, password, role, points) VALUES (?, ?, ?, 0)", 
                         (username, password, role))
            # Update them in case the database existed but passwords were different
            conn.execute("UPDATE users SET password = ?, role = ? WHERE username = ?", 
                         (password, role, username))
        
        conn.commit()

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user' in session: 
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                            (username, password)).fetchone()
        conn.close()
        
        if user:
            # Crucial: set both 'user' and 'role' in session
            session['user'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        
        flash("Invalid username or password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- CONSOLIDATED DASHBOARD ---
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    
    # 1. Handle New Forum Post
    if request.method == 'POST' and 'title' in request.form:
        conn.execute("INSERT INTO posts (author, title, content, category, created_at) VALUES (?, ?, ?, ?, ?)",
                     (session['user'], 
                      request.form['title'], 
                      request.form['content'], 
                      request.form.get('category', 'Life Skills'), 
                      datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard') + "#tab-wisdom-forum")

    # 2. Fetch User Points & Leaderboard
    user_data = conn.execute("SELECT points FROM users WHERE username = ?", (session['user'],)).fetchone()
    user_points = user_data['points'] if user_data else 0
    leaderboard = conn.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 10").fetchall()

    # 3. FIXED FILTERING LOGIC
    selected_category = request.args.get('filter', 'all')
    
    if selected_category != 'all':
        # Filtered Query
        posts = conn.execute("""
            SELECT p.*, (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count 
            FROM posts p 
            WHERE p.category = ?
            ORDER BY p.id DESC
        """, (selected_category,)).fetchall()
    else:
        # Show All Query
        posts = conn.execute("""
            SELECT p.*, (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count 
            FROM posts p 
            ORDER BY p.id DESC
        """).fetchall()

    # 4. Fetch Challenges and Submissions
    challenges = conn.execute("SELECT * FROM challenges ORDER BY id DESC").fetchall()
    
    all_subs = conn.execute("""
        SELECT s.*, COALESCE(c.title, 'Deleted Challenge') AS challenge_name 
        FROM submissions s 
        LEFT JOIN challenges c ON s.challenge_id = c.id 
        ORDER BY s.id DESC
    """).fetchall()
    
    user_subs = conn.execute("""
        SELECT s.*, COALESCE(c.title, 'Deleted Challenge') AS challenge_name 
        FROM submissions s 
        LEFT JOIN challenges c ON s.challenge_id = c.id 
        WHERE s.author = ? 
        ORDER BY s.id DESC
    """, (session['user'],)).fetchall()
    
    user_submitted_ids = [s['challenge_id'] for s in user_subs]

    conn.close()
    
    return render_template('dashboard.html', 
                           posts=posts, 
                           challenges=challenges, 
                           all_submissions=all_subs, 
                           my_submissions=user_subs,
                           user_submissions=user_submitted_ids,
                           user_points=user_points,
                           leaderboard=leaderboard,
                           selected_category=selected_category, # Ensure this is passed!
                           is_admin=(session.get('role') == 'admin'))

# --- FORUM ACTIONS ---
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db()
    
    
    if request.method == 'POST' and 'comment' in request.form:
        conn.execute("INSERT INTO comments (post_id, author, content, created_at) VALUES (?, ?, ?, ?)",
                     (post_id, session['user'], request.form['comment'], datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
        # Redirect back to the same page to show the comment
        conn.close()
        return redirect(url_for('post_detail', post_id=post_id))
    
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    comments = conn.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY id DESC", (post_id,)).fetchall()
    conn.close()
    return render_template('post.html', post=post, comments=comments, is_admin=(session.get('role') == 'admin'))

@app.route('/delete_comment/<int:comment_id>/<int:post_id>', methods=['POST'])
def delete_comment(comment_id, post_id):
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db()
    comment = conn.execute('SELECT author FROM comments WHERE id = ?', (comment_id,)).fetchone()
    if comment and (session.get('role') == 'admin' or session.get('user') == comment['author']):
        conn.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('post_detail', post_id=post_id))

# --- OTHER ROUTES 
@app.route('/create_challenge', methods=['POST'])
def create_challenge():
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    title = request.form.get('title')
    desc = request.form.get('description') 
    if not desc or not title:
        flash("Title and Description are required!")
        return redirect(url_for('dashboard') + "#tab-challenges")
    conn = get_db()
    try:
        conn.execute("INSERT INTO challenges (title, description, created_at) VALUES (?, ?, ?)",
                     (title, desc, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('dashboard') + "#tab-challenges")

@app.route('/submit_challenge/<int:challenge_id>', methods=['POST'])
def submit_challenge(challenge_id):
    if 'user' not in session: return redirect(url_for('login'))
    
    user_answer = request.form.get('answer', '').strip()
    word_count = len(user_answer.split())
    if word_count < 30:
        flash(f"Submission too short! You wrote {word_count} words, but 30 are required. ✍️")
        return redirect(url_for('dashboard') + "#tab-challenges")
    file = request.files.get('file')
    image_path = None
    
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join('static/uploads', filename))
        image_path = filename
        
    conn = get_db()
    try:
        # 1. Record the challenge submission
        conn.execute("INSERT INTO submissions (challenge_id, author, content, image_path, created_at) VALUES (?, ?, ?, ?, ?)",
            (challenge_id, session['user'], user_answer, image_path, datetime.now().strftime("%Y-%m-%d %H:%M")))
        
        # 2. Award 20 points to the user
        conn.execute("UPDATE users SET points = points + 20 WHERE username = ?", (session['user'],))
        
        conn.commit()
        flash("Challenge submitted! You earned +20 points! 🏆")
    except sqlite3.IntegrityError:
        flash("Already submitted.")
    except Exception as e:
        flash("An error occurred.")
        print(f"Error: {e}")
    finally:
        conn.close()
    return redirect(url_for('dashboard') + "#tab-challenges")

# --- ADMIN ACTIONS: DELETE CHALLENGES & SUBMISSIONS ---

@app.route('/delete_challenge/<int:challenge_id>', methods=['POST'])
def delete_challenge(challenge_id):
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    
    conn = get_db()
    # First, delete all submissions associated with this challenge
    conn.execute("DELETE FROM submissions WHERE challenge_id = ?", (challenge_id,))
    # Then delete the challenge itself
    conn.execute("DELETE FROM challenges WHERE id = ?", (challenge_id,))
    conn.commit()
    conn.close()
    flash("Challenge and all associated submissions deleted.")
    return redirect(url_for('dashboard') + "#tab-challenges")

@app.route('/delete_submission/<int:submission_id>', methods=['POST'])
def delete_submission(submission_id):
    if 'user' not in session: 
        return redirect(url_for('login'))
    
    conn = get_db()
    try:
        # 1. Fetch the submission
        sub = conn.execute("SELECT author, image_path FROM submissions WHERE id = ?", (submission_id,)).fetchone()
        
        if not sub:
            return redirect(url_for('dashboard') + "#tab-challenges")

        # 2. PERMISSION CHECK: Admin OR the person who is logged in
        current_user = session.get('user')
        is_admin = session.get('role') == 'admin'
        
        if is_admin or current_user == sub['author']:
            # Delete physical image file
            if sub['image_path']:
                file_path = os.path.join(app.root_path, 'static', 'uploads', sub['image_path'])
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Delete from Database
            conn.execute("DELETE FROM submissions WHERE id = ?", (submission_id,))

           
            # We deduct from the sub['author'] to ensure the correct person loses points
            conn.execute("UPDATE users SET points = MAX(0, points - 20) WHERE username = ?", (sub['author'],))
            
            conn.commit()
            flash("Successfully deleted! 20 points deducted.")
        else:
            flash("You can only delete your own posts.")
            
    except Exception as e:
        print(f"Delete Error: {e}")
    finally:
        conn.close()
    
    return redirect(url_for('dashboard') + "#tab-challenges")

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    conn = get_db()
    post = conn.execute('SELECT author FROM posts WHERE id = ?', (post_id,)).fetchone()
    if post and (session.get('role') == 'admin' or session.get('user') == post['author']):
        conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('dashboard') + "#tab-wisdom-forum")

@app.route('/edit/<int:post_id>', methods=['POST'])
def edit_post(post_id):
    conn = get_db()
    post = conn.execute('SELECT author FROM posts WHERE id = ?', (post_id,)).fetchone()
    if post and session['user'] == post['author']:
        conn.execute('UPDATE posts SET content = ? WHERE id = ?', (request.form.get('content'), post_id))
        conn.commit()
    conn.close()
    return redirect(url_for('dashboard') + "#tab-wisdom-forum")

@app.route('/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    user_id, conn = session['user'], get_db()
    already_liked = conn.execute("SELECT 1 FROM post_likes WHERE user_id = ? AND post_id = ?", (user_id, post_id)).fetchone()
    if not already_liked:
        conn.execute("INSERT INTO post_likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        conn.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
    else:
        conn.execute("DELETE FROM post_likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        conn.execute("UPDATE posts SET likes = likes - 1 WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard') + "#tab-wisdom-forum")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)



# --- Global notifications + FAQ chatbot ---
FAQ_RESPONSES = {
    "help": "You can ask about onboarding, rewards, or points.",
    "rewards": "Rewards are earned by completing quests and activities.",
    "points": "Points are awarded for activity completion and participation.",
    "quests": "Quests guide learning and community participation.",
}


def _faq_reply(message: str) -> str:
    text = (message or "").strip().lower()
    if not text:
        return "Ask me about rewards, points, quests, or onboarding."
    for key, reply in FAQ_RESPONSES.items():
        if key in text:
            return reply
    return "Thanks! I can answer FAQs about rewards, points, quests, and onboarding."


def _notification_stream():
    while True:
        payload = {
            "message": "Live update: system is running.",
            "ts": datetime.utcnow().isoformat(),
        }
        yield f"data: {json.dumps(payload)}\n\n"


        time.sleep(10)


@app.get("/api/notifications/stream")
def api_notifications_stream():
    return Response(_notification_stream(), mimetype="text/event-stream")


@app.post("/api/chatbot")
def api_chatbot():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    return jsonify({"reply": _faq_reply(message)})
