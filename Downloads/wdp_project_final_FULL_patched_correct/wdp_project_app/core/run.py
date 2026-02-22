import json
import time
import re
import hashlib
import random
import smtplib
from difflib import SequenceMatcher
from datetime import datetime
from flask import Response

import json
import os
import sqlite3
import urllib.parse
import urllib.request
from datetime import datetime, date, timedelta
from email.message import EmailMessage
from pathlib import Path

from flask import Flask, send_from_directory, request, jsonify, session, redirect, render_template, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import DatabaseError

from app.extensions import db, migrate
from app.models import User, UserSetting, AuthEvent, CircleSignup, AchievementState


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "app" / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static", template_folder=str(TEMPLATES_DIR))

# Core config
app.config["SECRET_KEY"] = "reconnect-secret-key"

# Admin credentials (set environment variables in production)
ADMIN_ID = os.getenv("ADMIN_ID", "1234")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "5678")
ADMIN_EMAILS = {
    "ryanadmin",
    "seanadmin",
    "nicholasadmin",
    "adenadmin",
}
ADMIN_EMAIL_PASSWORDS = {
    "ryanadmin": "Ryan123!",
    "seanadmin": "Sean123!",
    "nicholasadmin": "Nicholas123!",
    "adenadmin": "Aden123!",
}

COACH_LIBRARY = {
    "general": {
        "icebreakers": [
            "Hi! How has your day been so far?",
            "Whatâ€™s something small that made you smile today?",
            "If you could do one relaxing thing this week, what would it be?",
        ],
        "questions": [
            "What hobbies do you enjoy most these days?",
            "Do you have a favourite place in Singapore to visit?",
            "Whatâ€™s a simple memory you treasure?",
        ],
        "respectful": [
            "Itâ€™s nice to chat with you today.",
            "I appreciate you sharing that with me.",
        ],
    },
    "hawker": {
        "icebreakers": [
            "Do you have a favourite hawker stall or dish?",
            "Have you tried any new food places recently?",
        ],
        "questions": [
            "Whatâ€™s your go-to comfort food?",
            "Which hawker centre do you enjoy most?",
        ],
    },
    "family": {
        "icebreakers": [
            "Do you have a favourite family tradition?",
            "Whatâ€™s a lovely family memory you like to share?",
        ],
        "questions": [
            "Who in your family inspires you the most?",
            "Whatâ€™s a family story you enjoy telling?",
        ],
    },
    "childhood": {
        "icebreakers": [
            "What was your favourite childhood game?",
            "What did you enjoy doing after school as a kid?",
        ],
        "questions": [
            "What was a popular snack when you were young?",
            "Do you remember your childhood neighbourhood?",
        ],
    },
    "hobbies": {
        "icebreakers": [
            "What hobby are you enjoying lately?",
            "Have you picked up any new activities recently?",
        ],
        "questions": [
            "What do you like to do on weekends?",
            "Is there a skill youâ€™d like to learn this year?",
        ],
    },
    "tech": {
        "icebreakers": [
            "Would you like help with phone or app tips?",
            "Whatâ€™s one app you find useful?",
        ],
        "questions": [
            "Is there a digital skill you want to improve?",
            "Have you tried video calling with family?",
        ],
    },
    "singapore": {
        "icebreakers": [
            "Which part of Singapore do you enjoy visiting?",
            "Do you prefer the city or parks here?",
        ],
        "questions": [
            "Whatâ€™s a place in Singapore youâ€™d recommend?",
            "Any favourite festivals or celebrations here?",
        ],
    },
    "support": {
        "icebreakers": [
            "Iâ€™m here with you. Want to share how youâ€™re feeling?",
            "Would a gentle chat help today?",
        ],
        "questions": [
            "What usually helps you feel a bit better?",
            "Would you like a simple, comforting topic to talk about?",
        ],
        "respectful": [
            "Thank you for trusting me with this.",
            "Itâ€™s okay to take things one step at a time.",
        ],
    },
    "meetup": {
        "icebreakers": [
            "Would you like to plan a simple meetup at a community place?",
            "Maybe we can meet at a cafÃ© or library nearby?",
        ],
        "questions": [
            "What day works best for you?",
            "Would you prefer a quiet or lively place?",
        ],
    },
}

COACH_REWRITE_MAP = {
    "bro": "my friend",
    "lol": "thatâ€™s amusing",
    "u": "you",
    "ur": "your",
    "wtf": "",
    "omg": "oh my",
}

ONBOARDING_LANDMARKS = [
    "Marina Bay Sands",
    "Gardens by the Bay",
    "Merlion Park",
    "Esplanade",
    "Chinatown",
    "Clarke Quay",
    "Orchard Road",
    "Botanic Gardens",
    "National Museum",
    "Sentosa",
    "VivoCity",
    "East Coast Park",
    "Changi Airport",
    "Jewel Changi",
    "Singapore Zoo",
    "Night Safari",
    "Bird Paradise",
    "Pulau Ubin",
    "Haji Lane",
    "Little India",
]

WELLBEING_MOOD_META = {
    "happy": {"emoji": "ðŸ˜Š", "label": "Happy", "score": 5},
    "good": {"emoji": "ðŸ™‚", "label": "Good", "score": 4},
    "neutral": {"emoji": "ðŸ˜", "label": "Neutral", "score": 3},
    "stressed": {"emoji": "ðŸ˜Ÿ", "label": "Stressed", "score": 2},
    "sad": {"emoji": "ðŸ˜ž", "label": "Sad", "score": 1},
}
WELLBEING_MOOD_SCORES = {k: v["score"] for k, v in WELLBEING_MOOD_META.items()}


INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)
DB_PATH = (BASE_DIR.parent.parent / "database" / "wdp_project_final.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialise extensions
# Flask-Migrate is optional for running, but useful when you start changing models.
db.init_app(app)
migrate.init_app(app, db)



CHAT_DB_PATH = DB_PATH
FORUM_DB_PATH = DB_PATH


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


def _get_chat_conn():
    conn = sqlite3.connect(CHAT_DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=3000;")
    return conn


def _init_chat_schema():
    conn = _get_chat_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            match_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            avatar TEXT NOT NULL,
            location TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS match_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            sender_seen INTEGER NOT NULL DEFAULT 0,
            receiver_seen INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            edited_at TEXT,
            is_deleted INTEGER NOT NULL DEFAULT 0,
            deleted_at TEXT
        );
        CREATE TABLE IF NOT EXISTS admin_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS circle_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            circle_title TEXT NOT NULL,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS profanities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            level TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );
        """
    )
    cols = {row["name"] for row in cur.execute("PRAGMA table_info(matches)").fetchall()}
    if "user_id" not in cols:
        cur.execute("ALTER TABLE matches ADD COLUMN user_id INTEGER")
    req_cols = {row["name"] for row in cur.execute("PRAGMA table_info(match_requests)").fetchall()}
    if "sender_seen" not in req_cols:
        cur.execute("ALTER TABLE match_requests ADD COLUMN sender_seen INTEGER NOT NULL DEFAULT 0")
        req_cols.add("sender_seen")
    if "receiver_seen" not in req_cols:
        cur.execute("ALTER TABLE match_requests ADD COLUMN receiver_seen INTEGER NOT NULL DEFAULT 0")
        req_cols.add("receiver_seen")
    if "updated_at" not in req_cols:
        cur.execute("ALTER TABLE match_requests ADD COLUMN updated_at TEXT")
        req_cols.add("updated_at")
    conn.commit()
    conn.close()


def _chat_match_to_dict(row):
    return {
        "match_id": row["match_id"],
        "name": row["name"],
        "avatar": row["avatar"],
        "location": row["location"] or "",
        "created_at": row["created_at"],
    }


def _chat_message_to_dict(row):
    return {
        "id": row["id"],
        "chat_id": row["chat_id"],
        "sender": row["sender"],
        "text": row["text"],
        "created_at": row["created_at"],
        "edited_at": row["edited_at"],
        "is_deleted": bool(row["is_deleted"]),
        "deleted_at": row["deleted_at"],
    }


def _get_forum_conn():
    conn = sqlite3.connect(FORUM_DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=3000;")
    return conn


def _init_forum_schema():
    conn = _get_forum_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id INTEGER,
            author TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL,
            likes INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            author_id INTEGER,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS post_likes (
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, post_id),
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()


def _forum_current_user_name():
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = db.session.get(User, user_id)
    return user.full_name if user else None


def _forum_list_posts(selected_category: str):
    conn = _get_forum_conn()
    if selected_category != "all":
        rows = conn.execute(
            """
            SELECT p.*, (SELECT COUNT(*) FROM comments WHERE post_id = p.id) AS comment_count
            FROM posts p
            WHERE p.category = ?
            ORDER BY p.id DESC
            """,
            (selected_category,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT p.*, (SELECT COUNT(*) FROM comments WHERE post_id = p.id) AS comment_count
            FROM posts p
            ORDER BY p.id DESC
            """
        ).fetchall()
    conn.close()
    return rows

# Create tables automatically for this prototype
with app.app_context():
    db.create_all()
    _init_chat_schema()
    _init_forum_schema()


PAGES = {
    "dashboard": "dashboard.html",
    "login": "login.html",
    "login-2fa": "login_2fa.html",
    "signup": "signup.html",
    "onboarding": "onboarding.html",
    "profile": "profile.html",
    "explore": "explore.html",
    "messages": "messages.html",
    "circle-confirmation": "circle_confirmation.html",
    "learning-circles": "learning_circles.html",
    "discover": "discover.html",
    "forum": "forum.html",
    "challenges": "challenges.html",
    "terms": "terms.html",
    "safety": "safety.html",
    "achievements": "achievements.html",
    "wellbeing": "wellbeing.html",
    "scrapbook": "scrapbook.html",
    "avatar": "avatar_builder.html",
    "admin-login": "admin_login.html",
    "admin-dashboard": "admin_dashboard.html",
}

AVATAR_DEFAULT_CONFIG = {
    "avatar_name": "",
    "pose": "waving",
    "gender": "girl",
    "skin_tone": "light",
    "base": "body_waving",
    "face": "face_light",
    "eyes": "eyes_1",
    "mouth": "mouth_1",
    "hair": "hair_1",
    "glasses": "none",
    "top": "top_1",
}

AVATAR_OPTIONS = {
    "avatar_name": [],
    "pose": ["waving", "standing", "smiling"],
    "gender": ["girl", "boy"],
    "skin_tone": ["light", "tan", "dark"],
    "base": ["body_waving", "body_standing", "body_smiling"],
    "face": ["face_light", "face_tan", "face_dark"],
    "eyes": ["eyes_1", "eyes_2"],
    "mouth": ["mouth_1", "mouth_2"],
    "hair": ["hair_1", "hair_2"],
    "glasses": ["none", "glasses_1"],
    "top": ["top_1", "top_2"],
}


LANDMARKS = [
    {
        "id": 1,
        "name": "Jurong",
        "icon": "ðŸ­",
        "x": 220,
        "y": 310,
        "story": "Singapore's industrial heartland that transformed into a hub for innovation, featuring Jurong Bird Park and the upcoming Jurong Lake District.",
        "question": "What is Jurong best known for today?",
        "options": ["Shopping malls", "Innovation hub", "Beach resorts", "Historic temples"],
        "answer": 1,
    },
    {
        "id": 2,
        "name": "Chinatown",
        "icon": "ðŸ®",
        "x": 410,
        "y": 350,
        "story": "A vibrant district preserving Chinese heritage and culture, where traditional shophouses blend with modern businesses.",
        "question": "What makes Chinatown special?",
        "options": ["Modern skyscrapers", "Blend of heritage and modern life", "Beach activities", "Industrial sites"],
        "answer": 1,
    },
    {
        "id": 3,
        "name": "Marina Bay",
        "icon": "ðŸ™",
        "x": 490,
        "y": 340,
        "story": "This iconic waterfront area features Marina Bay Sands with three towers connected by a sky park.",
        "question": "How many towers does Marina Bay Sands have?",
        "options": ["2", "3", "4", "5"],
        "answer": 1,
    },
    {
        "id": 4,
        "name": "Orchard Road",
        "icon": "ðŸ›",
        "x": 380,
        "y": 290,
        "story": "Singapore's premier shopping district with over 20 shopping malls. It was once lined with fruit orchards.",
        "question": "What was Orchard Road before becoming a shopping district?",
        "options": ["Industrial area", "Fruit orchards", "Residential zone", "Fishing village"],
        "answer": 1,
    },
    {
        "id": 5,
        "name": "Kampong Glam",
        "icon": "ðŸ•Œ",
        "x": 520,
        "y": 285,
        "story": "The historic Malay-Muslim quarter centered around the golden-domed Sultan Mosque.",
        "question": "What is the famous mosque in Kampong Glam?",
        "options": ["Blue Mosque", "Sultan Mosque", "Crystal Mosque", "Grand Mosque"],
        "answer": 1,
    },
    {
        "id": 6,
        "name": "Little India",
        "icon": "ðŸ›",
        "x": 460,
        "y": 270,
        "story": "An ethnic district that celebrates Indian culture, featuring colorful streets and vibrant festivals.",
        "question": "Which festival is famously celebrated in Little India?",
        "options": ["Christmas", "Deepavali", "Chinese New Year", "Hari Raya"],
        "answer": 1,
    },
    {
        "id": 7,
        "name": "Botanic Gardens",
        "icon": "ðŸª´",
        "x": 310,
        "y": 250,
        "story": "A UNESCO World Heritage Site founded in 1859, featuring 82 hectares of lush greenery.",
        "question": "When was the Singapore Botanic Gardens founded?",
        "options": ["1819", "1859", "1900", "1965"],
        "answer": 1,
    },
    {
        "id": 8,
        "name": "Marina Bay Sands",
        "icon": "ðŸ¢",
        "x": 550,
        "y": 325,
        "story": "Marina Bay Sands features three towers connected by a sky park 200 meters above ground.",
        "question": "How many towers does Marina Bay Sands have?",
        "options": ["2", "3", "4", "5"],
        "answer": 1,
    },
    {
        "id": 9,
        "name": "Changi",
        "icon": "âœˆï¸",
        "x": 620,
        "y": 285,
        "story": "Home to Changi Airport, consistently rated the world's best airport.",
        "question": "What is Changi best known for?",
        "options": ["Shopping malls", "World-class airport", "Historical museums", "Nature parks"],
        "answer": 1,
    },
    {
        "id": 10,
        "name": "Sentosa",
        "icon": "ðŸ",
        "x": 370,
        "y": 470,
        "story": "Singapore's island resort destination offering beaches and attractions.",
        "question": "What does 'Sentosa' mean in Malay?",
        "options": ["Peace and tranquility", "Beautiful island", "Paradise beach", "Golden sands"],
        "answer": 0,
    },
]

QUESTS = [
    {"id": 1, "title": "Join Your First Learning Circle", "description": "Connect with others to learn or share a skill together", "reward": 1500, "total": 1},
    {"id": 2, "title": "Reply in the Community Forum", "description": "Share your thoughts or help answer someone's question", "reward": 75, "total": 1},
    {"id": 3, "title": "Share a Skill", "description": "Teach something you know - cooking, language, crafts, anything!", "reward": 200, "total": 1},
    {"id": 4, "title": "Thank a Connection", "description": "Send appreciation to someone who helped you", "reward": 50, "total": 1},
    {"id": 5, "title": "Complete 3 Learning Sessions", "description": "Keep learning and growing with the community", "reward": 300, "total": 3},
]

REWARDS = [
    {"id": 1, "name": "$2 GrabFood Voucher", "icon": "ðŸŽ", "cost": 500},
    {"id": 2, "name": "$3 Starbucks Voucher", "icon": "â˜•", "cost": 750},
    {"id": 3, "name": "$5 Popular Bookstore", "icon": "ðŸ“š", "cost": 1250},
    {"id": 4, "name": "$5 Kopitiam Voucher", "icon": "ðŸ¥–", "cost": 1250},
    {"id": 5, "name": "$10 NTUC Voucher", "icon": "ðŸ›’", "cost": 2500},
    {"id": 6, "name": "$10 Watsons Voucher", "icon": "ðŸ§´", "cost": 2500},
    {"id": 7, "name": "$15 Movie Voucher", "icon": "ðŸŽŸ", "cost": 3750},
    {"id": 8, "name": "$15 Uniqlo Voucher", "icon": "ðŸ‘•", "cost": 3750},
]

BADGE_GROUPS = {
    "Journey Badges": [
        {"id": 1, "name": "First Steps", "icon": "ðŸ¥‡", "description": "Unlock your first landmark", "threshold": 1, "requirement": "landmarks"},
        {"id": 2, "name": "City Explorer", "icon": "ðŸ§­", "description": "Complete 3 landmarks", "threshold": 3, "requirement": "landmarks"},
        {"id": 3, "name": "Island Voyager", "icon": "ðŸ—º", "description": "Complete all 10 landmarks", "threshold": 10, "requirement": "landmarks"},
    ],
    "Community Badges": [
        {"id": 4, "name": "Community Builder", "icon": "ðŸ§±", "description": "Complete 5 quests", "threshold": 5, "requirement": "quests"},
        {"id": 5, "name": "Helpful Guide", "icon": "ðŸ§‘â€ðŸ«", "description": "Complete 10 quests", "threshold": 10, "requirement": "quests"},
        {"id": 6, "name": "Master Connector", "icon": "ðŸ”—", "description": "Complete 20 quests", "threshold": 20, "requirement": "quests"},
    ],
    "Progress Badges": [
        {"id": 7, "name": "Point Collector", "icon": "ðŸª™", "description": "Earn 1,000 points", "threshold": 1000, "requirement": "points"},
        {"id": 8, "name": "Point Master", "icon": "ðŸ†", "description": "Earn 5,000 points", "threshold": 5000, "requirement": "points"},
        {"id": 9, "name": "Tier Ascender", "icon": "ðŸš€", "description": "Reach Tier 3", "threshold": 3, "requirement": "tier"},
    ],
}

SKILLS = [
    {"id": 1, "name": "WhatsApp Basics", "description": "Start a new chat and send a message.", "category": "Digital Basics", "icon": "whatsapp", "required_count": 1, "progress": 1, "completed": True, "parent_id": None},
    {"id": 2, "name": "Voice Notes", "description": "Record and send a voice message.", "category": "Digital Basics", "icon": "voice", "required_count": 2, "progress": 1, "completed": False, "parent_id": 1},
    {"id": 3, "name": "Photo Sharing", "description": "Share photos with a connection.", "category": "Digital Basics", "icon": "attachment", "required_count": 2, "progress": 0, "completed": False, "parent_id": 1},
    {"id": 4, "name": "Online Safety", "description": "Identify suspicious links and scams.", "category": "Safety & Security", "icon": "scam", "required_count": 3, "progress": 1, "completed": False, "parent_id": None},
]


def _default_achievements(user: User) -> dict:
    checkins = []

    landmarks = []
    for lm in LANDMARKS:
        landmarks.append({**lm, "unlocked": False, "completed": False})

    quests = []
    for q in QUESTS:
        quests.append({**q, "progress": 0, "completed": False})

    rewards = []
    for r in REWARDS:
        rewards.append({**r, "status": "locked"})

    return {
        "user": {
            "id": user.id,
            "username": user.full_name,
            "total_points": 0,
            "available_points": 0,
            "active_days": 0,
            "current_tier": 1,
            "current_streak": 0,
        },
        "landmarks": landmarks,
        "quests": quests,
        "rewards": rewards,
        "badges": {},
        "leaderboard": [
            {"username": "Auntie Mary", "total_points": 4200, "current_tier": 3},
            {"username": "Uncle Tan", "total_points": 3800, "current_tier": 3},
            {"username": user.full_name, "total_points": 1850, "current_tier": 2},
            {"username": "Mdm Chen", "total_points": 1650, "current_tier": 2},
            {"username": "Sam", "total_points": 1200, "current_tier": 1},
        ],
        "checkins": checkins,
        "skills": SKILLS,
    }


def _recompute_badges(state: dict) -> None:
    quests_completed = len([q for q in state["quests"] if q.get("completed")])
    landmarks_completed = len([l for l in state["landmarks"] if l.get("completed")])
    points = state["user"]["total_points"]
    tier = state["user"]["current_tier"]

    grouped = {}
    for group, badges in BADGE_GROUPS.items():
        grouped[group] = []
        for badge in badges:
            requirement = badge["requirement"]
            current = 0
            if requirement == "landmarks":
                current = landmarks_completed
            elif requirement == "quests":
                current = quests_completed
            elif requirement == "points":
                current = points
            elif requirement == "tier":
                current = tier
            grouped[group].append(
                {
                    "id": badge["id"],
                    "name": badge["name"],
                    "icon": badge["icon"],
                    "description": badge["description"],
                    "threshold": badge["threshold"],
                    "earned": current >= badge["threshold"],
                    "current": current,
                }
            )
    state["badges"] = grouped


def _sync_rewards(state: dict) -> None:
    available = state["user"]["available_points"]
    for reward in state["rewards"]:
        if reward.get("status") == "redeemed":
            continue
        reward["status"] = "available" if available >= reward["cost"] else "locked"


def _refresh_leaderboard(state: dict, user: User) -> None:
    base = [
        {"username": "Auntie Mary", "total_points": 4200, "current_tier": 3},
        {"username": "Uncle Tan", "total_points": 3800, "current_tier": 3},
        {"username": "Mdm Chen", "total_points": 1650, "current_tier": 2},
        {"username": "Sam", "total_points": 1200, "current_tier": 1},
    ]
    me = {
        "username": user.full_name,
        "total_points": state["user"]["total_points"],
        "current_tier": state["user"]["current_tier"],
    }
    combined = base + [me]
    combined.sort(key=lambda r: r["total_points"], reverse=True)
    state["leaderboard"] = combined[:10]


def _load_achievements(user_id: int) -> dict:
    row = AchievementState.query.filter_by(user_id=user_id).first()
    if not row:
        user = db.session.get(User, user_id)
        data = _default_achievements(user)
        _recompute_badges(data)
        _refresh_leaderboard(data, user)
        row = AchievementState(user_id=user_id, data_json=json.dumps(data))
        db.session.add(row)
        db.session.commit()
        return data
    data = json.loads(row.data_json)
    user = db.session.get(User, user_id)
    if user:
        _refresh_leaderboard(data, user)
    return data


def _save_achievements(user_id: int, state: dict) -> None:
    row = AchievementState.query.filter_by(user_id=user_id).first()
    if not row:
        row = AchievementState(user_id=user_id, data_json=json.dumps(state))
        db.session.add(row)
    else:
        row.data_json = json.dumps(state)
        row.updated_at = datetime.utcnow()
    db.session.commit()



@app.get("/")
def home():
    explore_cards = _list_home_explore_cards()
    return render_template("index.html", explore_cards=explore_cards)



@app.get("/admin-login")
def admin_login_page():
    return render_template("admin_login.html")


@app.get("/admin-dashboard")
def admin_dashboard_page():
    if not _require_admin():
        return redirect("/admin-login")
    return render_template("admin_dashboard.html")


@app.get("/logout")
def logout_page():
    session.pop("user_id", None)
    session.pop("is_admin", None)
    session.pop("admin_id", None)
    return redirect("/login")


@app.post("/dashboard")
def dashboard_forum_post():
    user_id = _require_login()
    if not user_id:
        return redirect("/login")

    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()
    category = (request.form.get("category") or "").strip()

    if not title or not content or not category:
        return redirect("/dashboard#tab-wisdom-forum")

    user = db.session.get(User, user_id)
    author_name = user.full_name if user else "User"

    conn = _get_forum_conn()
    conn.execute(
        "INSERT INTO posts (author_id, author, title, content, category, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, author_name, title, content, category, datetime.utcnow().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()
    _log_audit("wisdom_forum", "post", user_id, {"title": title, "category": category})
    _increment_quest_progress(user_id, 2)
    _add_notification(user_id, "forum_post", "Posted in the Wisdom Forum.", {"title": title})

    return redirect("/dashboard#tab-wisdom-forum")


@app.route("/forum/posts/<int:post_id>", methods=["GET", "POST"])
def forum_post_detail(post_id: int):
    user_id = _require_login()
    if not user_id:
        return redirect("/login")

    user = db.session.get(User, user_id)
    forum_user_name = user.full_name if user else "User"

    conn = _get_forum_conn()
    if request.method == "POST":
        comment = (request.form.get("comment") or "").strip()
        if comment:
            conn.execute(
                "INSERT INTO comments (post_id, author_id, author, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (post_id, user_id, forum_user_name, comment, datetime.utcnow().strftime("%Y-%m-%d %H:%M")),
            )
            conn.commit()
            _log_audit("wisdom_forum", "comment", user_id, {"post_id": post_id})
            _increment_quest_progress(user_id, 2)
            _add_notification(user_id, "forum_comment", "Replied in the Wisdom Forum.", {"post_id": post_id})

    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        return ("Not found", 404)

    comments = conn.execute(
        "SELECT * FROM comments WHERE post_id = ? ORDER BY id DESC",
        (post_id,),
    ).fetchall()
    conn.close()

    return render_template("post.html", post=post, comments=comments, is_admin=_require_admin(), forum_user_name=forum_user_name)


@app.post("/forum/posts/<int:post_id>/comments/<int:comment_id>/delete")
def forum_delete_comment(post_id: int, comment_id: int):
    user_id = _require_login()
    if not user_id:
        return redirect("/login")

    forum_user_name = _forum_current_user_name()
    conn = _get_forum_conn()
    comment = conn.execute(
        "SELECT author_id, author FROM comments WHERE id = ? AND post_id = ?",
        (comment_id, post_id),
    ).fetchone()

    if comment and (_require_admin() or comment["author_id"] == user_id or comment["author"] == (forum_user_name or "")):
        conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        conn.commit()
        _log_audit("wisdom_forum", "comment_delete", user_id, {"post_id": post_id})

    conn.close()
    return redirect(f"/forum/posts/{post_id}")


@app.post("/forum/posts/<int:post_id>/delete")
def forum_delete_post(post_id: int):
    user_id = _require_login()
    if not user_id:
        return redirect("/login")

    forum_user_name = _forum_current_user_name()
    conn = _get_forum_conn()
    post = conn.execute("SELECT author_id, author FROM posts WHERE id = ?", (post_id,)).fetchone()

    if post and (_require_admin() or post["author_id"] == user_id or post["author"] == (forum_user_name or "")):
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        _log_audit("wisdom_forum", "post_delete", user_id, {"post_id": post_id})

    conn.close()
    return redirect("/dashboard#tab-wisdom-forum")


@app.post("/forum/posts/<int:post_id>/edit")
def forum_edit_post(post_id: int):
    user_id = _require_login()
    if not user_id:
        return redirect("/login")

    forum_user_name = _forum_current_user_name()
    content = (request.form.get("content") or "").strip()
    if not content:
        return redirect("/dashboard#tab-wisdom-forum")

    conn = _get_forum_conn()
    post = conn.execute("SELECT author_id, author FROM posts WHERE id = ?", (post_id,)).fetchone()

    if post and (post["author_id"] == user_id or post["author"] == (forum_user_name or "")):
        conn.execute("UPDATE posts SET content = ? WHERE id = ?", (content, post_id))
        conn.commit()
        _log_audit("wisdom_forum", "post_edit", user_id, {"post_id": post_id})

    conn.close()
    return redirect("/dashboard#tab-wisdom-forum")


@app.post("/forum/posts/<int:post_id>/like")
def forum_like_post(post_id: int):
    user_id = _require_login()
    if not user_id:
        return redirect("/login")

    conn = _get_forum_conn()
    existing = conn.execute(
        "SELECT 1 FROM post_likes WHERE user_id = ? AND post_id = ?",
        (user_id, post_id),
    ).fetchone()

    if existing:
        conn.execute("DELETE FROM post_likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        conn.execute("UPDATE posts SET likes = CASE WHEN likes > 0 THEN likes - 1 ELSE 0 END WHERE id = ?", (post_id,))
        _log_audit("wisdom_forum", "like_remove", user_id, {"post_id": post_id})
    else:
        conn.execute("INSERT INTO post_likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        conn.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
        _log_audit("wisdom_forum", "like_add", user_id, {"post_id": post_id})

    conn.commit()
    conn.close()
    return redirect("/dashboard#tab-wisdom-forum")


@app.get("/api/forum/posts")
def api_forum_posts():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    category = (request.args.get("category") or "all").strip()
    conn = _get_forum_conn()
    if category and category.lower() != "all":
        rows = conn.execute(
            """
            SELECT p.*, (SELECT COUNT(*) FROM comments WHERE post_id = p.id) AS comment_count
            FROM posts p
            WHERE LOWER(p.category) = ?
            ORDER BY p.id DESC
            """,
            (category.lower(),),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT p.*, (SELECT COUNT(*) FROM comments WHERE post_id = p.id) AS comment_count
            FROM posts p
            ORDER BY p.id DESC
            """
        ).fetchall()
    conn.close()
    current_name = _forum_current_user_name() or ""
    is_admin = _require_admin()
    posts = []
    for r in rows:
        posts.append(
            {
                "id": r["id"],
                "author": r["author"],
                "title": r["title"],
                "content": r["content"],
                "category": r["category"],
                "likes": r["likes"],
                "comment_count": r["comment_count"],
                "created_at": r["created_at"],
                "can_edit": bool(is_admin or r["author_id"] == user_id or r["author"] == current_name),
            }
        )
    return jsonify({"ok": True, "posts": posts})


@app.post("/api/forum/posts")
def api_forum_create_post():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    category = (data.get("category") or "all").strip()
    if not title or not content:
        return jsonify({"ok": False, "error": "Title and content are required"}), 400

    user = db.session.get(User, user_id)
    author = user.full_name if user else "User"

    conn = _get_forum_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO posts (author_id, author, title, content, category, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, author, title, content, category, datetime.utcnow().strftime("%Y-%m-%d %H:%M")),
    )
    post_id = cur.lastrowid
    conn.commit()
    row = conn.execute(
        "SELECT p.*, (SELECT COUNT(*) FROM comments WHERE post_id = p.id) AS comment_count FROM posts p WHERE p.id = ?",
        (post_id,),
    ).fetchone()
    conn.close()
    _log_audit("wisdom_forum", "post", user_id, {"title": title, "category": category})
    return jsonify(
        {
            "ok": True,
            "post": {
                "id": row["id"],
                "author": row["author"],
                "title": row["title"],
                "content": row["content"],
                "category": row["category"],
                "likes": row["likes"],
                "comment_count": row["comment_count"],
                "created_at": row["created_at"],
                "can_edit": True,
            },
        }
    )


@app.post("/api/forum/posts/<int:post_id>/like")
def api_forum_like(post_id: int):
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    conn = _get_forum_conn()
    existing = conn.execute(
        "SELECT 1 FROM post_likes WHERE user_id = ? AND post_id = ?",
        (user_id, post_id),
    ).fetchone()
    liked = False
    if existing:
        conn.execute("DELETE FROM post_likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        conn.execute("UPDATE posts SET likes = CASE WHEN likes > 0 THEN likes - 1 ELSE 0 END WHERE id = ?", (post_id,))
        _log_audit("wisdom_forum", "like_remove", user_id, {"post_id": post_id})
        liked = False
    else:
        conn.execute("INSERT INTO post_likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        conn.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
        _log_audit("wisdom_forum", "like_add", user_id, {"post_id": post_id})
        liked = True
    conn.commit()
    likes = conn.execute("SELECT likes FROM posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()
    return jsonify({"ok": True, "likes": likes["likes"] if likes else 0, "liked": liked})


@app.put("/api/forum/posts/<int:post_id>")
def api_forum_edit(post_id: int):
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"ok": False, "error": "Content is required"}), 400

    conn = _get_forum_conn()
    post = conn.execute("SELECT author_id, author FROM posts WHERE id = ?", (post_id,)).fetchone()
    forum_user_name = _forum_current_user_name()
    if not post or not (_require_admin() or post["author_id"] == user_id or post["author"] == (forum_user_name or "")):
        conn.close()
        return jsonify({"ok": False, "error": "Not authorised"}), 403
    conn.execute("UPDATE posts SET content = ? WHERE id = ?", (content, post_id))
    conn.commit()
    conn.close()
    _log_audit("wisdom_forum", "post_edit", user_id, {"post_id": post_id})
    return jsonify({"ok": True})


@app.delete("/api/forum/posts/<int:post_id>")
def api_forum_delete(post_id: int):
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    conn = _get_forum_conn()
    post = conn.execute("SELECT author_id, author FROM posts WHERE id = ?", (post_id,)).fetchone()
    forum_user_name = _forum_current_user_name()
    if not post or not (_require_admin() or post["author_id"] == user_id or post["author"] == (forum_user_name or "")):
        conn.close()
        return jsonify({"ok": False, "error": "Not authorised"}), 403
    conn.execute("DELETE FROM post_likes WHERE post_id = ?", (post_id,))
    conn.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    _log_audit("wisdom_forum", "post_delete", user_id, {"post_id": post_id})
    return jsonify({"ok": True})


@app.get("/api/session")
def api_session():
    user_id = _require_login()
    if not user_id:
        return jsonify({"logged_in": False})

    user = db.session.get(User, user_id)
    name = user.full_name if user else "User"
    role = (user.member_type or "youth") if user else "youth"
    settings = _get_user_settings_map(user_id)
    avatar_url = settings.get("avatar_url", "")
    return jsonify({
        "logged_in": True,
        "name": name,
        "role": role,
        "is_admin": bool(session.get("is_admin")),
        "avatar_url": avatar_url,
    })


def _coach_interests(user_id: int) -> list:
    settings = _get_user_settings_map(user_id)
    onboarding = _safe_json(settings.get("onboarding", "{}"), {})
    return onboarding.get("interests") or []


def _coach_pick_items(keys: list, field: str, limit: int = 4) -> list:
    out = []
    for key in keys:
        items = COACH_LIBRARY.get(key, {}).get(field, [])
        for item in items:
            if item not in out:
                out.append(item)
            if len(out) >= limit:
                return out
    return out


def _coach_topic_keys(interests: list, mood: str, stage: str) -> list:
    keys = ["general"]
    interest_text = " ".join(interests or []).lower()
    if any(k in interest_text for k in ["food", "hawker", "cooking"]):
        keys.append("hawker")
    if any(k in interest_text for k in ["family", "grand", "parent"]):
        keys.append("family")
    if any(k in interest_text for k in ["childhood", "school", "memories"]):
        keys.append("childhood")
    if any(k in interest_text for k in ["tech", "phone", "digital", "computer"]):
        keys.append("tech")
    if any(k in interest_text for k in ["hobby", "music", "art", "gardening", "exercise"]):
        keys.append("hobbies")
    if any(k in interest_text for k in ["singapore", "travel", "places"]):
        keys.append("singapore")
    if mood == "lonely":
        keys.insert(0, "support")
    if stage == "meetup":
        keys.append("meetup")
    return keys


def _coach_rewrite(text: str) -> str:
    if not text:
        return ""
    out = text
    for word, repl in COACH_REWRITE_MAP.items():
        out = re.sub(rf"\\b{re.escape(word)}\\b", repl, out, flags=re.IGNORECASE)
    out = re.sub(r"\\s{2,}", " ", out).strip()
    return out


@app.get("/api/coach")
def api_coach_suggestions():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    stage = (request.args.get("stage") or "first").strip().lower()
    mood = (request.args.get("mood") or "").strip().lower()
    interests = _coach_interests(user_id)
    keys = _coach_topic_keys(interests, mood, stage)
    icebreakers = _coach_pick_items(keys, "icebreakers", limit=4)
    questions = _coach_pick_items(keys, "questions", limit=4)
    respectful = _coach_pick_items(keys, "respectful", limit=3)
    return jsonify({
        "ok": True,
        "icebreakers": icebreakers,
        "questions": questions,
        "respectful": respectful,
    })


@app.post("/api/coach/rewrite")
def api_coach_rewrite():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    rewritten = _coach_rewrite(text)
    return jsonify({"ok": True, "text": rewritten})


@app.get("/api/matching/profiles")
def api_matching_profiles():
    user_id = _require_login()
    if not user_id:
        return jsonify({"profiles": []})

    viewer_settings = _get_user_settings_map(user_id)
    viewer_onboarding = _safe_json(viewer_settings.get("onboarding", "{}"), {})
    viewer_interests = viewer_onboarding.get("interests") or []

    users = User.query.filter(User.id != user_id).order_by(User.created_at.desc()).all()
    profiles = []
    for u in users:
        settings_map = _get_user_settings_map(u.id)
        profiles.append(_build_match_profile(u, settings_map, viewer_interests))

    return jsonify({"profiles": profiles})


@app.post("/api/match_requests")
def api_create_match_request():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    receiver_raw = data.get("receiver_id")
    try:
        receiver_id = int(receiver_raw)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "receiver_id is required"}), 400

    if receiver_id == user_id:
        return jsonify({"ok": False, "error": "Cannot request yourself"}), 400

    receiver = db.session.get(User, receiver_id)
    if not receiver:
        return jsonify({"ok": False, "error": "User not found"}), 404

    conn = _get_chat_conn()
    existing = conn.execute(
        """SELECT id, status FROM match_requests
           WHERE sender_id = ? AND receiver_id = ?
           ORDER BY id DESC LIMIT 1""",
        (user_id, receiver_id),
    ).fetchone()
    if existing and existing["status"] == "pending":
        conn.close()
        return jsonify({"ok": True, "status": "pending", "request_id": existing["id"]}), 200
    if existing and existing["status"] == "accepted":
        conn.close()
        return jsonify({"ok": True, "status": "accepted", "request_id": existing["id"]}), 200

    now = _utc_now_iso()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO match_requests (sender_id, receiver_id, status, created_at, updated_at, sender_seen, receiver_seen)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, receiver_id, "pending", now, None, 1, 0),
    )
    conn.commit()
    request_id = cur.lastrowid
    conn.close()
    return jsonify({"ok": True, "status": "pending", "request_id": request_id}), 201


@app.get("/api/match_requests/incoming")
def api_list_incoming_match_requests():
    user_id = _require_login()
    if not user_id:
        return jsonify({"requests": []})

    conn = _get_chat_conn()
    rows = conn.execute(
        """SELECT id, sender_id, status, created_at FROM match_requests
           WHERE receiver_id = ? AND status = 'pending'
           ORDER BY created_at DESC""",
        (user_id,),
    ).fetchall()
    conn.close()

    output = []
    for row in rows:
        sender = db.session.get(User, row["sender_id"])
        if not sender:
            continue
        meta = _match_card_for_user(sender)
        output.append(
            {
                "id": row["id"],
                "sender_id": sender.id,
                "sender_name": meta["name"],
                "sender_avatar": meta["avatar"],
                "sender_location": meta["location"],
                "created_at": row["created_at"],
            }
        )
    return jsonify({"requests": output})


@app.post("/api/match_requests/<int:request_id>/respond")
def api_respond_match_request(request_id: int):
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").strip().lower()
    if action not in {"accept", "decline"}:
        return jsonify({"ok": False, "error": "action must be accept or decline"}), 400

    conn = _get_chat_conn()
    req = conn.execute(
        "SELECT id, sender_id, receiver_id, status FROM match_requests WHERE id = ?",
        (request_id,),
    ).fetchone()
    if not req or req["receiver_id"] != user_id:
        conn.close()
        return jsonify({"ok": False, "error": "Request not found"}), 404
    if req["status"] != "pending":
        conn.close()
        return jsonify({"ok": True, "status": req["status"]}), 200

    next_status = "accepted" if action == "accept" else "declined"
    conn.execute(
        """UPDATE match_requests
           SET status = ?, updated_at = ?, receiver_seen = 1, sender_seen = 0
           WHERE id = ?""",
        (next_status, _utc_now_iso(), request_id),
    )

    if next_status == "accepted":
        sender = db.session.get(User, req["sender_id"])
        receiver = db.session.get(User, req["receiver_id"])
        if sender and receiver:
            _ensure_match_row(conn, sender.id, receiver)
            _ensure_match_row(conn, receiver.id, sender)
            _increment_quest_progress(user_id, 4)
            _add_notification(
                req["sender_id"],
                "match_accept",
                f"{receiver.full_name} accepted your match request.",
                {"request_id": request_id},
            )
            _add_notification(
                req["receiver_id"],
                "match_accept",
                f"You connected with {sender.full_name}.",
                {"request_id": request_id},
            )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "status": next_status})


@app.get("/api/notifications")
def api_notifications():
    user_id = _require_login()
    if not user_id:
        return jsonify({"notifications": [], "unread_count": 0})

    conn = _get_chat_conn()
    pending = conn.execute(
        """SELECT id, sender_id, created_at, receiver_seen
           FROM match_requests
           WHERE receiver_id = ? AND status = 'pending'
           ORDER BY created_at DESC""",
        (user_id,),
    ).fetchall()
    decisions = conn.execute(
        """SELECT id, receiver_id, status, COALESCE(updated_at, created_at) AS ts
           FROM match_requests
           WHERE sender_id = ? AND status IN ('accepted', 'declined') AND sender_seen = 0
           ORDER BY ts DESC""",
        (user_id,),
    ).fetchall()
    conn.close()

    notifications = []
    unread_count = 0

    for row in pending:
        sender = db.session.get(User, row["sender_id"])
        if not sender:
            continue
        meta = _match_card_for_user(sender)
        is_unread = row["receiver_seen"] == 0
        if is_unread:
            unread_count += 1
        notifications.append(
            {
                "id": f"req-{row['id']}",
                "type": "match_request",
                "request_id": row["id"],
                "sender_id": sender.id,
                "sender_name": meta["name"],
                "sender_avatar": meta["avatar"],
                "sender_location": meta["location"],
                "created_at": row["created_at"],
                "unread": is_unread,
            }
        )

    for row in decisions:
        receiver = db.session.get(User, row["receiver_id"])
        if not receiver:
            continue
        meta = _match_card_for_user(receiver)
        notifications.append(
            {
                "id": f"dec-{row['id']}",
                "type": "match_decision",
                "request_id": row["id"],
                "status": row["status"],
                "receiver_id": receiver.id,
                "receiver_name": meta["name"],
                "receiver_avatar": meta["avatar"],
                "created_at": row["ts"],
                "unread": True,
            }
        )
        unread_count += 1

    conn = _get_main_conn()
    extra_rows = conn.execute(
        """SELECT id, user_id, type, message, meta_json, is_read, created_at
           FROM notifications
           WHERE user_id = ? OR user_id IS NULL
           ORDER BY created_at DESC
           LIMIT 50""",
        (user_id,),
    ).fetchall()
    conn.close()
    for row in extra_rows:
        is_global = row["user_id"] is None
        is_unread = (row["is_read"] == 0) and not is_global and row["user_id"] == user_id
        if is_unread:
            unread_count += 1
        notifications.append(
            {
                "id": f"sys-{row['id']}",
                "type": row["type"] or "system",
                "message": row["message"],
                "created_at": row["created_at"],
                "unread": is_unread,
            }
        )

    notifications.sort(key=lambda n: n.get("created_at") or "", reverse=True)
    return jsonify({"notifications": notifications, "unread_count": unread_count})


@app.post("/api/notifications/mark_read")
def api_notifications_mark_read():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    conn = _get_chat_conn()
    conn.execute(
        "UPDATE match_requests SET receiver_seen = 1 WHERE receiver_id = ? AND status = 'pending'",
        (user_id,),
    )
    conn.execute(
        "UPDATE match_requests SET sender_seen = 1 WHERE sender_id = ? AND status IN ('accepted', 'declined')",
        (user_id,),
    )
    conn.commit()
    conn.close()
    conn = _get_main_conn()
    conn.execute(
        "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
        (user_id,),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.get("/api/avatar")
def api_avatar_proxy():
    params = request.args.to_dict(flat=True)
    qs = urllib.parse.urlencode(params)
    remote_url = f"https://api.dicebear.com/6.x/avataaars/svg?{qs}"
    try:
        with urllib.request.urlopen(remote_url, timeout=5) as resp:
            data = resp.read()
        return Response(data, mimetype="image/svg+xml")
    except Exception:
        return Response("", status=502)


@app.get("/api/avatar/options")
def api_avatar_options():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    return jsonify({"ok": True, "options": AVATAR_OPTIONS, "default": AVATAR_DEFAULT_CONFIG})


@app.get("/api/avatar/me")
def api_avatar_me():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    conn = _get_main_conn()
    row = conn.execute(
        "SELECT config_json FROM user_avatar WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"ok": True, "config": AVATAR_DEFAULT_CONFIG, "source": "default"})

    try:
        loaded = json.loads(row["config_json"] or "{}")
        if not isinstance(loaded, dict):
            loaded = {}
    except Exception:
        loaded = {}
    merged = {**AVATAR_DEFAULT_CONFIG, **loaded}
    return jsonify({"ok": True, "config": merged, "source": "db"})


@app.post("/api/avatar/me")
def api_avatar_me_save():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    config = data.get("config")
    if not isinstance(config, dict):
        return jsonify({"ok": False, "error": "config must be an object"}), 400

    cleaned = {}
    for key, allowed in AVATAR_OPTIONS.items():
        if key == "avatar_name":
            name_value = str(config.get("avatar_name", AVATAR_DEFAULT_CONFIG["avatar_name"]) or "").strip()
            cleaned["avatar_name"] = name_value[:40]
            continue
        selected = config.get(key, AVATAR_DEFAULT_CONFIG[key])
        if selected not in allowed:
            selected = AVATAR_DEFAULT_CONFIG[key]
        cleaned[key] = selected

    conn = _get_main_conn()
    conn.execute(
        """
        INSERT INTO user_avatar (user_id, config_json, updated_at, snapshot_path)
        VALUES (?, ?, ?, NULL)
        ON CONFLICT(user_id) DO UPDATE SET
            config_json = excluded.config_json,
            updated_at = excluded.updated_at
        """,
        (user_id, json.dumps(cleaned), _utc_now_iso()),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "config": cleaned})


@app.get("/api/admin/chat/messages")
def api_admin_chat_messages():
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 403
    conn = _get_chat_conn()
    rows = conn.execute(
        "SELECT id, sender, text, created_at FROM admin_messages ORDER BY id ASC"
    ).fetchall()
    conn.close()
    return jsonify([{
        "id": r["id"],
        "sender": r["sender"],
        "text": r["text"],
        "created_at": r["created_at"],
    } for r in rows])


@app.post("/api/admin/chat/messages")
def api_admin_chat_send():
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 403
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "Message is required"}), 400
    sender = session.get("admin_id") or "admin"
    conn = _get_chat_conn()
    conn.execute(
        "INSERT INTO admin_messages (sender, text, created_at) VALUES (?, ?, ?)",
        (sender, text, _utc_now_iso()),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id, sender, text, created_at FROM admin_messages WHERE id = last_insert_rowid()"
    ).fetchone()
    conn.close()
    return jsonify({
        "id": row["id"],
        "sender": row["sender"],
        "text": row["text"],
        "created_at": row["created_at"],
    }), 201


@app.get("/api/circle/chat/messages")
def api_circle_chat_messages():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    title = (request.args.get("title") or "").strip()
    if not title:
        return jsonify({"ok": False, "error": "title is required"}), 400
    conn = _get_chat_conn()
    rows = conn.execute(
        "SELECT id, circle_title, sender, text, created_at FROM circle_messages WHERE circle_title = ? ORDER BY id ASC",
        (title,),
    ).fetchall()
    conn.close()
    return jsonify([{
        "id": r["id"],
        "circle_title": r["circle_title"],
        "sender": r["sender"],
        "text": r["text"],
        "created_at": r["created_at"],
    } for r in rows])


@app.post("/api/circle/chat/messages")
def api_circle_chat_send():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    text = (data.get("text") or "").strip()
    if not title or not text:
        return jsonify({"ok": False, "error": "title and text are required"}), 400

    user = db.session.get(User, user_id)
    sender_name = user.full_name if user else "User"

    conn = _get_chat_conn()
    conn.execute(
        "INSERT INTO circle_messages (circle_title, sender, text, created_at) VALUES (?, ?, ?, ?)",
        (title, sender_name, text, _utc_now_iso()),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id, circle_title, sender, text, created_at FROM circle_messages WHERE id = last_insert_rowid()",
    ).fetchone()
    conn.close()
    return jsonify({
        "id": row["id"],
        "circle_title": row["circle_title"],
        "sender": row["sender"],
        "text": row["text"],
        "created_at": row["created_at"],
    }), 201


@app.get("/api/matches")
def api_list_matches():
    user_id = _require_login()
    if not user_id:
        return jsonify([]), 200
    conn = _get_chat_conn()
    rows = conn.execute(
        "SELECT match_id, name, avatar, location, created_at FROM matches WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return jsonify([_chat_match_to_dict(r) for r in rows])


@app.post("/api/matches")
def api_create_match():
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    match_id = (data.get("match_id") or "").strip()
    if match_id:
        prefix = f"{user_id}:"
        match_key = match_id if match_id.startswith(prefix) else f"{prefix}{match_id}"
    else:
        match_key = ""
    name = (data.get("name") or "").strip()
    avatar = (data.get("avatar") or "").strip()
    location = (data.get("location") or "").strip()

    if not match_id or not name or not avatar:
        return jsonify({"error": "match_id, name, avatar are required"}), 400

    conn = _get_chat_conn()
    existing = conn.execute(
        "SELECT match_id, name, avatar, location, created_at FROM matches WHERE match_id = ? AND user_id = ?",
        (match_key, user_id),
    ).fetchone()
    if existing:
        conn.close()
        return jsonify(_chat_match_to_dict(existing)), 200

    conn.execute(
        "INSERT INTO matches (user_id, match_id, name, avatar, location, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, match_key, name, avatar, location or None, _utc_now_iso()),
    )
    conn.commit()
    row = conn.execute(
        "SELECT match_id, name, avatar, location, created_at FROM matches WHERE match_id = ? AND user_id = ?",
        (match_key, user_id),
    ).fetchone()
    conn.close()
    _log_audit("matches", "create", user_id, {"match_id": match_id})
    return jsonify(_chat_match_to_dict(row)), 201


@app.delete("/api/matches")
def api_clear_matches():
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    conn = _get_chat_conn()
    conn.execute("DELETE FROM messages WHERE chat_id IN (SELECT match_id FROM matches WHERE user_id = ?)", (user_id,))
    conn.execute("DELETE FROM matches WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    _log_audit("safety", "report", user_id, {"reason": reason})
    return jsonify({"ok": True})


@app.delete("/api/matches/<match_id>")
def api_delete_match(match_id):
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    conn = _get_chat_conn()
    existing = conn.execute(
        "SELECT match_id FROM matches WHERE match_id = ? AND user_id = ?",
        (match_id, user_id),
    ).fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": "match not found"}), 404

    conn.execute("DELETE FROM messages WHERE chat_id = ?", (match_id,))
    conn.execute("DELETE FROM matches WHERE match_id = ? AND user_id = ?", (match_id, user_id))
    conn.commit()
    conn.close()
    _log_audit("matches", "clear", user_id)
    return jsonify({"ok": True})


@app.get("/api/messages/<chat_id>")
def api_list_messages(chat_id):
    conn = _get_chat_conn()
    rows = conn.execute(
        "SELECT id, chat_id, sender, text, created_at, edited_at, is_deleted, deleted_at FROM messages WHERE chat_id = ? ORDER BY created_at ASC",
        (chat_id,),
    ).fetchall()
    conn.close()
    return jsonify([_chat_message_to_dict(r) for r in rows])


@app.post("/api/messages/<chat_id>")
def api_create_message(chat_id):
    data = request.get_json(silent=True) or {}
    sender = (data.get("sender") or "youth").strip().lower()
    text = (data.get("text") or "").strip()

    if sender not in ("youth", "elderly"):
        return jsonify({"error": "sender must be 'youth' or 'elderly'"}), 400
    if not text:
        return jsonify({"error": "text is required"}), 400

    conn = _get_chat_conn()
    conn.execute(
        "INSERT INTO messages (chat_id, sender, text, created_at) VALUES (?, ?, ?, ?)",
        (chat_id, sender, text, _utc_now_iso()),
    )
    conn.commit()
    msg = conn.execute(
        "SELECT id, chat_id, sender, text, created_at, edited_at, is_deleted, deleted_at FROM messages WHERE id = last_insert_rowid()",
    ).fetchone()
    conn.close()
    return jsonify(_chat_message_to_dict(msg)), 201


@app.put("/api/messages/<int:message_id>")
def api_update_message(message_id):
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400

    conn = _get_chat_conn()
    msg = conn.execute(
        "SELECT id, chat_id, sender, text, created_at, edited_at, is_deleted, deleted_at FROM messages WHERE id = ?",
        (message_id,),
    ).fetchone()
    if not msg:
        conn.close()
        return jsonify({"error": "message not found"}), 404
    if msg["is_deleted"]:
        conn.close()
        return jsonify({"error": "cannot edit deleted message"}), 400

    conn.execute(
        "UPDATE messages SET text = ?, edited_at = ? WHERE id = ?",
        (text, _utc_now_iso(), message_id),
    )
    conn.commit()
    updated = conn.execute(
        "SELECT id, chat_id, sender, text, created_at, edited_at, is_deleted, deleted_at FROM messages WHERE id = ?",
        (message_id,),
    ).fetchone()
    conn.close()
    return jsonify(_chat_message_to_dict(updated))


@app.delete("/api/messages/<int:message_id>")
def api_delete_message(message_id):
    conn = _get_chat_conn()
    msg = conn.execute(
        "SELECT id, chat_id, sender, text, created_at, edited_at, is_deleted, deleted_at FROM messages WHERE id = ?",
        (message_id,),
    ).fetchone()
    if not msg:
        conn.close()
        return jsonify({"error": "message not found"}), 404

    conn.execute(
        "UPDATE messages SET is_deleted = 1, deleted_at = ? WHERE id = ?",
        (_utc_now_iso(), message_id),
    )
    conn.commit()
    deleted = conn.execute(
        "SELECT id, chat_id, sender, text, created_at, edited_at, is_deleted, deleted_at FROM messages WHERE id = ?",
        (message_id,),
    ).fetchone()
    conn.close()
    return jsonify(_chat_message_to_dict(deleted))


@app.post("/api/messages/<int:message_id>/restore")
def api_restore_message(message_id):
    conn = _get_chat_conn()
    msg = conn.execute(
        "SELECT id, chat_id, sender, text, created_at, edited_at, is_deleted, deleted_at FROM messages WHERE id = ?",
        (message_id,),
    ).fetchone()
    if not msg:
        conn.close()
        return jsonify({"error": "message not found"}), 404

    conn.execute(
        "UPDATE messages SET is_deleted = 0, deleted_at = NULL WHERE id = ?",
        (message_id,),
    )
    conn.commit()
    restored = conn.execute(
        "SELECT id, chat_id, sender, text, created_at, edited_at, is_deleted, deleted_at FROM messages WHERE id = ?",
        (message_id,),
    ).fetchone()
    conn.close()
    return jsonify(_chat_message_to_dict(restored))


@app.get("/api/profanities")
def api_list_profanities():
    level = (request.args.get("level") or "").strip().lower()
    if level and level not in ("mild", "strong", "extreme"):
        return jsonify({"error": "level must be mild, strong, or extreme"}), 400

    conn = _get_chat_conn()
    if level:
        rows = conn.execute(
            "SELECT id, word, level, created_at, updated_at FROM profanities WHERE level = ? ORDER BY word ASC",
            (level,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, word, level, created_at, updated_at FROM profanities ORDER BY word ASC",
        ).fetchall()
    conn.close()
    return jsonify([{
        "id": r["id"],
        "word": r["word"],
        "level": r["level"],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    } for r in rows])


@app.post("/api/profanity-block")
def api_profanity_block():
    data = request.get_json(silent=True) or {}
    chat_id = (data.get("chat_id") or "").strip()
    text = (data.get("text") or "").strip()
    if not chat_id or not text:
        return jsonify({"error": "chat_id and text are required"}), 400
    return jsonify({"ok": True}), 201

@app.get("/<path:page>")
def page(page: str):
    if page.endswith(".html"):
        page = page[:-5]

    if page in PAGES:
        if page == "dashboard":
            selected_category = (request.args.get("filter") or "all").strip()
            allowed = {"all", "Money", "Career", "Relationships", "Life Skills", "Health"}
            if selected_category not in allowed:
                selected_category = "all"
            posts = _forum_list_posts(selected_category)
            user_id = _require_login()
            connections_count = 0
            memories_count = 0
            repoints_count = 0
            circles_count = 0
            badges_count = 0
            if user_id:
                conn = _get_chat_conn()
                connections_count = conn.execute(
                    "SELECT COUNT(*) AS c FROM matches WHERE user_id = ?", (user_id,)
                ).fetchone()["c"]
                conn.close()

                conn = _get_main_conn()
                memories_count = conn.execute(
                    "SELECT COUNT(*) AS c FROM challenge_entries WHERE user_id = ?", (user_id,)
                ).fetchone()["c"]
                badges_count = conn.execute(
                    "SELECT COUNT(*) AS c FROM user_badges WHERE user_id = ? AND earned = 1",
                    (user_id,),
                ).fetchone()["c"]
                conn.close()

                u = db.session.get(User, user_id)
                repoints_count = getattr(u, "total_points", 0) or 0
                circles_count = CircleSignup.query.filter_by(user_id=user_id).count()

            return render_template(
                PAGES[page],
                posts=posts,
                selected_category=selected_category,
                is_admin=_require_admin(),
                forum_user_name=_forum_current_user_name(),
                connections_count=connections_count,
                memories_count=memories_count,
                repoints_count=repoints_count,
                circles_count=circles_count,
                badges_count=badges_count,
            )
        if page == "forum":
            selected_category = (request.args.get("filter") or "all").strip()
            allowed = {"all", "Money", "Career", "Relationships", "Life Skills", "Health"}
            if selected_category not in allowed:
                selected_category = "all"
            posts = _forum_list_posts(selected_category)
            user_id = _require_login()
            return render_template(
                PAGES[page],
                posts=posts,
                selected_category=selected_category,
                is_admin=_require_admin(),
                forum_user_name=_forum_current_user_name(),
                user_id=user_id,
            )
        if page == "profile":
            if not _require_login():
                return redirect("/login")
            # Get user data
            user_id = session["user_id"]
            u = db.session.get(User, user_id)
            user_settings = _get_user_settings_map(user_id)
            onboarding = json.loads(user_settings.get("onboarding", "{}"))
            user_languages = _load_user_languages(user_id)
            avatar_url = user_settings.get("avatar_url", "")
            banner_url = user_settings.get("banner_url", "")
            location_name = user_settings.get("location_name", "")
            verified_with = user_settings.get("verified_with", "")

            conn = _get_chat_conn()
            connections_count = conn.execute(
                "SELECT COUNT(*) AS c FROM matches WHERE user_id = ?", (user_id,)
            ).fetchone()["c"]
            conn.close()

            conn = _get_main_conn()
            memories_count = conn.execute(
                "SELECT COUNT(*) AS c FROM challenge_entries WHERE user_id = ?", (user_id,)
            ).fetchone()["c"]
            badges_count = conn.execute(
                "SELECT COUNT(*) AS c FROM user_badges WHERE user_id = ? AND earned = 1",
                (user_id,),
            ).fetchone()["c"]
            conn.close()

            repoints_count = getattr(u, "total_points", 0) or 0
            circles_count = CircleSignup.query.filter_by(user_id=user_id).count()
            google_maps_key = os.getenv("GOOGLE_MAPS_KEY", "")

            member_label = "Senior" if (u.member_type or "").strip().lower() in ("senior", "elderly") else "Youth"
            return render_template(
                PAGES[page],
                user=u,
                onboarding=onboarding,
                user_languages=user_languages,
                avatar_url=avatar_url,
                banner_url=banner_url,
                location_name=location_name,
                verified_with=verified_with,
                connections_count=connections_count,
                memories_count=memories_count,
                repoints_count=repoints_count,
                circles_count=circles_count,
                badges_count=badges_count,
                member_label=member_label,
                google_maps_key=google_maps_key,
            )
        if page == "wellbeing":
            if not _require_login():
                return redirect("/login")
            user_id = session["user_id"]
            u = db.session.get(User, user_id)
            return render_template(PAGES[page], user=u)
        if page == "avatar":
            if not _require_login():
                return redirect("/login")
            return render_template(PAGES[page])
        if page == "scrapbook":
            if not _require_login():
                return redirect("/login")
            user_id = session["user_id"]
            u = db.session.get(User, user_id)
            return render_template(PAGES[page], user=u)
        if page == "onboarding":
            user_id = _require_login()
            if user_id:
                settings = UserSetting.query.filter_by(user_id=user_id).all()
                user_settings = {s.key: s.value for s in settings}
                onboarding = json.loads(user_settings.get("onboarding", "{}"))
                return render_template(PAGES[page], onboarding=onboarding)
            else:
                return render_template(PAGES[page], onboarding={})
        if page == "achievements":
            user_id = _require_login()
            if not user_id:
                return redirect("/login")
            u = db.session.get(User, user_id)
            return render_template(PAGES[page], user=u)
        return render_template(PAGES[page])

    return ("Not found", 404)


def _require_login():
    demo_user = request.headers.get("X-Demo-User")
    if demo_user:
        try:
            demo_id = int(demo_user)
        except (TypeError, ValueError):
            return None
        user = db.session.get(User, demo_id)
        return demo_id if user else None

    user_id = session.get("user_id")
    if not user_id:
        return None
    return user_id


def _get_user_settings_map(user_id: int) -> dict:
    try:
        settings = UserSetting.query.filter_by(user_id=user_id).all()
        return {s.key: s.value for s in settings}
    except DatabaseError:
        db.session.rollback()
        return {}


def _set_user_setting(user_id: int, key: str, value: str) -> None:
    try:
        setting = UserSetting.query.filter_by(user_id=user_id, key=key).first()
        if setting is None:
            setting = UserSetting(user_id=user_id, key=key, value=value)
            db.session.add(setting)
        else:
            setting.value = value
    except DatabaseError:
        db.session.rollback()


def _safe_json(value: str, default):
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


ALLOWED_PROFILE_LANGUAGES = [
    "English",
    "Chinese (Mandarin)",
    "Malay",
    "Tamil",
    "Hokkien",
]


def _load_user_languages(user_id: int) -> list[str]:
    user_settings = _get_user_settings_map(user_id)
    parsed = _safe_json(user_settings.get("languages", "[]") or "[]", [])
    if not isinstance(parsed, list):
        return []
    allowed = set(ALLOWED_PROFILE_LANGUAGES)
    cleaned = []
    for language in parsed:
        value = str(language).strip()
        if value and value in allowed and value not in cleaned:
            cleaned.append(value)
    return cleaned


def _save_user_languages(user_id: int, selected_languages: list[str]) -> list[str]:
    allowed = set(ALLOWED_PROFILE_LANGUAGES)
    cleaned = []
    for language in selected_languages or []:
        value = str(language).strip()
        if value and value in allowed and value not in cleaned:
            cleaned.append(value)
    _set_user_setting(user_id, "languages", json.dumps(cleaned))
    return cleaned


def _build_match_profile(user: User, settings_map: dict, viewer_interests: list) -> dict:
    onboarding = _safe_json(settings_map.get("onboarding", "{}"), {})
    interests = onboarding.get("interests") or []
    stations = onboarding.get("stations") or []
    member_type = (user.member_type or onboarding.get("memberType") or "youth").strip().lower()
    privacy = _safe_json(settings_map.get("privacy", "{}"), {})
    show_age = privacy.get("show_age", True)
    show_location = privacy.get("show_location", True)
    allow_direct = privacy.get("allow_direct", True)

    name = user.full_name or "User"
    avatar_url = settings_map.get("avatar_url") or f"https://api.dicebear.com/7.x/avataaars/svg?seed={name}"
    location_name = settings_map.get("location_name", "")
    location = stations[0] if stations else (location_name.split(",")[0].strip() if location_name else "")

    common = [i for i in interests if i in (viewer_interests or [])]
    match_score = 70 + min(25, len(common) * 6)
    if member_type == "senior":
        age = 65 + (user.id % 12)
    else:
        age = 20 + (user.id % 12)

    matched_tags = common[:3] or interests[:3] or ["Friendly", "Community-minded", "Open learner"]
    goals = ["Meet new friends", "Join a learning circle"]
    if member_type == "senior":
        teach = interests[:2] or ["Life stories", "Local tips"]
        learn = ["Digital tools", "Chat apps"]
        bio = "Enjoys community activities and sharing stories."
    else:
        teach = interests[:2] or ["Digital help", "Study tips"]
        learn = ["Local stories", "Community events"]
        bio = "Keen to connect with seniors and build community."

    return {
        "id": f"user-{user.id}",
        "user_id": user.id,
        "name": name,
        "age": age if show_age else None,
        "avatar": avatar_url,
        "location": location if show_location else "",
        "match": f"{match_score}%",
        "bio": bio,
        "matched": matched_tags,
        "interests": interests or ["Community", "Learning", "Sharing"],
        "goals": goals,
        "teach": teach,
        "learn": learn,
        "stations": stations,
        "allow_direct": bool(allow_direct),
        "is_real": True,
    }


def _match_card_for_user(user: User) -> dict:
    settings_map = _get_user_settings_map(user.id)
    onboarding = _safe_json(settings_map.get("onboarding", "{}"), {})
    stations = onboarding.get("stations") or []
    location_name = settings_map.get("location_name", "")
    location = stations[0] if stations else (location_name.split(",")[0].strip() if location_name else "")
    avatar_url = settings_map.get("avatar_url") or f"https://api.dicebear.com/7.x/avataaars/svg?seed={user.full_name}"
    return {"name": user.full_name, "avatar": avatar_url, "location": location}


def _ensure_match_row(conn, user_id: int, other_user: User) -> None:
    match_key = f"{user_id}:user-{other_user.id}"
    existing = conn.execute(
        "SELECT 1 FROM matches WHERE match_id = ? AND user_id = ?",
        (match_key, user_id),
    ).fetchone()
    if existing:
        return
    meta = _match_card_for_user(other_user)
    conn.execute(
        "INSERT INTO matches (user_id, match_id, name, avatar, location, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, match_key, meta["name"], meta["avatar"], meta["location"], _utc_now_iso()),
    )

def _require_admin():
    return bool(session.get("is_admin"))


def _generate_2fa_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def _send_2fa_email(to_email: str, code: str) -> bool:
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int((os.getenv("SMTP_PORT", "587") or "587").strip())
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip()
    from_email = os.getenv("SMTP_FROM", smtp_user or "no-reply@reconnect.local")
    use_tls = (os.getenv("SMTP_USE_TLS", "1") or "1").strip() == "1"

    if not smtp_host:
        print(f"[2FA DEV] email={to_email} code={code}")
        return False

    msg = EmailMessage()
    msg["Subject"] = "Your Re:Connect verification code"
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(
        "Your login verification code is: "
        + code
        + "\n\nThis code expires in 10 minutes.\nIf you did not request this, ignore this email."
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as smtp:
        if use_tls:
            smtp.starttls()
        if smtp_user:
            smtp.login(smtp_user, smtp_pass)
        smtp.send_message(msg)
    return True


def _set_pending_2fa(user: User, code: str) -> None:
    session["pending_2fa_user_id"] = user.id
    session["pending_2fa_email"] = user.email
    session["pending_2fa_code_sha256"] = hashlib.sha256(code.encode("utf-8")).hexdigest()
    session["pending_2fa_expires_at"] = (datetime.utcnow() + timedelta(minutes=10)).isoformat()


def _clear_pending_2fa() -> None:
    session.pop("pending_2fa_user_id", None)
    session.pop("pending_2fa_email", None)
    session.pop("pending_2fa_code_sha256", None)
    session.pop("pending_2fa_expires_at", None)

#Create Account
@app.post("/api/signup")
def api_signup():
    data = request.get_json(silent=True) or request.form

    full_name = (data.get("fullname") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not full_name or not email or not password:
        return jsonify({"ok": False, "error": "Missing required fields"}), 400

    if len(password) < 8:
        return jsonify({"ok": False, "error": "Password must be at least 8 characters"}), 400
    if not (any(c.isupper() for c in password) and any(c.islower() for c in password) and any(c.isdigit() for c in password) and any(not c.isalnum() for c in password)):
        return jsonify({"ok": False, "error": "Password must include uppercase, lowercase, number, and symbol"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"ok": False, "error": "Email already exists"}), 409

    u = User(full_name=full_name, email=email)
    u.set_password(password)

    db.session.add(u)
    db.session.commit()
    _ensure_ach_user(u)

    # Audit log
    db.session.add(
        AuthEvent(
            user_id=u.id,
            event_type="signup",
            email=u.email,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent", ""),
        )
    )
    db.session.commit()

    session["user_id"] = u.id
    _log_audit("auth", "signup", u.id, {"email": u.email})
    return jsonify({"ok": True})


@app.post("/signup")
def signup():
    full_name = (request.form.get("fullname") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not full_name or not email or not password:
        return render_template("signup.html", error="Missing required fields")

    if len(password) < 8:
        return render_template("signup.html", error="Password must be at least 8 characters")
    if not (any(c.isupper() for c in password) and any(c.islower() for c in password) and any(c.isdigit() for c in password) and any(not c.isalnum() for c in password)):
        return render_template("signup.html", error="Password must include uppercase, lowercase, number, and symbol")

    at_index = email.find("@")
    dot_after_at = email.find(".", at_index + 1) if at_index != -1 else -1
    if at_index <= 0 or dot_after_at == -1:
        return render_template("signup.html", error="Email must be an email address")

    if User.query.filter_by(email=email).first():
        return render_template("signup.html", error="Email already exists")

    u = User(full_name=full_name, email=email)
    u.set_password(password)

    db.session.add(u)
    db.session.commit()
    _ensure_ach_user(u)

    # Audit log
    db.session.add(
        AuthEvent(
            user_id=u.id,
            event_type="signup",
            email=u.email,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent", ""),
        )
    )
    db.session.commit()

    session["user_id"] = u.id
    _log_audit("auth", "signup", u.id, {"email": u.email})
    return redirect("/signup-avatar")


@app.get("/signup-avatar")
def signup_avatar_page():
    user_id = _require_login()
    if not user_id:
        return redirect("/signup")

    settings = _get_user_settings_map(user_id)
    avatar_config = json.loads(settings.get("avatar_config", "{}") or "{}")
    avatar_url = settings.get("avatar_url", "")
    return render_template("signup_avatar.html", avatar_config=avatar_config, avatar_url=avatar_url)


@app.post("/signup-avatar")
def signup_avatar_save():
    user_id = _require_login()
    if not user_id:
        return redirect("/signup")

    data = request.form or {}
    seed = (data.get("seed") or "ReConnect").strip()
    top = (data.get("top") or "").strip()
    eyes = (data.get("eyes") or "").strip()
    mouth = (data.get("mouth") or "").strip()
    accessories = (data.get("accessories") or "").strip()
    skin = (data.get("skin") or "").strip()
    gender = (data.get("gender") or "").strip()
    avatar_data = (data.get("avatar_data") or "").strip()

    accessories_q = "" if accessories == "earbuds" else accessories

    config = {
        "seed": seed,
        "top": top,
        "eyes": eyes,
        "mouth": mouth,
        "accessories": accessories,
        "skin": skin,
        "gender": gender,
    }

    qs = "&".join(
        [
            f"seed={urllib.parse.quote(seed)}",
            f"top={urllib.parse.quote(top)}",
            f"eyes={urllib.parse.quote(eyes)}",
            f"mouth={urllib.parse.quote(mouth)}",
            f"accessories={urllib.parse.quote(accessories_q)}",
            f"facialHair=Blank",
            f"skinColor={urllib.parse.quote(skin)}",
        ]
    )
    avatar_url = avatar_data or f"/api/avatar?{qs}"

    _set_user_setting(user_id, "avatar_config", json.dumps(config))
    _set_user_setting(user_id, "avatar_url", avatar_url)
    db.session.commit()

    return redirect("/onboarding")

#Log In
@app.post("/api/login")
def api_login():
    data = request.get_json(silent=True) or request.form

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"ok": False, "error": "Missing email or password"}), 400

    if len(password) < 8:
        return jsonify({"ok": False, "error": "Password must be at least 8 characters"}), 400

    u = User.query.filter_by(email=email).first()
    if not u or not u.check_password(password):
        return jsonify({"ok": False, "error": "Invalid email or password"}), 401

    code = _generate_2fa_code()
    _set_pending_2fa(u, code)
    delivered = False
    try:
        delivered = _send_2fa_email(u.email, code)
    except Exception:
        delivered = False

    return jsonify(
        {
            "ok": True,
            "requires_2fa": True,
            "delivery": "email" if delivered else "dev",
            "dev_code": code if not delivered else None,
        }
    )


@app.post("/api/login/2fa/verify")
def api_login_2fa_verify():
    pending_user_id = session.get("pending_2fa_user_id")
    pending_hash = session.get("pending_2fa_code_sha256")
    pending_expires = session.get("pending_2fa_expires_at")
    if not pending_user_id or not pending_hash or not pending_expires:
        return jsonify({"ok": False, "error": "No pending verification"}), 400

    try:
        expires_at = datetime.fromisoformat(pending_expires)
    except Exception:
        _clear_pending_2fa()
        return jsonify({"ok": False, "error": "Verification expired"}), 400
    if datetime.utcnow() > expires_at:
        _clear_pending_2fa()
        return jsonify({"ok": False, "error": "Verification code expired"}), 400

    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    if len(code) != 6 or not code.isdigit():
        return jsonify({"ok": False, "error": "Enter a valid 6-digit code"}), 400

    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    if code_hash != pending_hash:
        return jsonify({"ok": False, "error": "Incorrect verification code"}), 400

    u = db.session.get(User, pending_user_id)
    if not u:
        _clear_pending_2fa()
        return jsonify({"ok": False, "error": "User not found"}), 404

    db.session.add(
        AuthEvent(
            user_id=u.id,
            event_type="login",
            email=u.email,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent", ""),
        )
    )
    db.session.commit()

    session["user_id"] = u.id
    _clear_pending_2fa()
    _log_audit("auth", "login", u.id, {"email": u.email, "method": "2fa_email"})
    return jsonify({"ok": True})


@app.post("/api/login/2fa/resend")
def api_login_2fa_resend():
    pending_user_id = session.get("pending_2fa_user_id")
    if not pending_user_id:
        return jsonify({"ok": False, "error": "No pending verification"}), 400

    u = db.session.get(User, pending_user_id)
    if not u:
        _clear_pending_2fa()
        return jsonify({"ok": False, "error": "User not found"}), 404

    code = _generate_2fa_code()
    _set_pending_2fa(u, code)
    delivered = False
    try:
        delivered = _send_2fa_email(u.email, code)
    except Exception:
        delivered = False
    return jsonify(
        {
            "ok": True,
            "delivery": "email" if delivered else "dev",
            "dev_code": code if not delivered else None,
        }
    )


@app.post("/api/logout")
def api_logout():
    session.pop("user_id", None)
    _clear_pending_2fa()
    return jsonify({"ok": True})


@app.get("/api/me")
def api_me():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    u = db.session.get(User, user_id)
    if not u:
        return jsonify({"ok": False, "error": "User not found"}), 404

    return jsonify(
        {
            "ok": True,
            "user": {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "member_type": u.member_type,
            },
        }
    )

#Edit Bio
@app.get("/api/profile")
def api_profile():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    u = db.session.get(User, user_id)
    if not u:
        return jsonify({"ok": False, "error": "User not found"}), 404

    user_settings = _get_user_settings_map(user_id)

    onboarding = json.loads(user_settings.get("onboarding", "{}"))
    languages = _load_user_languages(user_id)
    skills_teach = json.loads(user_settings.get("skills_teach", "[]") or "[]")
    skills_learn = json.loads(user_settings.get("skills_learn", "[]") or "[]")
    privacy = json.loads(user_settings.get("privacy", "{}") or "{}")
    notifications = json.loads(user_settings.get("notifications", "{}") or "{}")

    conn = _get_chat_conn()
    connections_count = conn.execute(
        "SELECT COUNT(*) AS c FROM matches WHERE user_id = ?", (user_id,)
    ).fetchone()["c"]
    conn.close()

    conn = _get_main_conn()
    memories_count = conn.execute(
        "SELECT COUNT(*) AS c FROM challenge_entries WHERE user_id = ?", (user_id,)
    ).fetchone()["c"]
    badges_count = conn.execute(
        "SELECT COUNT(*) AS c FROM user_badges WHERE user_id = ? AND earned = 1",
        (user_id,),
    ).fetchone()["c"]
    conn.close()

    repoints = getattr(u, "total_points", 0) or 0
    circles_count = CircleSignup.query.filter_by(user_id=user_id).count()
    safety = _get_safety_snapshot(user_id)

    return jsonify(
        {
            "ok": True,
            "profile": {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "member_type": u.member_type,
                "bio": user_settings.get("bio", ""),
                "onboarding": onboarding,
                "languages": languages,
                "skills_teach": skills_teach,
                "skills_learn": skills_learn,
                "privacy": privacy,
                "notifications": notifications,
                "avatar_url": user_settings.get("avatar_url", ""),
                "banner_url": user_settings.get("banner_url", ""),
                "location_name": user_settings.get("location_name", ""),
                "location_lat": user_settings.get("location_lat", ""),
                "location_lng": user_settings.get("location_lng", ""),
                "verified_with": user_settings.get("verified_with", ""),
                "connections_count": connections_count,
                "memories_count": memories_count,
                "repoints": repoints,
                "circles_count": circles_count,
                "badges_count": badges_count,
                "emergency_contact": json.loads(user_settings.get("emergency_contact", "{}") or "{}"),
                "safety": safety,
            },
        }
    )


@app.post("/api/profile")
def api_update_profile():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}

    bio = data.get("bio", "").strip()
    languages = data.get("languages")
    skills_teach = data.get("skills_teach")
    skills_learn = data.get("skills_learn")
    privacy = data.get("privacy")
    interests = data.get("interests")
    notifications = data.get("notifications")
    location_name = (data.get("location_name") or "").strip()
    location_lat = (data.get("location_lat") or "").strip()
    location_lng = (data.get("location_lng") or "").strip()
    verified_with = data.get("verified_with")
    emergency_contact = data.get("emergency_contact")

    if bio:
        _set_user_setting(user_id, "bio", bio)
    if languages is not None:
        _save_user_languages(user_id, languages)
    if skills_teach is not None:
        _set_user_setting(user_id, "skills_teach", json.dumps(skills_teach))
    if skills_learn is not None:
        _set_user_setting(user_id, "skills_learn", json.dumps(skills_learn))
    if privacy is not None:
        _set_user_setting(user_id, "privacy", json.dumps(privacy))
    if interests is not None:
        existing = _safe_json(_get_user_settings_map(user_id).get("onboarding", "{}"), {})
        existing["interests"] = interests
        _set_user_setting(user_id, "onboarding", json.dumps(existing))
    if notifications is not None:
        _set_user_setting(user_id, "notifications", json.dumps(notifications))
    if location_name or location_lat or location_lng:
        _set_user_setting(user_id, "location_name", location_name)
        _set_user_setting(user_id, "location_lat", location_lat)
        _set_user_setting(user_id, "location_lng", location_lng)
    if verified_with is not None:
        cleaned = (verified_with or "").strip().lower()
        if cleaned and cleaned not in {"email", "phone", "singpass", "nric"}:
            return jsonify({"ok": False, "error": "Verification must be email or phone"}), 400
        _set_user_setting(user_id, "verified_with", cleaned)
    if emergency_contact is not None:
        _set_user_setting(user_id, "emergency_contact", json.dumps(emergency_contact))

    db.session.commit()
    return jsonify({"ok": True})


@app.post("/profile/languages/save")
def save_profile_languages():
    user_id = _require_login()
    if not user_id:
        return redirect("/login")

    selected_languages = request.form.getlist("languages")
    _save_user_languages(user_id, selected_languages)
    db.session.commit()
    flash("Languages saved.", "success")
    return redirect("/profile")


@app.get("/api/safety_score")
def api_safety_score():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    snapshot = _get_safety_snapshot(user_id)
    return jsonify({"ok": True, "safety": snapshot})


@app.get("/api/wellbeing/summary")
def api_wellbeing_summary():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    checkin = _get_latest_checkin(user_id)
    recos = _load_wellbeing_recos(user_id)
    analytics = _wellbeing_analytics(user_id)
    insight = analytics["insights"][0] if analytics["insights"] else _wellbeing_insight(user_id)
    nudge = _wellbeing_nudge(user_id, analytics)
    return jsonify(
        {
            "ok": True,
            "checkin": {
                "id": checkin["id"],
                "mood": _normalize_mood(checkin["mood"]),
                "reason": checkin["reason"],
                "notes": checkin["notes"],
                "created_at": checkin["created_at"],
            }
            if checkin
            else None,
            "last_updated_human": _humanize_relative_time(checkin["created_at"]) if checkin else "",
            "recommendations": recos,
            "insight": insight,
            "trend": analytics["trend"],
            "activity": analytics["activity"],
            "risk": analytics["risk"],
            "score": analytics["score"],
            "nudge": nudge,
            "badges": analytics["badges"],
        }
    )


@app.post("/api/wellbeing/checkin")
def api_wellbeing_checkin():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    mood = (data.get("mood") or "").strip().lower()
    reason = (data.get("reason") or "").strip()
    notes = (data.get("notes") or "").strip()
    if mood not in WELLBEING_MOOD_SCORES:
        return jsonify({"ok": False, "error": "Mood must be one of: happy, good, neutral, stressed, sad"}), 400

    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO mood_checkins (user_id, mood, reason, notes, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, mood, reason or None, notes or None, _utc_now_iso()),
    )
    conn.commit()
    conn.close()

    recos = _build_wellbeing_recos(mood)
    _store_wellbeing_recos(user_id, mood, recos)
    _add_notification(user_id, "wellbeing", f"Mood check-in saved: {mood}.", {"mood": mood})
    analytics = _wellbeing_analytics(user_id)
    return jsonify(
        {
            "ok": True,
            "mood": mood,
            "recommendations": recos,
            "insight": analytics["insights"][0] if analytics["insights"] else _wellbeing_insight(user_id),
            "trend": analytics["trend"],
            "risk": analytics["risk"],
            "score": analytics["score"],
            "nudge": _wellbeing_nudge(user_id, analytics),
        }
    )


@app.get("/api/wellbeing/history")
def api_wellbeing_history():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    rows = _get_recent_checkins(user_id, limit=30)
    history = [
        {
            "mood": _normalize_mood(r["mood"]),
            "reason": r["reason"],
            "notes": r["notes"],
            "created_at": r["created_at"],
            "mood_score": WELLBEING_MOOD_SCORES.get(_normalize_mood(r["mood"]), 3),
        }
        for r in rows
    ]
    return jsonify({"ok": True, "history": history})


@app.get("/api/wellbeing/dashboard")
def api_wellbeing_dashboard():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    analytics = _wellbeing_analytics(user_id)
    latest = _get_latest_checkin(user_id)
    return jsonify(
        {
            "ok": True,
            "latest_checkin": {
                "mood": _normalize_mood(latest["mood"]),
                "created_at": latest["created_at"],
                "reason": latest["reason"],
                "notes": latest["notes"],
            }
            if latest
            else None,
            "last_updated_human": _humanize_relative_time(latest["created_at"]) if latest else "",
            "trend": analytics["trend"],
            "activity": analytics["activity"],
            "daily_activity_7d": analytics["daily_activity_7d"],
            "social_energy": analytics["social_energy"],
            "emotion_breakdown": analytics["emotion_breakdown"],
            "weekly_distribution": analytics["weekly_distribution"],
            "line_points_30d": analytics["line_points_30d"],
            "mood_points_7d": analytics["mood_points_7d"],
            "insights": analytics["insights"],
            "recommendations": analytics["recommendations"],
            "risk": analytics["risk"],
            "score": analytics["score"],
            "badges": analytics["badges"],
            "nudge": _wellbeing_nudge(user_id, analytics),
        }
    )


@app.get("/api/wellbeing/journal")
def api_wellbeing_journal():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    conn = _get_main_conn()
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT id, prompt, gratitude, reflection, created_at
        FROM wellbeing_journal
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 30
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return jsonify(
        {
            "ok": True,
            "entries": [
                {
                    "id": r["id"],
                    "prompt": r["prompt"] or "",
                    "gratitude": r["gratitude"] or "",
                    "reflection": r["reflection"] or "",
                    "created_at": r["created_at"],
                }
                for r in rows
            ],
        }
    )


@app.post("/api/wellbeing/journal")
def api_wellbeing_journal_create():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    gratitude = (data.get("gratitude") or "").strip()
    reflection = (data.get("reflection") or "").strip()
    if not gratitude and not reflection:
        return jsonify({"ok": False, "error": "Write at least gratitude or reflection."}), 400
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO wellbeing_journal (user_id, prompt, gratitude, reflection, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, prompt or None, gratitude or None, reflection or None, _utc_now_iso()),
    )
    conn.commit()
    conn.close()
    _add_notification(user_id, "wellbeing", "Reflection journal saved.", {})
    return jsonify({"ok": True})


@app.get("/api/scrapbook/entries")
def api_scrapbook_entries():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    conn = _get_main_conn()
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT e.id, e.entry_type, e.title, e.content, e.visibility, e.created_at,
               e.related_user_id, e.circle_title, e.mood_tag, e.location, e.pinned,
               (SELECT file_path FROM scrapbook_media m WHERE m.entry_id = e.id ORDER BY m.id DESC LIMIT 1) AS media_url
        FROM scrapbook_entries e
        WHERE e.owner_user_id = ?
        ORDER BY e.pinned DESC, e.id DESC
        LIMIT 200
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return jsonify(
        {
            "ok": True,
            "entries": [
                {
                    "id": r["id"],
                    "entry_type": r["entry_type"],
                    "title": r["title"],
                    "content": r["content"],
                    "visibility": r["visibility"],
                    "created_at": r["created_at"],
                    "related_user_id": r["related_user_id"],
                    "circle_title": r["circle_title"],
                    "mood_tag": r["mood_tag"],
                    "location": r["location"],
                    "pinned": r["pinned"],
                    "media_url": r["media_url"],
                }
                for r in rows
            ],
        }
    )


@app.post("/api/scrapbook/entries")
def api_scrapbook_create():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    entry_type = (data.get("entry_type") or "chat").strip().lower()
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    visibility = (data.get("visibility") or "private").strip().lower()
    media_url = (data.get("media_url") or "").strip()
    related_user_id = data.get("related_user_id")
    circle_title = (data.get("circle_title") or "").strip()
    mood_tag = (data.get("mood_tag") or "").strip().lower()
    location = (data.get("location") or "").strip()

    if entry_type not in {"chat", "meetup", "circle", "challenge"}:
        return jsonify({"ok": False, "error": "Invalid entry type"}), 400
    if visibility not in {"private", "circle", "public"}:
        return jsonify({"ok": False, "error": "Invalid visibility"}), 400
    if mood_tag and mood_tag not in {"happy", "neutral", "lonely"}:
        return jsonify({"ok": False, "error": "Invalid mood tag"}), 400
    if not title:
        return jsonify({"ok": False, "error": "Title is required"}), 400

    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO scrapbook_entries (owner_user_id, related_user_id, circle_title, entry_type, title, content, visibility, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, related_user_id, circle_title or None, entry_type, title, content or None, visibility, _utc_now_iso()),
    )
    cur.execute(
        "UPDATE scrapbook_entries SET mood_tag = ?, location = ? WHERE id = ?",
        (mood_tag or None, location or None, cur.lastrowid),
    )
    entry_id = cur.lastrowid
    if media_url:
        media_type = "audio" if media_url.lower().endswith((".mp3", ".wav", ".ogg")) else "image"
        cur.execute(
            """
            INSERT INTO scrapbook_media (entry_id, media_type, file_path, uploaded_by, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (entry_id, media_type, media_url, user_id, _utc_now_iso()),
        )
    conn.commit()
    conn.close()
    # Update streaks
    conn = _get_main_conn()
    cur = conn.cursor()
    now = datetime.utcnow()
    week_start = _week_start(now)
    prev = cur.execute(
        "SELECT total_entries, weekly_streak, last_entry_at FROM scrapbook_stats WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    total_entries = (prev["total_entries"] if prev else 0) + 1
    weekly_streak = prev["weekly_streak"] if prev else 0
    last_entry_at = prev["last_entry_at"] if prev else None
    if not last_entry_at:
        weekly_streak = 1
    else:
        try:
            last_dt = datetime.fromisoformat(last_entry_at)
            if last_dt < week_start:
                weekly_streak += 1
        except Exception:
            weekly_streak = 1
    cur.execute(
        "INSERT OR REPLACE INTO scrapbook_stats (user_id, total_entries, weekly_streak, last_entry_at) VALUES (?, ?, ?, ?)",
        (user_id, total_entries, weekly_streak, now.isoformat()),
    )
    conn.commit()
    conn.close()
    _add_notification(user_id, "scrapbook", f"Memory saved: {title}.", {"entry_id": entry_id})
    return jsonify({"ok": True, "id": entry_id})


@app.post("/api/storybook/create")
def api_storybook_create():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    place = (data.get("place") or "").strip()
    event = (data.get("event") or "").strip()
    feeling = (data.get("feeling") or "").strip()
    lesson = (data.get("lesson") or "").strip()
    media_url = (data.get("media_url") or "").strip()
    if not title:
        return jsonify({"ok": False, "error": "Title is required"}), 400

    parts = []
    if place:
        parts.append(f"This story took place at {place}.")
    if event:
        parts.append(f"On that day, {event}.")
    if feeling:
        parts.append(f"I felt {feeling}.")
    if lesson:
        parts.append(f"The lesson I want to share is: {lesson}.")
    content = " ".join(parts).strip()

    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO storybook_drafts (user_id, title, place, event, feeling, lesson, media_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, title, place or None, event or None, feeling or None, lesson or None, media_url or None, _utc_now_iso()),
    )
    cur.execute(
        """
        INSERT INTO scrapbook_entries (owner_user_id, related_user_id, circle_title, entry_type, title, content, visibility, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, None, None, "storybook", title, content or None, "private", _utc_now_iso()),
    )
    entry_id = cur.lastrowid
    if media_url:
        cur.execute(
            """
            INSERT INTO scrapbook_media (entry_id, media_type, file_path, uploaded_by, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (entry_id, "image", media_url, user_id, _utc_now_iso()),
        )
    conn.commit()
    conn.close()
    _add_notification(user_id, "scrapbook", f"Storybook saved: {title}.", {"entry_id": entry_id})
    return jsonify({"ok": True, "id": entry_id})


@app.post("/api/scrapbook/pin")
def api_scrapbook_pin():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    entry_id = data.get("entry_id")
    pinned = 1 if data.get("pinned") else 0
    if not entry_id:
        return jsonify({"ok": False, "error": "entry_id required"}), 400
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE scrapbook_entries SET pinned = ? WHERE id = ? AND owner_user_id = ?",
        (pinned, entry_id, user_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.post("/api/scrapbook/reactions")
def api_scrapbook_reaction():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    entry_id = data.get("entry_id")
    reaction = (data.get("reaction") or "").strip()
    if reaction not in {"heart", "star", "thumbs"}:
        return jsonify({"ok": False, "error": "Invalid reaction"}), 400
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO scrapbook_reactions (entry_id, user_id, reaction_type, created_at) VALUES (?, ?, ?, ?)",
        (entry_id, user_id, reaction, _utc_now_iso()),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.get("/api/scrapbook/comments")
def api_scrapbook_comments():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    entry_id = request.args.get("entry_id")
    conn = _get_main_conn()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, entry_id, user_id, comment_text, created_at FROM scrapbook_comments WHERE entry_id = ? ORDER BY id DESC LIMIT 50",
        (entry_id,),
    ).fetchall()
    conn.close()
    return jsonify({"ok": True, "comments": [dict(r) for r in rows]})


@app.post("/api/scrapbook/comments")
def api_scrapbook_comment_create():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    entry_id = data.get("entry_id")
    text = (data.get("text") or "").strip()
    if not entry_id or not text:
        return jsonify({"ok": False, "error": "entry_id and text required"}), 400
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO scrapbook_comments (entry_id, user_id, comment_text, created_at) VALUES (?, ?, ?, ?)",
        (entry_id, user_id, text, _utc_now_iso()),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.get("/api/scrapbook/settings")
def api_scrapbook_settings():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    return jsonify({"ok": True, "settings": _get_scrapbook_settings(user_id)})


@app.post("/api/scrapbook/settings")
def api_scrapbook_settings_update():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    theme = (data.get("theme") or "").strip().lower()
    view = (data.get("view") or "").strip().lower()
    if theme and theme not in {"minimal", "vintage", "kampung", "modern"}:
        return jsonify({"ok": False, "error": "Invalid theme"}), 400
    if view and view not in {"book", "timeline", "grid"}:
        return jsonify({"ok": False, "error": "Invalid view"}), 400
    _set_scrapbook_settings(user_id, theme or None, view or None)
    return jsonify({"ok": True})


@app.get("/api/scrapbook/suggest")
def api_scrapbook_suggest():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    # Placeholder AI suggestion
    title = "Shared Moments"
    content = "You and a friend shared meaningful stories this week. Would you like to save this memory?"
    return jsonify({"ok": True, "suggestion": {"title": title, "content": content, "entry_type": "chat"}})


@app.get("/api/scrapbook/family_viewer")
def api_scrapbook_family_viewer():
    access_key = (request.args.get("key") or "").strip()
    if not access_key:
        return jsonify({"ok": False, "error": "Missing key"}), 400
    conn = _get_main_conn()
    cur = conn.cursor()
    viewer = cur.execute(
        "SELECT * FROM trusted_viewers WHERE access_key = ?",
        (access_key,),
    ).fetchone()
    if not viewer:
        conn.close()
        return jsonify({"ok": False, "error": "Invalid key"}), 404
    owner_id = viewer["owner_user_id"]
    latest_checkin = cur.execute(
        "SELECT mood, created_at FROM mood_checkins WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (owner_id,),
    ).fetchone()
    activity = {
        "circles": cur.execute("SELECT COUNT(*) AS c FROM circle_signups WHERE user_id = ?", (owner_id,)).fetchone()["c"],
        "challenges": cur.execute("SELECT COUNT(*) AS c FROM challenge_entries WHERE user_id = ?", (owner_id,)).fetchone()["c"],
    }
    conn.close()
    return jsonify(
        {
            "ok": True,
            "mood": dict(latest_checkin) if latest_checkin else None,
            "activity": activity,
            "alerts": [],
        }
    )


def _save_uploaded_image(file_storage, prefix: str, user_id: int) -> str:
    filename = secure_filename(file_storage.filename or "")
    if not filename:
        raise ValueError("Invalid filename")
    ext = Path(filename).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        raise ValueError("Unsupported file type")
    safe_name = f"{prefix}_{user_id}_{int(time.time())}{ext}"
    path = UPLOADS_DIR / safe_name
    file_storage.save(path)
    return f"/static/uploads/{safe_name}"


@app.post("/api/profile/avatar")
def api_profile_avatar():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    file = request.files.get("avatar")
    if not file:
        return jsonify({"ok": False, "error": "No file uploaded"}), 400
    try:
        url = _save_uploaded_image(file, "avatar", user_id)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    _set_user_setting(user_id, "avatar_url", url)
    db.session.commit()
    return jsonify({"ok": True, "url": url})


@app.post("/api/profile/banner")
def api_profile_banner():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    file = request.files.get("banner")
    if not file:
        return jsonify({"ok": False, "error": "No file uploaded"}), 400
    try:
        url = _save_uploaded_image(file, "banner", user_id)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    _set_user_setting(user_id, "banner_url", url)
    db.session.commit()
    return jsonify({"ok": True, "url": url})


@app.post("/api/report")
def api_report():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    reason = (data.get("reason") or "").strip()
    incident_date = (data.get("incident_date") or "").strip()
    details = (data.get("details") or "").strip()
    target_match_id = (data.get("target_match_id") or "").strip()
    block_connection = bool(data.get("block_connection"))
    if not reason or not incident_date:
        return jsonify({"ok": False, "error": "Reason and date are required"}), 400

    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reports (user_id, reason, incident_date, details, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, reason, incident_date, details or None, "pending", _utc_now_iso()),
    )
    conn.commit()
    conn.close()
    if block_connection and target_match_id:
        chat = _get_chat_conn()
        chat.execute("DELETE FROM messages WHERE chat_id = ?", (target_match_id,))
        chat.execute("DELETE FROM matches WHERE user_id = ? AND match_id = ?", (user_id, target_match_id))
        chat.commit()
        chat.close()
    _log_audit("safety", "report", user_id, {"reason": reason, "incident_date": incident_date})
    return jsonify({"ok": True})


#Join Circle
@app.post("/api/circle_signup")
def api_circle_signup():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    time = (data.get("time") or "").strip()
    duration = (data.get("duration") or "").strip()

    if not title:
        return jsonify({"ok": False, "error": "Missing circle title"}), 400

    signup = CircleSignup(
        user_id=user_id,
        circle_title=title,
        circle_time=time,
        circle_duration=duration,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent", ""),
    )
    db.session.add(signup)
    db.session.commit()
    _log_audit("learning_circle", "join", user_id, {"title": title})
    _increment_quest_progress(user_id, 1)
    _increment_quest_progress(user_id, 5)
    _add_notification(user_id, "learning_circle", f"Joined learning circle: {title}.", {"title": title})
    points = 3 if _is_partner_circle(title) else 2
    _add_safety_event(user_id, "circle_join", points, f"Joined circle: {title}")
    return jsonify({"ok": True, "id": signup.id})


@app.post("/api/circle_leave")
def api_circle_leave():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"ok": False, "error": "Missing circle title"}), 400

    CircleSignup.query.filter_by(user_id=user_id, circle_title=title).delete()
    db.session.commit()
    _log_audit("learning_circle", "leave", user_id, {"title": title})
    return jsonify({"ok": True})


@app.get("/api/circle_signups")
def api_circle_signups():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    rows = CircleSignup.query.filter_by(user_id=user_id).all()
    return jsonify(
        {
            "ok": True,
            "circles": [
                {
                    "title": r.circle_title,
                    "time": r.circle_time,
                    "duration": r.circle_duration,
                }
                for r in rows
            ],
        }
    )


@app.get("/api/challenges/current")
def api_challenge_current():
    user_id = _require_login()
    is_admin = bool(session.get("is_admin"))
    challenge = _get_current_challenge()
    if not challenge:
        return jsonify({"ok": False, "error": "No challenge available"}), 404

    entries = _list_challenge_entries(challenge["id"])
    out_entries = []
    for e in entries:
        comments = _list_entry_comments(e["id"])
        likes_count = _count_challenge_entry_likes(e["id"])
        liked = False
        if user_id:
            liked = _has_challenge_entry_like(e["id"], user_id)
        out_entries.append(
            {
                "id": e["id"],
                "author_name": e["author_name"],
                "content": e["content"],
                "image_url": e["image_url"],
                "created_at": e["created_at"],
                "likes": likes_count,
                "liked": liked,
                "can_edit": bool(is_admin or (user_id and e["user_id"] == user_id)),
                "comments": [
                    {
                        "id": c["id"],
                        "author_name": c["author_name"],
                        "content": c["content"],
                        "created_at": c["created_at"],
                    }
                    for c in comments
                ],
            }
        )

    return jsonify(
        {
            "ok": True,
            "challenge": {
                "id": challenge["id"],
                "title": challenge["title"],
                "description": challenge["description"],
                "reward_points": challenge["reward_points"],
                "week_label": challenge["week_label"],
            },
            "entries": out_entries,
        }
    )


@app.post("/api/challenges/entries")
def api_create_challenge_entry():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    image_url = (data.get("image_url") or "").strip()
    if not content:
        return jsonify({"ok": False, "error": "Content is required"}), 400

    challenge = _get_current_challenge()
    if not challenge:
        return jsonify({"ok": False, "error": "No challenge available"}), 404

    user = db.session.get(User, user_id)
    author_name = user.full_name if user else "User"

    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO challenge_entries (challenge_id, user_id, author_name, content, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (challenge["id"], user_id, author_name, content, image_url or None, _utc_now_iso()),
    )
    conn.commit()
    conn.close()
    _log_audit("weekly_challenge", "entry", user_id, {"challenge_id": challenge["id"]})
    _add_notification(
        user_id,
        "weekly_challenge",
        f"Submitted a weekly challenge entry: {challenge['title']}.",
        {"challenge_id": challenge["id"]},
    )
    return jsonify({"ok": True})


@app.post("/api/challenges/entries/<int:entry_id>/comments")
def api_create_challenge_comment(entry_id: int):
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"ok": False, "error": "Content is required"}), 400

    user = db.session.get(User, user_id)
    author_name = user.full_name if user else "User"

    conn = _get_main_conn()
    cur = conn.cursor()
    existing = cur.execute(
        "SELECT id, user_id, author_name FROM challenge_entries WHERE id = ?",
        (entry_id,),
    ).fetchone()
    if not existing:
        conn.close()
        return jsonify({"ok": False, "error": "Entry not found"}), 404

    cur.execute(
        "INSERT INTO challenge_comments (entry_id, user_id, author_name, content, created_at) VALUES (?, ?, ?, ?, ?)",
        (entry_id, user_id, author_name, content, _utc_now_iso()),
    )
    conn.commit()
    conn.close()
    _log_audit("weekly_challenge", "comment", user_id, {"entry_id": entry_id})
    if existing["user_id"] and existing["user_id"] != user_id:
        _add_notification(
            existing["user_id"],
            "weekly_challenge_comment",
            f"{author_name} commented on your challenge entry.",
            {"entry_id": entry_id},
        )
    return jsonify({"ok": True})


@app.post("/api/challenges/entries/<int:entry_id>/like")
def api_challenge_like(entry_id: int):
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    conn = _get_main_conn()
    cur = conn.cursor()
    existing = cur.execute(
        "SELECT 1 FROM challenge_entry_likes WHERE entry_id = ? AND user_id = ?",
        (entry_id, user_id),
    ).fetchone()
    liked = False
    if existing:
        cur.execute(
            "DELETE FROM challenge_entry_likes WHERE entry_id = ? AND user_id = ?",
            (entry_id, user_id),
        )
        _log_audit("weekly_challenge", "like_remove", user_id, {"entry_id": entry_id})
        liked = False
    else:
        cur.execute(
            "INSERT INTO challenge_entry_likes (entry_id, user_id) VALUES (?, ?)",
            (entry_id, user_id),
        )
        _log_audit("weekly_challenge", "like_add", user_id, {"entry_id": entry_id})
        liked = True
    conn.commit()
    likes = cur.execute(
        "SELECT COUNT(*) AS c FROM challenge_entry_likes WHERE entry_id = ?",
        (entry_id,),
    ).fetchone()["c"]
    conn.close()
    return jsonify({"ok": True, "likes": likes, "liked": liked})


@app.put("/api/challenges/entries/<int:entry_id>")
def api_challenge_edit(entry_id: int):
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    image_url = (data.get("image_url") or "").strip() or None
    if not content:
        return jsonify({"ok": False, "error": "Content is required"}), 400

    conn = _get_main_conn()
    cur = conn.cursor()
    entry = cur.execute(
        "SELECT user_id FROM challenge_entries WHERE id = ?",
        (entry_id,),
    ).fetchone()
    if not entry:
        conn.close()
        return jsonify({"ok": False, "error": "Entry not found"}), 404
    if entry["user_id"] != user_id and not _require_admin():
        conn.close()
        return jsonify({"ok": False, "error": "Not authorised"}), 403
    cur.execute(
        "UPDATE challenge_entries SET content = ?, image_url = ? WHERE id = ?",
        (content, image_url, entry_id),
    )
    conn.commit()
    conn.close()
    _log_audit("weekly_challenge", "entry_edit", user_id, {"entry_id": entry_id})
    return jsonify({"ok": True})


@app.delete("/api/challenges/entries/<int:entry_id>")
def api_challenge_delete(entry_id: int):
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    conn = _get_main_conn()
    cur = conn.cursor()
    entry = cur.execute(
        "SELECT user_id FROM challenge_entries WHERE id = ?",
        (entry_id,),
    ).fetchone()
    if not entry:
        conn.close()
        return jsonify({"ok": False, "error": "Entry not found"}), 404
    if entry["user_id"] != user_id and not _require_admin():
        conn.close()
        return jsonify({"ok": False, "error": "Not authorised"}), 403
    cur.execute("DELETE FROM challenge_entry_likes WHERE entry_id = ?", (entry_id,))
    cur.execute("DELETE FROM challenge_comments WHERE entry_id = ?", (entry_id,))
    cur.execute("DELETE FROM challenge_entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
    _log_audit("weekly_challenge", "entry_delete", user_id, {"entry_id": entry_id})
    return jsonify({"ok": True})


def _save_user_meetup_preferences(user_id: int, stations: list[str]):
    conn = _get_main_conn()
    cur = conn.cursor()
    cleaned = []
    seen = set()
    for station in stations or []:
        value = str(station).strip()
        if not value:
            continue
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(value)

    cur.execute("DELETE FROM user_meetup_preferences WHERE user_id = ?", (user_id,))
    if cleaned:
        cur.executemany(
            "INSERT OR IGNORE INTO user_meetup_preferences (user_id, station_name) VALUES (?, ?)",
            [(user_id, station) for station in cleaned],
        )
    conn.commit()
    conn.close()


@app.post("/api/onboarding")
def api_onboarding():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}

    member_type = (data.get("memberType") or "").strip()
    interests = data.get("interests") or []
    days = data.get("days") or []
    time = data.get("time") or []
    stations = data.get("stations") or []
    landmarks = data.get("landmarks") or []

    # Update a field on the user table for quick access
    u = db.session.get(User, user_id)
    if not u:
        return jsonify({"ok": False, "error": "User not found"}), 404

    if member_type:
        u.member_type = member_type

    payload = {
        "memberType": member_type,
        "interests": interests,
        "days": days,
        "time": time,
        "stations": stations,
        "landmarks": landmarks,
    }

    setting = UserSetting.query.filter_by(user_id=user_id, key="onboarding").first()
    if setting is None:
        setting = UserSetting(user_id=user_id, key="onboarding", value=json.dumps(payload))
        db.session.add(setting)
    else:
        setting.value = json.dumps(payload)

    location_value = ", ".join(stations) if stations else ""
    location_setting = UserSetting.query.filter_by(user_id=user_id, key="location_name").first()
    if location_setting is None:
        location_setting = UserSetting(user_id=user_id, key="location_name", value=location_value)
        db.session.add(location_setting)
    else:
        location_setting.value = location_value

    db.session.commit()
    _save_user_meetup_preferences(user_id, stations)
    return jsonify({"ok": True})


@app.get("/api/safe_locations")
def api_safe_locations():
    stations_raw = (request.args.get("stations") or "").strip()
    if not stations_raw:
        return jsonify([])

    stations = []
    seen = set()
    for token in stations_raw.split(","):
        station = token.strip()
        if not station:
            continue
        key = station.casefold()
        if key in seen:
            continue
        seen.add(key)
        stations.append(station)

    if not stations:
        return jsonify([])

    placeholders = ",".join(["?"] * len(stations))
    conn = _get_main_conn()
    rows = conn.execute(
        f"""
        SELECT place_name, venue_type, address, lat, lng, station_name, walking_mins
          FROM safe_locations
         WHERE station_name IN ({placeholders})
         ORDER BY station_name, walking_mins ASC, place_name ASC
        """,
        tuple(stations),
    ).fetchall()
    conn.close()

    payload = [
        {
            "place_name": row["place_name"],
            "venue_type": row["venue_type"],
            "address": row["address"] or "",
            "lat": float(row["lat"]),
            "lng": float(row["lng"]),
            "station_name": row["station_name"],
            "walking_mins": row["walking_mins"],
        }
        for row in rows
    ]
    return jsonify(payload)


@app.post("/api/admin/login")
def api_admin_login():
    data = request.get_json(silent=True) or request.form
    admin_id = (data.get("adminId") or "").strip().lower()
    password = data.get("password") or ""

    if (admin_id == ADMIN_ID and password == ADMIN_PASSWORD) or (
        admin_id in ADMIN_EMAIL_PASSWORDS and password == ADMIN_EMAIL_PASSWORDS.get(admin_id)
    ):
        session["is_admin"] = True
        session["admin_id"] = admin_id
        _log_audit("roles", "admin_login", None, {"admin_id": admin_id})
        return jsonify({"ok": True})

    return jsonify({"ok": False, "error": "Invalid admin credentials"}), 401


@app.post("/api/admin/logout")
def api_admin_logout():
    if session.get("admin_id"):
        _log_audit("roles", "admin_logout", None, {"admin_id": session.get("admin_id")})
    session.pop("is_admin", None)
    session.pop("admin_id", None)
    return jsonify({"ok": True})


@app.get("/api/admin/overview")
def api_admin_overview():
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 401

    days = request.args.get("days")
    cutoff = None
    if days:
        try:
            cutoff = datetime.utcnow() - timedelta(days=int(days))
        except Exception:
            cutoff = None

    auth_query = AuthEvent.query
    circle_query = CircleSignup.query
    if cutoff:
        auth_query = auth_query.filter(AuthEvent.created_at >= cutoff)
        circle_query = circle_query.filter(CircleSignup.created_at >= cutoff)

    auth_events = auth_query.order_by(AuthEvent.created_at.desc()).limit(200).all()
    circle_signups = circle_query.order_by(CircleSignup.created_at.desc()).limit(200).all()

    def _u_name(uid):
        u = db.session.get(User, uid) if uid else None
        return u.full_name if u else ""

    conn = _get_main_conn()
    cur = conn.cursor()
    audit_where = ""
    params = []
    if cutoff:
        audit_where = "WHERE created_at >= ?"
        params.append(cutoff.isoformat())

    audit_rows = cur.execute(
        f"SELECT id, component, action, user_id, meta_json, created_at FROM audit_logs {audit_where} ORDER BY id DESC LIMIT 200",
        params,
    ).fetchall()

    def _count_with_cutoff(table: str, col: str = "created_at"):
        if cutoff:
            row = cur.execute(
                f"SELECT COUNT(*) AS c FROM {table} WHERE {col} >= ?",
                (cutoff.isoformat(),),
            ).fetchone()
        else:
            row = cur.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
        return row["c"] if row else 0

    posts_count = _count_with_cutoff("posts")
    comments_count = _count_with_cutoff("comments")
    matches_count = _count_with_cutoff("matches")
    messages_count = _count_with_cutoff("messages")
    challenge_entries_count = _count_with_cutoff("challenge_entries")
    reports_count = _count_with_cutoff("reports")
    conn.close()

    landmark_stats = {name: {"youth": 0, "senior": 0} for name in ONBOARDING_LANDMARKS}
    landmark_settings = UserSetting.query.filter_by(key="onboarding").all()
    for setting in landmark_settings:
        try:
            payload = json.loads(setting.value or "{}")
        except Exception:
            payload = {}
        member_type = (payload.get("memberType") or "").strip().lower()
        if not member_type:
            u = db.session.get(User, setting.user_id)
            member_type = (u.member_type or "").strip().lower() if u else ""
        group = "senior" if member_type in ("senior", "elderly") else "youth"
        for name in payload.get("landmarks") or []:
            if name in landmark_stats:
                landmark_stats[name][group] += 1

    landmark_rows = []
    top_youth = {"name": "", "count": 0}
    top_senior = {"name": "", "count": 0}
    top_overall = {"name": "", "count": 0}
    for name in ONBOARDING_LANDMARKS:
        youth_count = landmark_stats[name]["youth"]
        senior_count = landmark_stats[name]["senior"]
        total = youth_count + senior_count
        if youth_count > top_youth["count"]:
            top_youth = {"name": name, "count": youth_count}
        if senior_count > top_senior["count"]:
            top_senior = {"name": name, "count": senior_count}
        if total > top_overall["count"]:
            top_overall = {"name": name, "count": total}
        landmark_rows.append(
            {
                "name": name,
                "youth": youth_count,
                "senior": senior_count,
                "total": total,
            }
        )

    recent_activity = []
    for e in auth_events[:50]:
        recent_activity.append(
            {
                "type": f"auth:{e.event_type}",
                "source_table": "auth_events",
                "source_id": e.id,
                "user_id": e.user_id,
                "user_name": _u_name(e.user_id),
                "created_at": e.created_at.isoformat(),
                "summary": f"{e.event_type} - {e.email}",
            }
        )
    for r in audit_rows[:80]:
        recent_activity.append(
            {
                "type": "audit",
                "source_table": "audit_logs",
                "source_id": r["id"],
                "user_id": r["user_id"],
                "user_name": _u_name(r["user_id"]),
                "created_at": r["created_at"],
                "summary": f"{r['component']} / {r['action']}",
            }
        )
    recent_activity.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    recent_activity = recent_activity[:120]

    db_sources = []
    try:
        for p in (BASE_DIR.parent.parent / "database").glob("*.db"):
            db_sources.append(p.name)
    except Exception:
        pass

    total_users = User.query.count() if not cutoff else User.query.filter(User.created_at >= cutoff).count()
    total_auth_events = AuthEvent.query.count() if not cutoff else AuthEvent.query.filter(AuthEvent.created_at >= cutoff).count()
    total_circle_signups = CircleSignup.query.count() if not cutoff else CircleSignup.query.filter(CircleSignup.created_at >= cutoff).count()

    return jsonify(
        {
            "ok": True,
            "auth_events": [
                {
                    "id": e.id,
                    "created_at": e.created_at.isoformat(),
                    "event_type": e.event_type,
                    "user_id": e.user_id,
                    "user_name": _u_name(e.user_id),
                    "email": e.email,
                    "ip_address": e.ip_address,
                }
                for e in auth_events
            ],
            "circle_signups": [
                {
                    "id": s.id,
                    "created_at": s.created_at.isoformat(),
                    "user_id": s.user_id,
                    "user_name": _u_name(s.user_id),
                    "circle_title": s.circle_title,
                    "circle_time": s.circle_time,
                    "circle_duration": s.circle_duration,
                    "ip_address": s.ip_address,
                }
                for s in circle_signups
            ],
            "audit_logs": [
                {
                    "id": r["id"],
                    "component": r["component"],
                    "action": r["action"],
                    "user_id": r["user_id"],
                    "meta_json": r["meta_json"],
                    "created_at": r["created_at"],
                }
                for r in audit_rows
            ],
            "recent_activity": recent_activity,
            "db_sources": db_sources,
            "stats": {
                "total_users": total_users,
                "total_auth_events": total_auth_events,
                "total_circle_signups": total_circle_signups,
                "total_posts": posts_count,
                "total_comments": comments_count,
                "total_matches": matches_count,
                "total_messages": messages_count,
                "total_challenge_entries": challenge_entries_count,
                "total_reports": reports_count,
            },
            "landmark_stats": landmark_rows,
            "landmark_summary": {
                "top_youth": top_youth,
                "top_senior": top_senior,
                "top_overall": top_overall,
            },
        }
    )


@app.get("/api/admin/safety")
def api_admin_safety():
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 401
    conn = _get_main_conn()
    cur = conn.cursor()
    low_scores = cur.execute(
        """
        SELECT u.id, u.full_name, u.email, s.score, s.last_updated
        FROM safety_scores s
        JOIN users u ON u.id = s.user_id
        WHERE s.score < 40
        ORDER BY s.score ASC, s.last_updated DESC
        LIMIT 200
        """
    ).fetchall()
    reports = cur.execute(
        """
        SELECT id, user_id, reason, incident_date, details, status, created_at
        FROM reports
        ORDER BY id DESC
        LIMIT 200
        """
    ).fetchall()
    conn.close()
    return jsonify(
        {
            "ok": True,
            "low_scores": [
                {
                    "user_id": r["id"],
                    "full_name": r["full_name"],
                    "email": r["email"],
                    "score": r["score"],
                    "last_updated": r["last_updated"],
                }
                for r in low_scores
            ],
            "reports": [
                {
                    "id": r["id"],
                    "user_id": r["user_id"],
                    "reason": r["reason"],
                    "incident_date": r["incident_date"],
                    "details": r["details"],
                    "status": r["status"],
                    "created_at": r["created_at"],
                }
                for r in reports
            ],
        }
    )


@app.post("/api/admin/safety/adjust")
def api_admin_safety_adjust():
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 401
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    points = data.get("points")
    details = (data.get("details") or "").strip()
    if not user_id or points is None:
        return jsonify({"ok": False, "error": "user_id and points are required"}), 400
    score = _add_safety_event(int(user_id), "admin_adjust", int(points), details or "Manual adjustment")
    _log_audit("safety", "adjust_score", int(user_id), {"points": points, "details": details})
    return jsonify({"ok": True, "score": score})


@app.post("/api/admin/reports/<int:report_id>/status")
def api_admin_report_status(report_id: int):
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 401
    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").strip().lower()
    if status not in {"pending", "confirmed", "resolved"}:
        return jsonify({"ok": False, "error": "Invalid status"}), 400
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute("UPDATE reports SET status = ? WHERE id = ?", (status, report_id))
    conn.commit()
    conn.close()
    _log_audit("safety", "update_report_status", None, {"report_id": report_id, "status": status})
    return jsonify({"ok": True})


@app.get("/api/admin/export")
def api_admin_export():
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 401

    export_type = (request.args.get("type") or "").strip()
    headers = []
    rows = []

    export_format = (request.args.get("format") or "").strip().lower()

    if export_type == "auth_events":
        headers = ["id", "created_at", "event_type", "user_id", "email", "ip_address"]
        events = AuthEvent.query.order_by(AuthEvent.created_at.desc()).limit(2000).all()
        rows = [
            [e.id, e.created_at.isoformat(), e.event_type, e.user_id, e.email, e.ip_address]
            for e in events
        ]
    elif export_type == "circle_signups":
        headers = ["id", "created_at", "user_id", "circle_title", "circle_time", "circle_duration", "ip_address"]
        signups = CircleSignup.query.order_by(CircleSignup.created_at.desc()).limit(2000).all()
        rows = [
            [s.id, s.created_at.isoformat(), s.user_id, s.circle_title, s.circle_time, s.circle_duration, s.ip_address]
            for s in signups
        ]
    elif export_type == "audit_logs":
        headers = ["id", "created_at", "component", "action", "user_id", "meta_json"]
        conn = _get_main_conn()
        cur = conn.cursor()
        rows = [
            [r["id"], r["created_at"], r["component"], r["action"], r["user_id"], r["meta_json"]]
            for r in cur.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 2000").fetchall()
        ]
        conn.close()
    elif export_type == "reports":
        headers = ["id", "created_at", "user_id", "reason", "incident_date", "details", "status"]
        conn = _get_main_conn()
        cur = conn.cursor()
        rows = [
            [r["id"], r["created_at"], r["user_id"], r["reason"], r["incident_date"], r["details"], r["status"]]
            for r in cur.execute("SELECT * FROM reports ORDER BY id DESC LIMIT 2000").fetchall()
        ]
        conn.close()
    elif export_type == "challenge_entries":
        headers = ["id", "created_at", "challenge_id", "user_id", "author_name", "content", "image_url"]
        conn = _get_main_conn()
        cur = conn.cursor()
        rows = [
            [r["id"], r["created_at"], r["challenge_id"], r["user_id"], r["author_name"], r["content"], r["image_url"]]
            for r in cur.execute("SELECT * FROM challenge_entries ORDER BY id DESC LIMIT 2000").fetchall()
        ]
        conn.close()
    elif export_type == "overview":
        headers = ["metric", "value"]
        conn = _get_main_conn()
        cur = conn.cursor()
        stats = {
            "total_users": User.query.count(),
            "total_auth_events": AuthEvent.query.count(),
            "total_circle_signups": CircleSignup.query.count(),
            "total_posts": cur.execute("SELECT COUNT(*) AS c FROM posts").fetchone()["c"],
            "total_comments": cur.execute("SELECT COUNT(*) AS c FROM comments").fetchone()["c"],
            "total_matches": cur.execute("SELECT COUNT(*) AS c FROM matches").fetchone()["c"],
            "total_messages": cur.execute("SELECT COUNT(*) AS c FROM messages").fetchone()["c"],
            "total_challenge_entries": cur.execute("SELECT COUNT(*) AS c FROM challenge_entries").fetchone()["c"],
            "total_reports": cur.execute("SELECT COUNT(*) AS c FROM reports").fetchone()["c"],
        }
        rows = [[k, v] for k, v in stats.items()]
        conn.close()
    else:
        return jsonify({"ok": False, "error": "Invalid export type"}), 400

    def _csv_escape(val):
        if val is None:
            return ""
        text = str(val).replace('"', '""')
        return f"\"{text}\""

    if export_format == "xls":
        lines = ["\t".join(headers)]
        for row in rows:
            lines.append("\t".join(str(v if v is not None else "") for v in row))
        data = "\n".join(lines)
        return Response(
            data,
            mimetype="application/vnd.ms-excel",
            headers={"Content-Disposition": f"attachment; filename={export_type}.xls"},
        )
    csv_lines = [",".join(headers)]
    for row in rows:
        csv_lines.append(",".join(_csv_escape(v) for v in row))
    csv_data = "\n".join(csv_lines)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={export_type}.csv"},
    )


@app.post("/api/admin/bulk")
def api_admin_bulk():
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 401

    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").strip()
    conn = _get_main_conn()
    cur = conn.cursor()

    if action == "clear_matches":
        cur.execute("DELETE FROM messages")
        cur.execute("DELETE FROM matches")
        conn.commit()
        conn.close()
        _log_audit("admin", "bulk_clear_matches")
        return jsonify({"ok": True})

    if action == "clear_forum":
        cur.execute("DELETE FROM post_likes")
        cur.execute("DELETE FROM comments")
        cur.execute("DELETE FROM posts")
        conn.commit()
        conn.close()
        _log_audit("admin", "bulk_clear_forum")
        return jsonify({"ok": True})

    if action == "clear_reports":
        cur.execute("DELETE FROM reports")
        conn.commit()
        conn.close()
        _log_audit("admin", "bulk_clear_reports")
        return jsonify({"ok": True})
    if action == "clear_challenges":
        cur.execute("DELETE FROM challenge_entry_likes")
        cur.execute("DELETE FROM challenge_comments")
        cur.execute("DELETE FROM challenge_entries")
        conn.commit()
        conn.close()
        _log_audit("admin", "bulk_clear_challenges")
        return jsonify({"ok": True})

    conn.close()
    return jsonify({"ok": False, "error": "Invalid action"}), 400


@app.get("/api/admin/posts")
def api_admin_posts():
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 401
    conn = _get_main_conn()
    rows = conn.execute(
        "SELECT id, author, title, content, category, created_at FROM posts ORDER BY id DESC LIMIT 200"
    ).fetchall()
    conn.close()
    return jsonify({"ok": True, "posts": [dict(r) for r in rows]})


@app.get("/api/admin/challenge_entries")
def api_admin_challenge_entries():
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 401
    conn = _get_main_conn()
    rows = conn.execute(
        "SELECT id, challenge_id, user_id, author_name, content, image_url, created_at FROM challenge_entries ORDER BY id DESC LIMIT 200"
    ).fetchall()
    conn.close()
    return jsonify({"ok": True, "entries": [dict(r) for r in rows]})


@app.put("/api/admin/challenge_entries/<int:entry_id>")
def api_admin_challenge_entry_update(entry_id: int):
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 401
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    image_url = (data.get("image_url") or "").strip()
    if not content:
        return jsonify({"ok": False, "error": "Content is required"}), 400
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE challenge_entries SET content = ?, image_url = ? WHERE id = ?",
        (content, image_url or None, entry_id),
    )
    conn.commit()
    conn.close()
    _log_audit("admin", "challenge_entry_update", None, {"entry_id": entry_id})
    return jsonify({"ok": True})


@app.delete("/api/admin/challenge_entries/<int:entry_id>")
def api_admin_challenge_entry_delete(entry_id: int):
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 401
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM challenge_entry_likes WHERE entry_id = ?", (entry_id,))
    cur.execute("DELETE FROM challenge_comments WHERE entry_id = ?", (entry_id,))
    cur.execute("DELETE FROM challenge_entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
    _log_audit("admin", "challenge_entry_delete", None, {"entry_id": entry_id})
    return jsonify({"ok": True})


@app.put("/api/admin/posts/<int:post_id>")
def api_admin_post_update(post_id: int):
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 401
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"ok": False, "error": "Content is required"}), 400
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute("UPDATE posts SET content = ? WHERE id = ?", (content, post_id))
    conn.commit()
    conn.close()
    _log_audit("admin", "post_update", None, {"post_id": post_id})
    return jsonify({"ok": True})


@app.delete("/api/admin/posts/<int:post_id>")
def api_admin_post_delete(post_id: int):
    if not _require_admin():
        return jsonify({"ok": False, "error": "Not authorised"}), 401
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM post_likes WHERE post_id = ?", (post_id,))
    cur.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
    cur.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    _log_audit("admin", "post_delete", None, {"post_id": post_id})
    return jsonify({"ok": True})


@app.get("/api/achievements")
def api_achievements():
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    user = db.session.get(User, user_id)
    _ensure_ach_user(user)
    conn = _get_ach_conn()
    cur = conn.cursor()

    user_row = cur.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    points = user_row["total_points"]
    tier = _update_tier(points)
    cur.execute("UPDATE users SET current_tier = ? WHERE id = ?", (tier, user_id))
    user_row = cur.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    landmarks = []
    for lm in cur.execute(
        """SELECT l.*, ul.unlocked, ul.completed
           FROM landmarks l
           JOIN user_landmarks ul ON ul.landmark_id = l.id
           WHERE ul.user_id = ?
           ORDER BY l.id""",
        (user_id,),
    ).fetchall():
        opts = cur.execute(
            "SELECT option_text FROM landmark_options WHERE landmark_id = ? ORDER BY option_index",
            (lm["id"],),
        ).fetchall()
        landmarks.append(
            {
                "id": lm["id"],
                "name": lm["name"],
                "icon": lm["icon"],
                "x": lm["x"],
                "y": lm["y"],
                "story": lm["story"],
                "question": lm["question"],
                "options": [o["option_text"] for o in opts],
                "answer": lm["correct_answer"],
                "unlocked": bool(lm["unlocked"]),
                "completed": bool(lm["completed"]),
            }
        )

    quests = []
    for q in cur.execute(
        """SELECT q.*, uq.progress, uq.completed
           FROM quests q
           JOIN user_quests uq ON uq.quest_id = q.id
           WHERE uq.user_id = ?
           ORDER BY q.id""",
        (user_id,),
    ).fetchall():
        quests.append(
            {
                "id": q["id"],
                "title": q["title"],
                "description": q["description"],
                "reward": q["reward"],
                "total": q["total_required"],
                "progress": q["progress"],
                "completed": bool(q["completed"]),
            }
        )

    rewards = []
    redeemed_ids = {
        r["reward_id"]
        for r in cur.execute("SELECT reward_id FROM user_rewards WHERE user_id = ?", (user_id,)).fetchall()
    }
    for r in cur.execute("SELECT * FROM rewards WHERE is_active = 1 ORDER BY id").fetchall():
        if r["id"] in redeemed_ids:
            status = "redeemed"
        else:
            status = "available" if user_row["available_points"] >= r["cost"] else "locked"
        rewards.append(
            {
                "id": r["id"],
                "name": r["name"],
                "icon": r["icon"],
                "cost": r["cost"],
                "description": r["description"],
                "status": status,
            }
        )

    checkins = [
        row["checkin_date"]
        for row in cur.execute(
            "SELECT checkin_date FROM user_checkins WHERE user_id = ? ORDER BY checkin_date",
            (user_id,),
        ).fetchall()
    ]

    skills = []
    for s in cur.execute(
        """SELECT s.*, us.progress, us.completed
           FROM skills s
           JOIN user_skills us ON us.skill_id = s.id
           WHERE us.user_id = ?
           ORDER BY s.id""",
        (user_id,),
    ).fetchall():
        skills.append(
            {
                "id": s["id"],
                "name": s["name"],
                "description": s["description"],
                "required_count": s["required_count"],
                "parent_id": s["parent_id"],
                "category": s["category"],
                "level": s["level"],
                "icon": s["icon"],
                "reward_points": s["reward_points"],
                "progress": s["progress"],
                "completed": bool(s["completed"]),
            }
        )

    quests_completed = len([q for q in quests if q["completed"]])
    landmarks_completed = len([l for l in landmarks if l["completed"]])
    skills_completed = len([s for s in skills if s["completed"]])

    badges = {}
    for b in cur.execute("SELECT * FROM badges ORDER BY id").fetchall():
        requirement = b["requirement_type"]
        current = 0
        if requirement == "landmarks":
            current = landmarks_completed
        elif requirement == "quests":
            current = quests_completed
        elif requirement == "points":
            current = user_row["total_points"]
        elif requirement == "tier":
            current = user_row["current_tier"]
        elif requirement == "skills":
            current = skills_completed
        earned = 1 if current >= b["threshold"] else 0
        cur.execute(
            "UPDATE user_badges SET earned = ?, earned_at = CASE WHEN ?=1 THEN COALESCE(earned_at, ?) ELSE earned_at END WHERE user_id = ? AND badge_id = ?",
            (earned, earned, datetime.utcnow().isoformat(), user_id, b["id"]),
        )
        badges.setdefault(b["category"], []).append(
            {
                "id": b["id"],
                "name": b["name"],
                "icon": b["icon"],
                "description": b["description"],
                "threshold": b["threshold"],
                "earned": bool(earned),
                "current": current,
            }
        )

    leaderboard = [
        {
            "username": row["full_name"],
            "total_points": row["total_points"],
            "current_tier": row["current_tier"],
        }
        for row in cur.execute(
            "SELECT full_name, total_points, current_tier FROM users ORDER BY total_points DESC LIMIT 10"
        ).fetchall()
    ]

    conn.commit()
    conn.close()

    state = {
        "user": {
            "id": user_row["id"],
            "username": user_row["full_name"],
            "total_points": user_row["total_points"],
            "available_points": user_row["available_points"],
            "active_days": user_row["active_days"],
            "current_tier": user_row["current_tier"],
            "current_streak": user_row["current_streak"],
        },
        "landmarks": landmarks,
        "quests": quests,
        "rewards": rewards,
        "badges": badges,
        "leaderboard": leaderboard,
        "checkins": checkins,
        "skills": skills,
    }
    return jsonify({"ok": True, "data": state})


@app.post("/api/achievements/quests/<int:quest_id>/progress")
def api_achievements_quest_progress(quest_id: int):
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    user = db.session.get(User, user_id)
    _ensure_ach_user(user)
    conn = _get_ach_conn()
    cur = conn.cursor()
    quest = cur.execute(
        "SELECT q.reward, q.total_required, uq.progress, uq.completed FROM quests q JOIN user_quests uq ON uq.quest_id = q.id WHERE q.id = ? AND uq.user_id = ?",
        (quest_id, user_id),
    ).fetchone()
    if not quest:
        conn.close()
        return jsonify({"ok": False, "error": "Quest not found"}), 404
    progress = quest["progress"]
    completed = quest["completed"]
    was_completed = bool(completed)
    if not completed and progress < quest["total_required"]:
        progress += 1
        if progress >= quest["total_required"]:
            completed = 1
            cur.execute(
                "UPDATE users SET total_points = total_points + ?, available_points = available_points + ? WHERE id = ?",
                (quest["reward"], quest["reward"], user_id),
            )
    cur.execute(
        "UPDATE user_quests SET progress = ?, completed = ?, completed_at = CASE WHEN ?=1 THEN COALESCE(completed_at, ?) ELSE completed_at END WHERE user_id = ? AND quest_id = ?",
        (progress, completed, completed, datetime.utcnow().isoformat(), user_id, quest_id),
    )
    conn.commit()
    conn.close()
    if completed and not was_completed:
        _add_notification(
            user_id,
            "quest_complete",
            f"Quest completed! (+{quest['reward']} pts)",
            {"quest_id": quest_id},
        )
    return api_achievements()


@app.post("/api/achievements/rewards/<int:reward_id>/redeem")
def api_achievements_redeem_reward(reward_id: int):
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    user = db.session.get(User, user_id)
    _ensure_ach_user(user)
    conn = _get_ach_conn()
    cur = conn.cursor()
    reward = cur.execute("SELECT cost FROM rewards WHERE id = ? AND is_active = 1", (reward_id,)).fetchone()
    if not reward:
        conn.close()
        return jsonify({"ok": False, "error": "Reward not found"}), 404
    already = cur.execute(
        "SELECT id FROM user_rewards WHERE user_id = ? AND reward_id = ?",
        (user_id, reward_id),
    ).fetchone()
    if already:
        conn.close()
        return jsonify({"ok": False, "error": "Already redeemed"}), 400
    user_row = cur.execute("SELECT available_points FROM users WHERE id = ?", (user_id,)).fetchone()
    if user_row["available_points"] < reward["cost"]:
        conn.close()
        return jsonify({"ok": False, "error": "Not enough points"}), 400
    cur.execute(
        "INSERT INTO user_rewards (user_id, reward_id, redeemed_at) VALUES (?, ?, ?)",
        (user_id, reward_id, datetime.utcnow().isoformat()),
    )
    cur.execute(
        "UPDATE users SET available_points = available_points - ? WHERE id = ?",
        (reward["cost"], user_id),
    )
    conn.commit()
    conn.close()
    return api_achievements()


@app.post("/api/achievements/skills/<int:skill_id>/progress")
def api_achievements_skill_progress(skill_id: int):
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    user = db.session.get(User, user_id)
    _ensure_ach_user(user)
    conn = _get_ach_conn()
    cur = conn.cursor()
    skill = cur.execute(
        "SELECT s.name, s.required_count, s.reward_points, us.progress, us.completed FROM skills s JOIN user_skills us ON us.skill_id = s.id WHERE s.id = ? AND us.user_id = ?",
        (skill_id, user_id),
    ).fetchone()
    if not skill:
        conn.close()
        return jsonify({"ok": False, "error": "Skill not found"}), 404
    if skill["completed"]:
        conn.close()
        return api_achievements()
    progress = min(skill["progress"] + 1, skill["required_count"])
    completed = 1 if progress >= skill["required_count"] else 0
    cur.execute(
        "UPDATE user_skills SET progress = ?, completed = ?, completed_at = CASE WHEN ?=1 THEN COALESCE(completed_at, ?) ELSE completed_at END WHERE user_id = ? AND skill_id = ?",
        (progress, completed, completed, datetime.utcnow().isoformat(), user_id, skill_id),
    )
    if completed:
        cur.execute(
            "UPDATE users SET total_points = total_points + ?, available_points = available_points + ? WHERE id = ?",
            (skill["reward_points"], skill["reward_points"], user_id),
        )
        cur.execute(
            "INSERT INTO user_skill_rewards (user_id, skill_id, reward_points, rewarded_at) VALUES (?, ?, ?, ?)",
            (user_id, skill_id, skill["reward_points"], datetime.utcnow().isoformat()),
        )
    conn.commit()
    conn.close()
    if completed:
        _increment_quest_progress(user_id, 3)
        _add_notification(
            user_id,
            "skill_complete",
            f"Skill completed: {skill['name']} (+{skill['reward_points']} pts)",
            {"skill_id": skill_id},
        )
    return api_achievements()


@app.post("/api/achievements/landmarks/<int:landmark_id>/unlock")
def api_achievements_landmark_unlock(landmark_id: int):
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    user = db.session.get(User, user_id)
    _ensure_ach_user(user)
    conn = _get_ach_conn()
    cur = conn.cursor()
    order = cur.execute("SELECT id FROM landmarks ORDER BY id").fetchall()
    ids = [row["id"] for row in order]
    if landmark_id not in ids:
        conn.close()
        return jsonify({"ok": False, "error": "Landmark not found"}), 404
    index = ids.index(landmark_id)
    points_needed = (index + 1) * 1000
    user_row = cur.execute("SELECT total_points FROM users WHERE id = ?", (user_id,)).fetchone()
    if user_row["total_points"] < points_needed:
        conn.close()
        return jsonify({"ok": False, "error": "Not enough points"}), 400
    cur.execute(
        "UPDATE user_landmarks SET unlocked = 1, unlocked_at = COALESCE(unlocked_at, ?) WHERE user_id = ? AND landmark_id = ?",
        (datetime.utcnow().isoformat(), user_id, landmark_id),
    )
    conn.commit()
    conn.close()
    return api_achievements()


@app.post("/api/achievements/landmarks/<int:landmark_id>/complete")
def api_achievements_landmark_complete(landmark_id: int):
    user_id = _require_login()
    if not user_id:
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    user = db.session.get(User, user_id)
    _ensure_ach_user(user)
    conn = _get_ach_conn()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT completed FROM user_landmarks WHERE user_id = ? AND landmark_id = ?",
        (user_id, landmark_id),
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({"ok": False, "error": "Landmark not found"}), 404
    awarded = 0
    if not row["completed"]:
        awarded = 200
        cur.execute(
            "UPDATE user_landmarks SET completed = 1, completed_at = COALESCE(completed_at, ?) WHERE user_id = ? AND landmark_id = ?",
            (datetime.utcnow().isoformat(), user_id, landmark_id),
        )
        cur.execute(
            "UPDATE users SET total_points = total_points + ?, available_points = available_points + ? WHERE id = ?",
            (awarded, awarded, user_id),
        )
    conn.commit()
    conn.close()
    data = api_achievements().get_json()
    return jsonify({"ok": True, "data": data["data"], "awarded_points": awarded})



ACH_DB_PATH = DB_PATH


def _get_ach_conn():
    conn = sqlite3.connect(ACH_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _get_main_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=3000;")
    return conn


def _init_home_schema():
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS home_explore_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT 'orange',
            link TEXT
        );
        """
    )
    cols = {row["name"] for row in cur.execute("PRAGMA table_info(home_explore_cards)").fetchall()}
    if "link" not in cols:
        cur.execute("ALTER TABLE home_explore_cards ADD COLUMN link TEXT")
    count = cur.execute("SELECT COUNT(*) AS c FROM home_explore_cards").fetchone()["c"]
    if count != 4:
        cur.execute("DELETE FROM home_explore_cards")
        cur.executemany(
            "INSERT INTO home_explore_cards (title, description, icon, color, link) VALUES (?, ?, ?, ?, ?)",
            [
                ("Wisdom Forum", "Ask questions and share wisdom", "ðŸ’¡", "orange", "/dashboard#tab-wisdom-forum"),
                ("Matching", "Find people with shared interests", "ðŸ¤", "teal", "/dashboard#tab-matches"),
                ("Learning Circles", "Join group sessions", "ðŸ“š", "orange", "/dashboard#tab-learning-circles"),
                ("Achievements", "Track quests and badges", "ðŸ…", "teal", "/achievements"),
            ],
        )
    else:
        cur.execute(
            """
            UPDATE home_explore_cards
               SET link = CASE
                   WHEN title = 'Wisdom Forum' THEN '/dashboard#tab-wisdom-forum'
                   WHEN title = 'Matching' THEN '/dashboard#tab-matches'
                   WHEN title = 'Learning Circles' THEN '/dashboard#tab-learning-circles'
                   WHEN title = 'Achievements' THEN '/achievements'
                   ELSE link
               END
             WHERE link IS NULL OR link = ''
            """
        )
    conn.commit()
    conn.close()


def _list_home_explore_cards():
    conn = _get_main_conn()
    rows = conn.execute(
        "SELECT id, title, description, icon, color, link FROM home_explore_cards ORDER BY id ASC"
    ).fetchall()
    conn.close()
    return rows


def _init_meetup_schema():
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS safe_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_name TEXT NOT NULL,
            place_name TEXT NOT NULL,
            venue_type TEXT NOT NULL,
            address TEXT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            walking_mins INTEGER,
            UNIQUE(station_name, place_name)
        );

        CREATE TABLE IF NOT EXISTS user_meetup_preferences (
            user_id INTEGER NOT NULL,
            station_name TEXT NOT NULL,
            PRIMARY KEY (user_id, station_name),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )

    seed_rows = [
        ("Bishan", "Junction 8 Cafe", "cafe", "9 Bishan Place, Singapore 579837", 1.3509, 103.8487, 4),
        ("Bishan", "Bishan Public Library", "library", "5 Bishan Place, Singapore 579841", 1.3507, 103.8489, 5),
        ("Bishan", "Bishan Community Club", "community_club", "51 Bishan Street 13, Singapore 579799", 1.3516, 103.8499, 6),
        ("Siglap", "Siglap South Community Centre", "community_club", "6 Palm Road, Singapore 456541", 1.3090, 103.9270, 7),
        ("Siglap", "Bedok Public Library", "library", "11 Bedok North Street 1, Singapore 469662", 1.3269, 103.9305, 8),
        ("Marine Parade", "Marine Parade Public Library", "library", "278 Marine Parade Road, Singapore 449282", 1.3027, 103.9070, 6),
        ("Marine Parade", "Marine Parade Community Club", "community_club", "278 Marine Parade Road, Singapore 449282", 1.3028, 103.9066, 5),
        ("Tanjong Katong", "Katong Community Centre", "community_club", "51 Kampong Arang Road, Singapore 438178", 1.3057, 103.8862, 7),
        ("Tanjong Katong", "Geylang East Public Library", "library", "50 Geylang East Avenue 1, Singapore 389777", 1.3183, 103.8856, 9),
        ("Buona Vista", "Buona Vista Community Club", "community_club", "36 Holland Drive, Singapore 270036", 1.3074, 103.7888, 6),
        ("Buona Vista", "The Star Vista", "mall", "1 Vista Exchange Green, Singapore 138617", 1.3066, 103.7890, 4),
        ("Caldecott", "Toa Payoh West Community Club", "community_club", "200 Lorong 2 Toa Payoh, Singapore 319642", 1.3357, 103.8502, 9),
        ("Caldecott", "Lornie Nature Corridor Gate", "park", "Lornie Road, Singapore", 1.3437, 103.8179, 10),
        ("Toa Payoh", "Toa Payoh Public Library", "library", "6 Toa Payoh Central, Singapore 319191", 1.3320, 103.8474, 5),
        ("Bugis", "National Library", "library", "100 Victoria Street, Singapore 188064", 1.2966, 103.8545, 5),
        ("City Hall", "Raffles City", "mall", "252 North Bridge Road, Singapore 179103", 1.2932, 103.8526, 4),
    ]
    cur.executemany(
        """
        INSERT OR IGNORE INTO safe_locations
            (station_name, place_name, venue_type, address, lat, lng, walking_mins)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        seed_rows,
    )

    cur.execute(
        """
        UPDATE safe_locations
           SET station_name = 'Bishan'
         WHERE lower(place_name) = lower('Junction 8 Cafe')
        """
    )
    cur.execute(
        """
        DELETE FROM safe_locations
         WHERE lower(place_name) = lower('Junction 8 Cafe')
           AND station_name <> 'Bishan'
        """
    )
    conn.commit()
    conn.close()


def _init_challenges_schema():
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS weekly_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            reward_points INTEGER NOT NULL,
            week_label TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS challenge_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            content TEXT NOT NULL,
            image_url TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (challenge_id) REFERENCES weekly_challenges(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS challenge_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (entry_id) REFERENCES challenge_entries(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS challenge_entry_likes (
            entry_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (entry_id, user_id),
            FOREIGN KEY (entry_id) REFERENCES challenge_entries(id) ON DELETE CASCADE
        );
        """
    )
    count = cur.execute("SELECT COUNT(*) AS c FROM weekly_challenges").fetchone()["c"]
    if count == 0:
        cur.execute(
            "INSERT INTO weekly_challenges (title, description, reward_points, week_label, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                "ðŸ¥Ÿ Recreate Your Childhood Snack",
                "Share a photo or story of a snack you loved as a child. Tell us the memories behind it!",
                20,
                "Week 12 Challenge",
                _utc_now_iso(),
            ),
        )
    conn.commit()
    conn.close()


def _init_reports_schema():
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            incident_date TEXT NOT NULL,
            details TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
        """
    )
    cols = {row["name"] for row in cur.execute("PRAGMA table_info(reports)").fetchall()}
    if "status" not in cols:
        cur.execute("ALTER TABLE reports ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'")
    conn.commit()
    conn.close()


def _init_safety_schema():
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS safety_scores (
            user_id INTEGER PRIMARY KEY,
            score INTEGER NOT NULL,
            last_updated TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS safety_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            points INTEGER NOT NULL,
            ref_id TEXT,
            details TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_safety_events_user
            ON safety_events(user_id, created_at);
        """
    )
    conn.commit()
    conn.close()


def _init_wellbeing_schema():
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS mood_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood TEXT NOT NULL,
            reason TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_mood_user_created
            ON mood_checkins(user_id, created_at);

        CREATE TABLE IF NOT EXISTS wellbeing_recos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood TEXT NOT NULL,
            reco_type TEXT NOT NULL,
            reco_title TEXT NOT NULL,
            reco_link TEXT,
            clicked INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_recos_user_created
            ON wellbeing_recos(user_id, created_at);

        CREATE TABLE IF NOT EXISTS wellbeing_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            prompt TEXT,
            gratitude TEXT,
            reflection TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_wellbeing_journal_user_created
            ON wellbeing_journal(user_id, created_at);
        """
    )
    conn.commit()
    conn.close()


def _init_partner_schema():
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            logo_url TEXT,
            description TEXT,
            verified INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS circle_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            circle_title TEXT NOT NULL,
            partner_id INTEGER,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 20,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'registered',
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


def _init_scrapbook_schema():
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS scrapbook_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_user_id INTEGER NOT NULL,
            related_user_id INTEGER,
            circle_title TEXT,
            entry_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            visibility TEXT NOT NULL DEFAULT 'private',
            mood_tag TEXT,
            location TEXT,
            pinned INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS scrapbook_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            media_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_by INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS scrapbook_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reaction_type TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS scrapbook_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            comment_text TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS scrapbook_stats (
            user_id INTEGER PRIMARY KEY,
            total_entries INTEGER NOT NULL DEFAULT 0,
            weekly_streak INTEGER NOT NULL DEFAULT 0,
            last_entry_at TEXT
        );
        CREATE TABLE IF NOT EXISTS storybook_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            place TEXT,
            event TEXT,
            feeling TEXT,
            lesson TEXT,
            media_url TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trusted_viewers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_user_id INTEGER NOT NULL,
            viewer_email TEXT NOT NULL,
            access_key TEXT NOT NULL,
            can_view_mood INTEGER NOT NULL DEFAULT 1,
            can_view_activity INTEGER NOT NULL DEFAULT 1,
            can_view_alerts INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        """
    )
    cols = {row["name"] for row in cur.execute("PRAGMA table_info(scrapbook_entries)").fetchall()}
    if "mood_tag" not in cols:
        cur.execute("ALTER TABLE scrapbook_entries ADD COLUMN mood_tag TEXT")
    if "location" not in cols:
        cur.execute("ALTER TABLE scrapbook_entries ADD COLUMN location TEXT")
    if "pinned" not in cols:
        cur.execute("ALTER TABLE scrapbook_entries ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0")
    conn.commit()
    conn.close()


def _init_avatar_schema():
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_avatar (
            user_id INTEGER PRIMARY KEY,
            config_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            snapshot_path TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def _init_admin_schema():
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            component TEXT NOT NULL,
            action TEXT NOT NULL,
            user_id INTEGER,
            meta_json TEXT,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


def _init_meta_schema():
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    conn.commit()
    conn.close()


def _init_notifications_schema():
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            meta_json TEXT,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_notifications_user
            ON notifications(user_id, is_read, created_at);
        """
    )
    count = cur.execute("SELECT COUNT(*) AS c FROM notifications").fetchone()["c"]
    if count == 0:
        cur.execute(
            "INSERT INTO notifications (user_id, type, message, meta_json, is_read, created_at) VALUES (?, ?, ?, ?, 1, ?)",
            (None, "system", "Welcome to Re:Connect SG! New weekly challenges are live.", json.dumps({}), _utc_now_iso()),
        )
    conn.commit()
    conn.close()


def _week_start(dt: datetime) -> datetime:
    return (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def _ensure_safety_score(user_id: int) -> int:
    conn = _get_main_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT score FROM safety_scores WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        conn.close()
        return int(row["score"])
    score = 50
    cur.execute(
        "INSERT INTO safety_scores (user_id, score, last_updated) VALUES (?, ?, ?)",
        (user_id, score, _utc_now_iso()),
    )
    conn.commit()
    conn.close()
    return score


def _recompute_safety_score(user_id: int) -> int:
    conn = _get_main_conn()
    cur = conn.cursor()
    base = 50
    total = cur.execute(
        "SELECT COALESCE(SUM(points), 0) AS total FROM safety_events WHERE user_id = ?", (user_id,)
    ).fetchone()["total"]
    score = max(0, min(100, base + int(total)))
    cur.execute(
        "INSERT OR REPLACE INTO safety_scores (user_id, score, last_updated) VALUES (?, ?, ?)",
        (user_id, score, _utc_now_iso()),
    )
    conn.commit()
    conn.close()
    return score


def _add_safety_event(user_id: int, event_type: str, points: int, details: str = None, ref_id: str = None) -> int:
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO safety_events (user_id, event_type, points, ref_id, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, event_type, int(points), ref_id, details, _utc_now_iso()),
    )
    conn.commit()
    conn.close()
    return _recompute_safety_score(user_id)


def _get_safety_snapshot(user_id: int) -> dict:
    score = _ensure_safety_score(user_id)
    conn = _get_main_conn()
    cur = conn.cursor()
    events = cur.execute(
        """
        SELECT event_type, points, details, created_at
        FROM safety_events
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    tier = "green" if score >= 80 else ("yellow" if score >= 40 else "red")
    return {
        "score": score,
        "tier": tier,
        "trusted": score >= 80,
        "events": [
            {
                "event_type": e["event_type"],
                "points": e["points"],
                "details": e["details"] or "",
                "created_at": e["created_at"],
            }
            for e in events
        ],
    }


def _partner_circle_keywords():
    return ["dbs", "singtel", "scam", "govtech", "spf"]


def _is_partner_circle(title: str) -> bool:
    if not title:
        return False
    lowered = title.lower()
    return any(k in lowered for k in _partner_circle_keywords())


def _normalize_mood(mood: str) -> str:
    m = (mood or "").strip().lower()
    if m == "lonely":
        return "sad"
    if m in WELLBEING_MOOD_SCORES:
        return m
    return "neutral"


def _format_mood(mood: str) -> str:
    meta = WELLBEING_MOOD_META.get(_normalize_mood(mood), WELLBEING_MOOD_META["neutral"])
    return f"{meta['emoji']} {meta['label']}"


def _parse_iso_dt(raw: str):
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", ""))
    except Exception:
        return None


def _humanize_relative_time(raw: str) -> str:
    dt = _parse_iso_dt(raw)
    if not dt:
        return ""
    delta = datetime.utcnow() - dt
    mins = int(max(delta.total_seconds(), 0) // 60)
    if mins < 60:
        return f"{mins} min ago" if mins != 1 else "1 min ago"
    hrs = mins // 60
    if hrs < 24:
        return f"{hrs} hr ago" if hrs == 1 else f"{hrs} hrs ago"
    days = hrs // 24
    return f"{days} day ago" if days == 1 else f"{days} days ago"


def _get_weekly_checkin(user_id: int, now: datetime = None):
    now = now or datetime.utcnow()
    start = _week_start(now)
    end = start + timedelta(days=7)
    conn = _get_main_conn()
    cur = conn.cursor()
    row = cur.execute(
        """
        SELECT id, mood, reason, notes, created_at
        FROM mood_checkins
        WHERE user_id = ? AND created_at >= ? AND created_at < ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id, start.isoformat(), end.isoformat()),
    ).fetchone()
    conn.close()
    return row


def _get_latest_checkin(user_id: int):
    conn = _get_main_conn()
    cur = conn.cursor()
    row = cur.execute(
        """
        SELECT id, mood, reason, notes, created_at
        FROM mood_checkins
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    conn.close()
    return row


def _get_recent_checkins(user_id: int, limit: int = 8):
    conn = _get_main_conn()
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT mood, reason, notes, created_at
        FROM mood_checkins
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    conn.close()
    return rows


def _activity_snapshot(user_id: int):
    conn = _get_main_conn()
    cur = conn.cursor()
    user_row = cur.execute("SELECT full_name FROM users WHERE id = ?", (user_id,)).fetchone()
    full_name = (user_row["full_name"] if user_row else "") or ""
    now = datetime.utcnow()
    week_start = _week_start(now).isoformat()
    circles = cur.execute(
        "SELECT COUNT(*) AS c FROM circle_signups WHERE user_id = ? AND created_at >= ?",
        (user_id, week_start),
    ).fetchone()["c"]
    messages = cur.execute(
        "SELECT COUNT(*) AS c FROM messages WHERE sender = ? AND created_at >= ?",
        (full_name, week_start),
    ).fetchone()["c"] if full_name else 0
    challenges = cur.execute(
        "SELECT COUNT(*) AS c FROM challenge_entries WHERE user_id = ? AND created_at >= ?",
        (user_id, week_start),
    ).fetchone()["c"]
    conn.close()
    return {"circles": int(circles), "messages": int(messages), "challenges": int(challenges)}


def _trend_from_checkins(rows: list) -> dict:
    if not rows:
        return {"arrow": "âž¡", "label": "Stable", "delta": 0}
    scores = [WELLBEING_MOOD_SCORES.get(_normalize_mood(r["mood"]), 3) for r in rows]
    recent = scores[:7]
    prev = scores[7:14]
    if not prev:
        prev = recent
    recent_avg = sum(recent) / max(len(recent), 1)
    prev_avg = sum(prev) / max(len(prev), 1)
    delta = round(recent_avg - prev_avg, 2)
    if delta >= 0.3:
        return {"arrow": "â¬†", "label": "Improving", "delta": delta}
    if delta <= -0.3:
        return {"arrow": "â¬‡", "label": "Declining", "delta": delta}
    return {"arrow": "âž¡", "label": "Stable", "delta": delta}


def _emotion_breakdown(rows: list) -> list:
    base = {k: 0 for k in WELLBEING_MOOD_META.keys()}
    for r in rows:
        base[_normalize_mood(r["mood"])] = base.get(_normalize_mood(r["mood"]), 0) + 1
    total = sum(base.values()) or 1
    return [
        {
            "mood": mood,
            "label": WELLBEING_MOOD_META[mood]["label"],
            "emoji": WELLBEING_MOOD_META[mood]["emoji"],
            "count": count,
            "pct": round((count / total) * 100),
        }
        for mood, count in base.items()
    ]


def _line_points_30d(rows: list) -> list:
    now = datetime.utcnow()
    by_day = {}
    for r in rows:
        dt = _parse_iso_dt(r["created_at"])
        if not dt:
            continue
        day_key = dt.date().isoformat()
        by_day.setdefault(day_key, []).append(WELLBEING_MOOD_SCORES.get(_normalize_mood(r["mood"]), 3))
    points = []
    for offset in range(29, -1, -1):
        day = (now - timedelta(days=offset)).date()
        vals = by_day.get(day.isoformat(), [])
        avg = round(sum(vals) / len(vals), 2) if vals else None
        points.append({"day": day.isoformat(), "value": avg})
    return points


def _mood_points_7d(rows: list) -> list:
    now = datetime.utcnow().date()
    by_day = {}
    for r in rows:
        dt = _parse_iso_dt(r["created_at"])
        if not dt:
            continue
        key = dt.date().isoformat()
        by_day.setdefault(key, []).append(WELLBEING_MOOD_SCORES.get(_normalize_mood(r["mood"]), 3))
    points = []
    for offset in range(6, -1, -1):
        day = now - timedelta(days=offset)
        vals = by_day.get(day.isoformat(), [])
        avg = round(sum(vals) / len(vals), 2) if vals else None
        rounded = int(round(avg)) if isinstance(avg, (int, float)) else 3
        mood_key = next((k for k, s in WELLBEING_MOOD_SCORES.items() if s == rounded), "neutral")
        points.append(
            {
                "day": day.isoformat(),
                "day_label": day.strftime("%a"),
                "value": avg,
                "emoji": WELLBEING_MOOD_META[mood_key]["emoji"] if vals else "â€¢",
            }
        )
    return points


def _daily_activity_7d(user_id: int) -> list:
    conn = _get_main_conn()
    cur = conn.cursor()
    user_row = cur.execute("SELECT full_name FROM users WHERE id = ?", (user_id,)).fetchone()
    full_name = (user_row["full_name"] if user_row else "") or ""
    start = (datetime.utcnow().date() - timedelta(days=6)).isoformat()
    circles_rows = cur.execute(
        "SELECT substr(created_at, 1, 10) AS d, COUNT(*) AS c FROM circle_signups WHERE user_id = ? AND created_at >= ? GROUP BY d",
        (user_id, start),
    ).fetchall()
    msg_rows = cur.execute(
        "SELECT substr(created_at, 1, 10) AS d, COUNT(*) AS c FROM messages WHERE sender = ? AND created_at >= ? GROUP BY d",
        (full_name, start),
    ).fetchall() if full_name else []
    challenge_rows = cur.execute(
        "SELECT substr(created_at, 1, 10) AS d, COUNT(*) AS c FROM challenge_entries WHERE user_id = ? AND created_at >= ? GROUP BY d",
        (user_id, start),
    ).fetchall()
    conn.close()

    merged = {}
    for row in circles_rows:
        merged[row["d"]] = merged.get(row["d"], 0) + int(row["c"]) * 2
    for row in msg_rows:
        merged[row["d"]] = merged.get(row["d"], 0) + int(row["c"])
    for row in challenge_rows:
        merged[row["d"]] = merged.get(row["d"], 0) + int(row["c"]) * 3

    out = []
    for offset in range(6, -1, -1):
        day = (datetime.utcnow().date() - timedelta(days=offset))
        raw = int(merged.get(day.isoformat(), 0))
        intensity = min(5, raw)
        out.append(
            {
                "day": day.isoformat(),
                "day_label": day.strftime("%a"),
                "value": raw,
                "intensity": intensity,
            }
        )
    return out


def _social_energy(activity: dict) -> dict:
    score = int(min(100, activity["circles"] * 20 + activity["messages"] * 2 + activity["challenges"] * 18))
    if score >= 70:
        level = "High"
        filled = 5
    elif score >= 40:
        level = "Medium"
        filled = 3
    elif score >= 15:
        level = "Low"
        filled = 2
    else:
        level = "Very Low"
        filled = 1
    return {"score": score, "level": level, "filled": filled, "total": 5}


def _risk_status(rows: list) -> dict:
    if not rows:
        return {"level": "low", "show": False, "message": ""}
    recent = [_normalize_mood(r["mood"]) for r in rows[:5]]
    negative = sum(1 for m in recent if m in {"stressed", "sad"})
    streak = 0
    for mood in recent:
        if mood in {"stressed", "sad"}:
            streak += 1
        else:
            break
    if streak >= 3 or negative >= 4:
        return {
            "level": "high",
            "show": True,
            "message": "We are here for you. Explore support circles or message a buddy.",
        }
    if streak >= 2 or negative >= 3:
        return {
            "level": "medium",
            "show": True,
            "message": "You seem a bit low lately. A small social step can help.",
        }
    return {"level": "low", "show": False, "message": ""}


def _build_wellbeing_recos(mood: str):
    mood = _normalize_mood(mood)
    if mood in {"sad", "stressed"}:
        return [
            {"type": "circle", "title": "Join a Support Circle", "link": "/learning-circles"},
            {"type": "match", "title": "Message a Buddy Match", "link": "/messages"},
            {"type": "forum", "title": "Read encouraging stories", "link": "/forum"},
        ]
    if mood == "neutral":
        return [
            {"type": "challenge", "title": "Try this week's challenge", "link": "/challenges"},
            {"type": "circle", "title": "Join one learning circle", "link": "/learning-circles"},
            {"type": "forum", "title": "Post in the Wisdom Forum", "link": "/forum"},
        ]
    return [
        {"type": "forum", "title": "Share a win in the forum", "link": "/forum"},
        {"type": "circle", "title": "Host or join a circle", "link": "/learning-circles"},
        {"type": "match", "title": "Encourage a connection", "link": "/messages"},
    ]


def _store_wellbeing_recos(user_id: int, mood: str, recos: list):
    conn = _get_main_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM wellbeing_recos WHERE user_id = ?", (user_id,))
    for r in recos:
        norm_mood = _normalize_mood(mood)
        cur.execute(
            """
            INSERT INTO wellbeing_recos (user_id, mood, reco_type, reco_title, reco_link, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, norm_mood, r["type"], r["title"], r.get("link"), _utc_now_iso()),
        )
    conn.commit()
    conn.close()


def _load_wellbeing_recos(user_id: int):
    conn = _get_main_conn()
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT reco_type, reco_title, reco_link, created_at
        FROM wellbeing_recos
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 6
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [
        {
            "type": r["reco_type"],
            "title": r["reco_title"],
            "link": r["reco_link"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def _get_scrapbook_settings(user_id: int) -> dict:
    settings = _get_user_settings_map(user_id)
    theme = (settings.get("scrapbook_theme") or "vintage").strip().lower()
    view = (settings.get("scrapbook_view") or "book").strip().lower()
    return {"theme": theme, "view": view}


def _set_scrapbook_settings(user_id: int, theme: str = None, view: str = None):
    if theme:
        _set_user_setting(user_id, "scrapbook_theme", theme)
    if view:
        _set_user_setting(user_id, "scrapbook_view", view)


def _wellbeing_insight(user_id: int) -> str:
    rows = _get_recent_checkins(user_id, limit=12)
    if len(rows) < 2:
        return ""
    moods = [_normalize_mood(r["mood"]) for r in rows[:3]]
    if moods[:2] == ["sad", "sad"] or moods[:2] == ["stressed", "stressed"]:
        return "You have had a tough streak. Try a low-pressure social activity today."
    trend = _trend_from_checkins(rows)
    if trend["label"] == "Improving":
        return "Your mood trend is improving in the last 7 days."
    if trend["label"] == "Declining":
        return "Your mood trend dipped this week. A buddy message may help."
    return "Your mood is stable this week."


def _wellbeing_score(rows: list, activity: dict) -> int:
    mood_vals = [WELLBEING_MOOD_SCORES.get(_normalize_mood(r["mood"]), 3) for r in rows[:14]]
    mood_avg = (sum(mood_vals) / len(mood_vals)) if mood_vals else 3
    mood_component = ((mood_avg - 1) / 4) * 60
    engagement_raw = activity["circles"] * 6 + activity["messages"] * 1.2 + activity["challenges"] * 8
    engagement_component = min(30, engagement_raw)
    checkin_days = len({_parse_iso_dt(r["created_at"]).date().isoformat() for r in rows[:7] if _parse_iso_dt(r["created_at"])})
    consistency_component = min(10, checkin_days * 2)
    score = int(round(mood_component + engagement_component + consistency_component))
    return max(0, min(100, score))


def _wellbeing_badges(rows: list, activity: dict) -> list:
    badges = []
    if activity["messages"] >= 10:
        badges.append({"name": "Active Listener", "unlocked": True})
    if activity["circles"] >= 2:
        badges.append({"name": "Community Helper", "unlocked": True})
    positive = sum(1 for r in rows[:14] if _normalize_mood(r["mood"]) in {"happy", "good"})
    if positive >= 7:
        badges.append({"name": "Positivity Builder", "unlocked": True})
    if not badges:
        badges = [
            {"name": "Positivity Builder", "unlocked": False},
            {"name": "Active Listener", "unlocked": False},
            {"name": "Community Helper", "unlocked": False},
        ]
    return badges


def _wellbeing_analytics(user_id: int) -> dict:
    rows = _get_recent_checkins(user_id, limit=60)
    activity = _activity_snapshot(user_id)
    daily_activity = _daily_activity_7d(user_id)
    trend = _trend_from_checkins(rows)
    breakdown = _emotion_breakdown(rows[:30])
    weekly_breakdown = _emotion_breakdown(rows[:7] if rows else [])
    score = _wellbeing_score(rows, activity)
    risk = _risk_status(rows)
    latest_mood = _normalize_mood(rows[0]["mood"]) if rows else "neutral"
    recommendations = _build_wellbeing_recos(latest_mood)
    insights = []
    if trend["label"] == "Improving":
        insights.append("Your mood is improving compared to the previous week.")
    elif trend["label"] == "Declining":
        insights.append("Your mood trend dipped this week. A quick check-in with a buddy may help.")
    else:
        insights.append("Your mood trend is steady this week.")
    if activity["circles"] > 0 and activity["messages"] > 0:
        insights.append("You tend to feel better on days with social activity.")
    if activity["messages"] == 0:
        insights.append("You have not messaged anyone this week. A short hello can boost connection.")
    if risk["level"] == "high":
        insights.append("You have had repeated low moods. Consider support circles and trusted contacts.")
    while len(insights) < 3:
        insights.append("Small daily reflections can improve emotional awareness over time.")
    return {
        "trend": trend,
        "activity": activity,
        "daily_activity_7d": daily_activity,
        "social_energy": _social_energy(activity),
        "emotion_breakdown": breakdown,
        "weekly_distribution": weekly_breakdown,
        "line_points_30d": _line_points_30d(rows),
        "mood_points_7d": _mood_points_7d(rows),
        "recommendations": recommendations,
        "insights": insights[:3],
        "risk": risk,
        "score": score,
        "badges": _wellbeing_badges(rows, activity),
    }


def _wellbeing_nudge(user_id: int, analytics: dict = None) -> str:
    data = analytics or _wellbeing_analytics(user_id)
    activity = data["activity"]
    trend = data["trend"]["label"]
    if activity["circles"] > 0 and trend == "Improving":
        return "You feel happier on days you join Learning Circles."
    if activity["messages"] == 0 and activity["circles"] == 0:
        return "You have not interacted this week. Say hi to a buddy?"
    if data["risk"]["show"]:
        return "We are here for you. Explore support circles when ready."
    return "Keep your momentum going with one meaningful interaction today."


def _log_audit(component: str, action: str, user_id: int = None, meta: dict = None) -> None:
    try:
        conn = _get_main_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO audit_logs (component, action, user_id, meta_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                component,
                action,
                user_id,
                json.dumps(meta or {}),
                _utc_now_iso(),
            ),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _add_notification(user_id: int, notif_type: str, message: str, meta: dict = None) -> None:
    try:
        conn = _get_main_conn()
        conn.execute(
            "INSERT INTO notifications (user_id, type, message, meta_json, is_read, created_at) VALUES (?, ?, ?, ?, 0, ?)",
            (user_id, notif_type, message, json.dumps(meta or {}), _utc_now_iso()),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _get_current_challenge():
    conn = _get_main_conn()
    row = conn.execute(
        "SELECT id, title, description, reward_points, week_label, created_at FROM weekly_challenges ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return row


def _list_challenge_entries(challenge_id: int):
    conn = _get_main_conn()
    rows = conn.execute(
        """SELECT id, challenge_id, user_id, author_name, content, image_url, created_at
           FROM challenge_entries
           WHERE challenge_id = ?
           ORDER BY id DESC""",
        (challenge_id,),
    ).fetchall()
    conn.close()
    return rows


def _list_entry_comments(entry_id: int):
    conn = _get_main_conn()
    rows = conn.execute(
        """SELECT id, entry_id, user_id, author_name, content, created_at
           FROM challenge_comments
           WHERE entry_id = ?
           ORDER BY id ASC""",
        (entry_id,),
    ).fetchall()
    conn.close()
    return rows


def _count_challenge_entry_likes(entry_id: int) -> int:
    conn = _get_main_conn()
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM challenge_entry_likes WHERE entry_id = ?",
        (entry_id,),
    ).fetchone()
    conn.close()
    return row["c"] if row else 0


def _has_challenge_entry_like(entry_id: int, user_id: int) -> bool:
    conn = _get_main_conn()
    row = conn.execute(
        "SELECT 1 FROM challenge_entry_likes WHERE entry_id = ? AND user_id = ?",
        (entry_id, user_id),
    ).fetchone()
    conn.close()
    return bool(row)


def _init_ach_schema():
    conn = _get_ach_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS badges (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            threshold INTEGER NOT NULL,
            requirement_type TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS landmarks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT NOT NULL,
            story TEXT NOT NULL,
            question TEXT NOT NULL,
            correct_answer INTEGER NOT NULL,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS landmark_options (
            id INTEGER PRIMARY KEY,
            landmark_id INTEGER NOT NULL,
            option_text TEXT NOT NULL,
            option_index INTEGER NOT NULL,
            FOREIGN KEY (landmark_id) REFERENCES landmarks(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            reward INTEGER NOT NULL,
            total_required INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT NOT NULL,
            cost INTEGER NOT NULL,
            description TEXT,
            is_active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            required_count INTEGER NOT NULL,
            parent_id INTEGER,
            category TEXT NOT NULL,
            level INTEGER NOT NULL,
            icon TEXT NOT NULL,
            reward_points INTEGER NOT NULL,
            FOREIGN KEY (parent_id) REFERENCES skills(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS checkin_rewards (
            id INTEGER PRIMARY KEY,
            streak_days INTEGER NOT NULL,
            reward_points INTEGER NOT NULL,
            description TEXT
        );
        CREATE TABLE IF NOT EXISTS user_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_id INTEGER NOT NULL,
            earned INTEGER NOT NULL DEFAULT 0,
            earned_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (badge_id) REFERENCES badges(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS user_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            checkin_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS user_landmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            landmark_id INTEGER NOT NULL,
            unlocked INTEGER NOT NULL DEFAULT 0,
            completed INTEGER NOT NULL DEFAULT 0,
            unlocked_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (landmark_id) REFERENCES landmarks(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS user_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quest_id INTEGER NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            completed INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (quest_id) REFERENCES quests(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS user_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reward_id INTEGER NOT NULL,
            redeemed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (reward_id) REFERENCES rewards(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS user_skill_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            reward_points INTEGER NOT NULL,
            rewarded_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS user_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            completed INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
        );
        """
    )

    # Ensure achievements columns exist on the main users table.
    user_cols = {row["name"] for row in cur.execute("PRAGMA table_info(users)").fetchall()}
    def _add_col(name: str, ddl: str):
        if name not in user_cols:
            cur.execute(f"ALTER TABLE users ADD COLUMN {ddl}")
            user_cols.add(name)

    _add_col("total_points", "total_points INTEGER NOT NULL DEFAULT 0")
    _add_col("available_points", "available_points INTEGER NOT NULL DEFAULT 0")
    _add_col("active_days", "active_days INTEGER NOT NULL DEFAULT 0")
    _add_col("current_tier", "current_tier INTEGER NOT NULL DEFAULT 1")
    _add_col("current_streak", "current_streak INTEGER NOT NULL DEFAULT 0")
    _add_col("is_admin", "is_admin INTEGER NOT NULL DEFAULT 0")

    def _table_count(table: str) -> int:
        return cur.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]

    if _table_count("badges") == 0:
        cur.executemany(
            "INSERT INTO badges (id, name, icon, description, category, threshold, requirement_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "First Steps", "badge", "Unlock your first landmark", "Journey", 1, "landmarks"),
                (2, "City Explorer", "badge", "Complete 3 landmarks", "Journey", 3, "landmarks"),
                (3, "Island Voyager", "badge", "Complete all 10 landmarks", "Journey", 10, "landmarks"),
                (4, "Community Builder", "badge", "Complete 5 quests", "Community", 5, "quests"),
                (5, "Helpful Guide", "badge", "Complete 10 quests", "Community", 10, "quests"),
                (6, "Master Connector", "badge", "Complete 20 quests", "Community", 20, "quests"),
                (7, "Point Collector", "coin", "Earn 1,000 points", "Progress", 1000, "points"),
                (8, "Point Master", "trophy", "Earn 5,000 points", "Progress", 5000, "points"),
                (9, "Tier Ascender", "rocket", "Reach Tier 3", "Progress", 3, "tier"),
                (10, "Skill Starter", "badge", "Complete 5 skills", "Skills", 5, "skills"),
                (11, "Skill Builder", "badge", "Complete 10 skills", "Skills", 10, "skills"),
                (12, "Skill Master", "badge", "Complete 15 skills", "Skills", 15, "skills"),
                (13, "Skill Elite", "badge", "Complete 20 skills", "Skills", 20, "skills"),
                (14, "Digital Grandmaster", "badge", "Complete all skills", "Skills", 999, "skills"),
            ],
        )

    if _table_count("landmarks") == 0:
        cur.executemany(
            "INSERT INTO landmarks (id, name, icon, story, question, correct_answer, x, y) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "Jurong", "pin", "Singapore's industrial heartland that transformed into a hub for innovation.", "What is Jurong best known for today?", 1, 220, 310),
                (2, "Chinatown", "pin", "A vibrant district preserving Chinese heritage and culture.", "What makes Chinatown special?", 1, 410, 350),
                (3, "Marina Bay", "pin", "This iconic waterfront area features Marina Bay Sands.", "How many towers does Marina Bay Sands have?", 1, 490, 340),
                (4, "Orchard Road", "pin", "Singapore's premier shopping district with over 20 malls.", "What was Orchard Road before becoming a shopping district?", 1, 380, 290),
                (5, "Kampong Glam", "pin", "The historic Malay-Muslim quarter centered around the Sultan Mosque.", "What is the famous mosque in Kampong Glam?", 1, 520, 285),
                (6, "Little India", "pin", "An ethnic district that celebrates Indian culture.", "Which festival is famously celebrated in Little India?", 1, 460, 270),
                (7, "Botanic Gardens", "pin", "A UNESCO World Heritage Site founded in 1859.", "When was the Singapore Botanic Gardens founded?", 1, 310, 250),
                (8, "Marina Bay Sands", "pin", "Marina Bay Sands features three towers connected by a sky park.", "How many towers does Marina Bay Sands have?", 1, 550, 325),
                (9, "Changi", "pin", "Home to Changi Airport, consistently rated the world's best airport.", "What is Changi best known for?", 1, 620, 285),
                (10, "Sentosa", "pin", "Singapore's island resort destination offering beaches and attractions.", "What does 'Sentosa' mean in Malay?", 0, 370, 470),
            ],
        )

    if _table_count("landmark_options") == 0:
        options = {
            1: ["Shopping malls", "Innovation hub", "Beach resorts", "Historic temples"],
            2: ["Modern skyscrapers", "Blend of heritage and modern life", "Beach activities", "Industrial sites"],
            3: ["2", "3", "4", "5"],
            4: ["Industrial area", "Fruit orchards", "Residential zone", "Fishing village"],
            5: ["Blue Mosque", "Sultan Mosque", "Crystal Mosque", "Grand Mosque"],
            6: ["Christmas", "Deepavali", "Chinese New Year", "Hari Raya"],
            7: ["1819", "1859", "1900", "1965"],
            8: ["2", "3", "4", "5"],
            9: ["Shopping malls", "World-class airport", "Historical museums", "Nature parks"],
            10: ["Peace and tranquility", "Beautiful island", "Paradise beach", "Golden sands"],
        }
        for lm_id, opts in options.items():
            for idx, text in enumerate(opts):
                cur.execute(
                    "INSERT INTO landmark_options (landmark_id, option_text, option_index) VALUES (?, ?, ?)",
                    (lm_id, text, idx),
                )

    if _table_count("quests") == 0:
        cur.executemany(
            "INSERT INTO quests (id, title, description, reward, total_required) VALUES (?, ?, ?, ?, ?)",
            [
                (1, "Join Your First Learning Circle", "Connect with others to learn or share a skill together", 1500, 1),
                (2, "Reply in the Community Forum", "Share your thoughts or help answer someone else's question", 75, 1),
                (3, "Share a Skill", "Teach something you know - cooking, language, crafts, anything!", 200, 1),
                (4, "Thank a Connection", "Send appreciation to someone who helped you", 50, 1),
                (5, "Complete 3 Learning Sessions", "Keep learning and growing with the community", 300, 3),
            ],
        )

    if _table_count("rewards") == 0:
        cur.executemany(
            "INSERT INTO rewards (id, name, icon, cost, description, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (1, "$2 GrabFood Voucher", "gift", 500, None, 1),
                (2, "$3 Starbucks Voucher", "cup", 750, None, 1),
                (3, "$5 Popular Bookstore", "book", 1250, None, 1),
                (4, "$5 Kopitiam Voucher", "bread", 1250, None, 1),
                (5, "$10 NTUC Voucher", "cart", 2500, None, 1),
                (6, "$10 Watsons Voucher", "bag", 2500, None, 1),
                (7, "$15 Movie Voucher", "ticket", 3750, None, 1),
                (8, "$15 Uniqlo Voucher", "shirt", 3750, None, 1),
            ],
        )

    if _table_count("skills") == 0:
        cur.executemany(
            "INSERT INTO skills (id, name, description, required_count, parent_id, category, level, icon, reward_points) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "WhatsApp Basics", "Teach basic messaging and contacts.", 10, None, "Communication", 1, "whatsapp", 50),
                (2, "Emojis & Stickers", "Help seniors use emojis and stickers.", 5, 1, "Communication", 1, "emoji", 30),
                (3, "Voice Messages", "Guide seniors to send voice notes.", 5, 1, "Communication", 2, "voice", 40),
                (4, "Video Calls", "Help seniors make a video call.", 3, 3, "Communication", 3, "video", 60),
                (5, "Group Chats", "Create and manage group chats.", 3, 2, "Communication", 3, "group", 60),
                (6, "Email Basics", "Read and reply to emails.", 8, None, "Communication", 1, "email", 40),
                (7, "Email Attachments", "Send and download attachments.", 4, 6, "Communication", 2, "attachment", 50),
                (8, "Banking Login", "Log in securely to banking apps.", 6, None, "Financial", 1, "bank", 50),
                (9, "Check Balance", "Check account balances.", 4, 8, "Financial", 2, "balance", 40),
                (10, "Transfer Money", "Make a transfer safely.", 5, 9, "Financial", 2, "transfer", 60),
                (11, "Bill Payment", "Pay utility bills online.", 4, 10, "Financial", 3, "bill", 70),
                (12, "Scam Awareness", "Identify common scam patterns.", 5, None, "Safety", 1, "scam", 40),
                (13, "Password Security", "Set strong passwords and manage them.", 3, 12, "Safety", 2, "password", 50),
                (14, "Privacy Settings", "Update privacy and sharing controls.", 4, 13, "Safety", 3, "privacy", 60),
            ],
        )

    if _table_count("checkin_rewards") == 0:
        cur.executemany(
            "INSERT INTO checkin_rewards (id, streak_days, reward_points, description) VALUES (?, ?, ?, ?)",
            [(1, 7, 100, "Perfect week bonus"), (2, 30, 500, "Perfect month bonus")],
        )

    conn.commit()
    conn.close()


def _merge_legacy_databases():
    base_dir = BASE_DIR.parent.parent / "database"
    legacy_paths = [
        base_dir / "reconnect.db",
        base_dir / "sean_reconnect.db",
        base_dir / "reconnect-sg_forum.db",
        base_dir / "dashboard.db",
        base_dir / "app.db",
    ]
    legacy_paths = [p for p in legacy_paths if p.exists() and p.resolve() != DB_PATH.resolve()]
    if not legacy_paths:
        return

    conn = _get_main_conn()
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT)")
    merged = cur.execute("SELECT value FROM app_meta WHERE key = ?", ("legacy_merge_done",)).fetchone()
    if merged and (merged["value"] or "").strip() == "1":
        conn.close()
        return

    def ensure_email(base: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", ".", (base or "legacy").lower()).strip(".")
        if not slug:
            slug = "legacy"
        email = f"{slug}@legacy.local"
        suffix = 1
        while cur.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            suffix += 1
            email = f"{slug}{suffix}@legacy.local"
        return email

    def ensure_user(full_name: str, email: str = None, password_hash: str = None, created_at: str = None, is_admin: int = 0) -> int:
        if email:
            row = cur.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if row:
                if full_name:
                    cur.execute("UPDATE users SET full_name = COALESCE(full_name, ?) WHERE id = ?", (full_name, row["id"]))
                return row["id"]
        email = ensure_email(full_name or "legacy-user")
        if password_hash:
            text = str(password_hash)
            if ":" not in text:
                password_hash = generate_password_hash(text)
        else:
            password_hash = generate_password_hash("legacy-import")
        created_at = created_at or _utc_now_iso()
        cur.execute(
            "INSERT INTO users (full_name, email, password_hash, member_type, created_at, is_admin) VALUES (?, ?, ?, ?, ?, ?)",
            (full_name or "Legacy User", email, password_hash, None, created_at, int(is_admin) if is_admin else 0),
        )
        return cur.lastrowid

    def ensure_legacy_user_by_name(name: str) -> int:
        name = (name or "Legacy User").strip() or "Legacy User"
        row = cur.execute("SELECT id FROM users WHERE full_name = ? LIMIT 1", (name,)).fetchone()
        if row:
            return row["id"]
        return ensure_user(name)

    def row_get(row, key: str, default=None):
        if row is None:
            return default
        if key in row.keys():
            value = row[key]
            return value if value is not None else default
        return default

    conn.commit()

    for path in legacy_paths:
        legacy = sqlite3.connect(path)
        legacy.row_factory = sqlite3.Row
        lcur = legacy.cursor()
        tables = {r["name"] for r in lcur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

        if "users" in tables:
            for row in lcur.execute("SELECT * FROM users").fetchall():
                email = row_get(row, "email")
                name = row_get(row, "name") or row_get(row, "full_name") or row_get(row, "username") or "Legacy User"
                password_hash = row_get(row, "password_hash") or row_get(row, "password")
                created_at = row_get(row, "created_at")
                is_admin = row_get(row, "is_admin", 0)
                ensure_user(name, email, password_hash, created_at, is_admin)
            conn.commit()

        if "matches" in tables:
            for row in lcur.execute("SELECT * FROM matches").fetchall():
                cur.execute(
                    "INSERT OR IGNORE INTO matches (match_id, name, avatar, location, created_at) VALUES (?, ?, ?, ?, ?)",
                    (row_get(row, "match_id"), row_get(row, "name"), row_get(row, "avatar"), row_get(row, "location"), row_get(row, "created_at")),
                )
            conn.commit()

        if "messages" in tables:
            for row in lcur.execute("SELECT * FROM messages").fetchall():
                exists = cur.execute(
                    "SELECT 1 FROM messages WHERE chat_id = ? AND sender = ? AND text = ? AND created_at = ?",
                    (row_get(row, "chat_id"), row_get(row, "sender"), row_get(row, "text"), row_get(row, "created_at")),
                ).fetchone()
                if not exists:
                    cur.execute(
                        "INSERT INTO messages (chat_id, sender, text, created_at, edited_at, is_deleted, deleted_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            row_get(row, "chat_id"),
                            row_get(row, "sender"),
                            row_get(row, "text"),
                            row_get(row, "created_at"),
                            row_get(row, "edited_at"),
                            row_get(row, "is_deleted", 0),
                            row_get(row, "deleted_at"),
                        ),
                    )
            conn.commit()

        if "profanities" in tables:
            for row in lcur.execute("SELECT * FROM profanities").fetchall():
                cur.execute(
                    "INSERT OR IGNORE INTO profanities (word, level, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (row_get(row, "word"), row_get(row, "level"), row_get(row, "created_at"), row_get(row, "updated_at")),
                )
            conn.commit()

        if "posts" in tables:
            post_map = {}
            for row in lcur.execute("SELECT * FROM posts").fetchall():
                author = row_get(row, "author") or "Anonymous"
                author_id = ensure_legacy_user_by_name(author)
                existing = cur.execute(
                    "SELECT id FROM posts WHERE title = ? AND content = ? AND author = ? AND created_at = ?",
                    (row_get(row, "title"), row_get(row, "content"), author, row_get(row, "created_at")),
                ).fetchone()
                if existing:
                    post_id = existing["id"]
                else:
                    cur.execute(
                        "INSERT INTO posts (author_id, author, title, content, category, likes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            author_id,
                            author,
                            row_get(row, "title"),
                            row_get(row, "content"),
                            row_get(row, "category") or "General",
                            row_get(row, "likes") or 0,
                            row_get(row, "created_at"),
                        ),
                    )
                    post_id = cur.lastrowid
                post_map[row_get(row, "id")] = post_id
            conn.commit()

            if "comments" in tables:
                for row in lcur.execute("SELECT * FROM comments").fetchall():
                    post_id = post_map.get(row_get(row, "post_id"))
                    if not post_id:
                        continue
                    author = row_get(row, "author") or "Anonymous"
                    author_id = ensure_legacy_user_by_name(author)
                    existing = cur.execute(
                        "SELECT id FROM comments WHERE post_id = ? AND author = ? AND content = ? AND created_at = ?",
                        (post_id, author, row_get(row, "content"), row_get(row, "created_at")),
                    ).fetchone()
                    if not existing:
                        cur.execute(
                            "INSERT INTO comments (post_id, author_id, author, content, created_at) VALUES (?, ?, ?, ?, ?)",
                            (post_id, author_id, author, row_get(row, "content"), row_get(row, "created_at")),
                        )
                conn.commit()

        if "challenges" in tables:
            challenge_map = {}
            for row in lcur.execute("SELECT * FROM challenges").fetchall():
                existing = cur.execute(
                    "SELECT id FROM weekly_challenges WHERE title = ? AND description = ?",
                    (row_get(row, "title"), row_get(row, "description")),
                ).fetchone()
                if existing:
                    challenge_id = existing["id"]
                else:
                    cur.execute(
                        "INSERT INTO weekly_challenges (title, description, reward_points, week_label, created_at) VALUES (?, ?, ?, ?, ?)",
                        (
                            row_get(row, "title"),
                            row_get(row, "description"),
                            20,
                            "Legacy Challenge",
                            row_get(row, "created_at") or _utc_now_iso(),
                        ),
                    )
                    challenge_id = cur.lastrowid
                challenge_map[row_get(row, "id")] = challenge_id
            conn.commit()

            if "submissions" in tables:
                for row in lcur.execute("SELECT * FROM submissions").fetchall():
                    challenge_id = challenge_map.get(row_get(row, "challenge_id"))
                    if not challenge_id:
                        continue
                    author = row_get(row, "author") or "Legacy Participant"
                    author_id = ensure_legacy_user_by_name(author)
                    existing = cur.execute(
                        "SELECT id FROM challenge_entries WHERE challenge_id = ? AND user_id = ? AND content = ? AND created_at = ?",
                        (challenge_id, author_id, row_get(row, "content"), row_get(row, "created_at")),
                    ).fetchone()
                    if not existing:
                        cur.execute(
                            "INSERT INTO challenge_entries (challenge_id, user_id, author_name, content, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                challenge_id,
                                author_id,
                                author,
                                row_get(row, "content"),
                                row_get(row, "image_path"),
                                row_get(row, "created_at") or _utc_now_iso(),
                            ),
                        )
                conn.commit()

        if "challenge" in tables:
            challenge_map = {}
            for row in lcur.execute("SELECT * FROM challenge").fetchall():
                existing = cur.execute(
                    "SELECT id FROM weekly_challenges WHERE title = ? AND description = ?",
                    (row_get(row, "title"), row_get(row, "description")),
                ).fetchone()
                if existing:
                    challenge_id = existing["id"]
                else:
                    cur.execute(
                        "INSERT INTO weekly_challenges (title, description, reward_points, week_label, created_at) VALUES (?, ?, ?, ?, ?)",
                        (
                            row_get(row, "title"),
                            row_get(row, "description"),
                            20,
                            "Legacy Challenge",
                            _utc_now_iso(),
                        ),
                    )
                    challenge_id = cur.lastrowid
                challenge_map[row_get(row, "id")] = challenge_id
            conn.commit()

            if "submission" in tables:
                legacy_user_id = ensure_legacy_user_by_name("Legacy Participant")
                for row in lcur.execute("SELECT * FROM submission").fetchall():
                    challenge_id = challenge_map.get(row_get(row, "challenge_id"))
                    if not challenge_id:
                        continue
                    existing = cur.execute(
                        "SELECT id FROM challenge_entries WHERE challenge_id = ? AND user_id = ? AND content = ?",
                        (challenge_id, legacy_user_id, row_get(row, "content")),
                    ).fetchone()
                    if not existing:
                        cur.execute(
                            "INSERT INTO challenge_entries (challenge_id, user_id, author_name, content, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                challenge_id,
                                legacy_user_id,
                                "Legacy Participant",
                                row_get(row, "content"),
                                None,
                                _utc_now_iso(),
                            ),
                        )
                conn.commit()

        if "users" in tables and path.name == "app.db":
            for row in lcur.execute("SELECT * FROM users").fetchall():
                email = row_get(row, "email")
                if not email:
                    continue
                user_id = ensure_user(row_get(row, "username") or row_get(row, "full_name") or "Legacy User", email, row_get(row, "password_hash"))
                cur.execute(
                    "UPDATE users SET total_points = MAX(COALESCE(total_points, 0), ?), available_points = MAX(COALESCE(available_points, 0), ?) WHERE id = ?",
                    (row_get(row, "total_points", 0), row_get(row, "available_points", 0), user_id),
                )
            conn.commit()

        legacy.close()

    cur.execute("DELETE FROM app_meta WHERE key = ?", ("legacy_merge_done",))
    cur.execute("INSERT INTO app_meta (key, value) VALUES (?, ?)", ("legacy_merge_done", "1"))
    conn.commit()
    conn.close()


with app.app_context():
    _init_ach_schema()
    _init_home_schema()
    _init_meetup_schema()
    _init_challenges_schema()
    _init_reports_schema()
    _init_safety_schema()
    _init_wellbeing_schema()
    _init_partner_schema()
    _init_scrapbook_schema()
    _init_avatar_schema()
    _init_admin_schema()
    _init_meta_schema()
    _init_notifications_schema()
    _merge_legacy_databases()


def _ensure_ach_user(user: User) -> None:
    conn = _get_ach_conn()
    cur = conn.cursor()
    existing = cur.execute("SELECT id FROM users WHERE id = ?", (user.id,)).fetchone()
    if not existing:
        # User was created in the main app; achievements columns will be initialized below.
        pass
    cur.execute(
        """UPDATE users
           SET full_name = COALESCE(full_name, ?)
           WHERE id = ?""",
        (user.full_name, user.id),
    )

    # Initialize achievements columns if they are NULL.
    cur.execute(
        """UPDATE users
           SET total_points = COALESCE(total_points, 0),
               available_points = COALESCE(available_points, 0),
               active_days = COALESCE(active_days, 0),
               current_tier = COALESCE(current_tier, 1),
               current_streak = COALESCE(current_streak, 0),
               is_admin = COALESCE(is_admin, 0)
           WHERE id = ?""",
        (user.id,),
    )

    count = cur.execute("SELECT COUNT(*) AS c FROM user_badges WHERE user_id = ?", (user.id,)).fetchone()["c"]
    if count == 0:
        for row in cur.execute("SELECT id FROM badges").fetchall():
            cur.execute(
                "INSERT INTO user_badges (user_id, badge_id, earned, earned_at) VALUES (?, ?, 0, NULL)",
                (user.id, row["id"]),
            )

    count = cur.execute("SELECT COUNT(*) AS c FROM user_landmarks WHERE user_id = ?", (user.id,)).fetchone()["c"]
    if count == 0:
        for row in cur.execute("SELECT id FROM landmarks").fetchall():
            cur.execute(
                "INSERT INTO user_landmarks (user_id, landmark_id, unlocked, completed) VALUES (?, ?, 0, 0)",
                (user.id, row["id"]),
            )

    count = cur.execute("SELECT COUNT(*) AS c FROM user_quests WHERE user_id = ?", (user.id,)).fetchone()["c"]
    if count == 0:
        for row in cur.execute("SELECT id, total_required FROM quests").fetchall():
            cur.execute(
                "INSERT INTO user_quests (user_id, quest_id, progress, completed) VALUES (?, ?, 0, 0)",
                (user.id, row["id"]),
            )

    count = cur.execute("SELECT COUNT(*) AS c FROM user_skills WHERE user_id = ?", (user.id,)).fetchone()["c"]
    if count == 0:
        for row in cur.execute("SELECT id FROM skills").fetchall():
            cur.execute(
                "INSERT INTO user_skills (user_id, skill_id, progress, completed) VALUES (?, ?, 0, 0)",
                (user.id, row["id"]),
            )

    conn.commit()
    conn.close()


def _update_tier(points: int) -> int:
    if points >= 4000:
        return 3
    if points >= 2000:
        return 2
    return 1


def _increment_quest_progress(user_id: int, quest_id: int, increment: int = 1) -> None:
    user = db.session.get(User, user_id)
    if not user:
        return
    _ensure_ach_user(user)
    conn = _get_ach_conn()
    cur = conn.cursor()
    quest = cur.execute(
        """SELECT q.title, q.reward, q.total_required, uq.progress, uq.completed
           FROM quests q
           JOIN user_quests uq ON uq.quest_id = q.id
           WHERE q.id = ? AND uq.user_id = ?""",
        (quest_id, user_id),
    ).fetchone()
    if not quest:
        conn.close()
        return
    if quest["completed"]:
        conn.close()
        return
    progress = min(quest["progress"] + increment, quest["total_required"])
    completed = 1 if progress >= quest["total_required"] else 0
    if completed:
        cur.execute(
            "UPDATE users SET total_points = total_points + ?, available_points = available_points + ? WHERE id = ?",
            (quest["reward"], quest["reward"], user_id),
        )
    cur.execute(
        """UPDATE user_quests
           SET progress = ?, completed = ?, completed_at = CASE WHEN ?=1 THEN COALESCE(completed_at, ?) ELSE completed_at END
           WHERE user_id = ? AND quest_id = ?""",
        (progress, completed, completed, datetime.utcnow().isoformat(), user_id, quest_id),
    )
    conn.commit()
    conn.close()
    if completed:
        _add_notification(
            user_id,
            "quest_complete",
            f"Quest completed: {quest['title']} (+{quest['reward']} pts)",
            {"quest_id": quest_id},
        )



# --- Global notifications + local FAQ chatbot ---
FAQ_JSON_PATH = STATIC_DIR / "data" / "faq.json"
FAQ_DEFAULT_SUGGESTIONS = [
    "How matching works",
    "Report someone",
    "Join a circle",
    "Points and badges",
]
FAQ_SYNONYMS = {
    "signin": "login",
    "log in": "login",
    "register": "signup",
    "account": "profile",
    "buddy": "matching",
    "chat": "message",
    "messages": "message",
    "reporting": "report",
    "blocklist": "block",
    "classes": "circles",
    "workshop": "circles",
    "points": "repoints",
    "mrt": "station",
    "location": "meetup",
}


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", (value or "").lower())).strip()


def _load_faq_entries() -> list[dict]:
    try:
        raw = FAQ_JSON_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
    except Exception:
        pass
    return []


def _expand_tokens(tokens: set[str]) -> set[str]:
    out = set(tokens)
    for token in list(tokens):
        mapped = FAQ_SYNONYMS.get(token)
        if mapped:
            out.add(mapped)
    return out


def _faq_match(message: str) -> tuple[str, list[str]]:
    text = _normalize_text(message)
    if not text:
        return (
            "I can help with account, matching, safety, circles, challenges, and points. Try one of the quick topics.",
            FAQ_DEFAULT_SUGGESTIONS,
        )

    entries = _load_faq_entries()
    if not entries:
        return (
            "Iâ€™m not sure yet. Here are common topics: matching, reporting, circles, and points.",
            FAQ_DEFAULT_SUGGESTIONS,
        )

    user_tokens = _expand_tokens(set(text.split()))
    best = None
    best_score = 0.0

    for entry in entries:
        question = str(entry.get("question", ""))
        answer = str(entry.get("answer", ""))
        keywords = entry.get("keywords") or []
        key_text = " ".join([str(k) for k in keywords])
        doc = _normalize_text(question + " " + key_text)
        if not doc or not answer:
            continue

        doc_tokens = _expand_tokens(set(doc.split()))
        overlap = len(user_tokens.intersection(doc_tokens))
        fuzzy = SequenceMatcher(None, text, doc).ratio()
        score = overlap * 2.0 + fuzzy
        if question.lower() in text:
            score += 0.8

        if score > best_score:
            best_score = score
            best = entry

    if best and best_score >= 1.2:
        answer = str(best.get("answer", "")).strip()
        suggestions = [s for s in FAQ_DEFAULT_SUGGESTIONS if _normalize_text(s) != _normalize_text(str(best.get("question", "")))]
        return answer, suggestions[:4]

    return (
        "Iâ€™m not sure yet. Here are common topics I can help with. You can also report this or contact admin/support.",
        FAQ_DEFAULT_SUGGESTIONS,
    )


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


@app.post("/faq")
def faq_reply():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "") or "")[:240]
    reply, suggestions = _faq_match(message)
    return jsonify({"reply": reply, "suggestions": suggestions})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)

