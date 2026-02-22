# 🚀 How to Run Re:Connect SG

## Step-by-Step Instructions

### **1. Download the Project**
Save all files to a folder on your computer called `reconnect-sg`

### **2. Open Terminal/Command Prompt**

**Windows:**
- Press `Windows + R`
- Type `cmd` and press Enter

**Mac:**
- Press `Command + Space`
- Type `Terminal` and press Enter

**Linux:**
- Press `Ctrl + Alt + T`

### **3. Navigate to Project Folder**

```bash
cd path/to/reconnect-sg
```

Examples:
- Mac/Linux: `cd ~/Desktop/reconnect-sg`
- Windows: `cd C:\Users\YourName\Desktop\reconnect-sg`

### **4. Check Python is Installed**

```bash
python3 --version
```

Or on Windows:
```bash
python --version
```

If Python is not installed, download from: https://python.org

### **5. Start the Server**

```bash
python3 app.py
```

Or on Windows:
```bash
python app.py
```

You should see:
```
 Re:Connect SG server running at http://localhost:3000
```

### **6. Open in Your Browser**

Go to: **http://localhost:3000/index.html**

### **7. Navigate the Site**

- **Homepage** → Click "Sign Up"
- **Sign Up** → Fill form → Submit
- **Onboarding** → Choose Youth/Senior → Select interests → Set availability
- **Dashboard** → Explore tabs:
  - **Matches**: Connect with compatible buddies
  - **Learning Circles**: Join group sessions
  - **Weekly Challenges**: Participate in activities
  - **Memory Tree**: Track your connections
  - **Badges**: View achievements

### **To Stop the Server**

Press `Ctrl + C` in the terminal

## 📄 Available Pages

- `index.html` - Homepage
- `login.html` - Login page
- `signup.html` - Registration
- `onboarding.html` - 3-step setup
- `dashboard.html` - Multi-tab dashboard
- `explore.html` - Events & activities
- `messages.html` - Re:Chat messaging
- `perks.html` - Rewards & points

## ✨ Complete Feature List

### 🎨 Design & Accessibility
- **Primary Orange**: #F47C20 | **Secondary Teal**: #2CB6A5
- **Accessibility Suite**:
  - Font sizing: Normal → Large → Extra Large (click A/AA button)
  - High contrast mode for better visibility
  - Screen reader compatible
  - Keyboard navigation (Tab, Alt+B, Alt+N, ESC)
- **Singapore Localization**:
  - 🇬🇧 English | 🇨🇳 中文 | 🇲🇾 Bahasa Melayu | 🇮🇳 தமிழ்
  - Culturally appropriate icons and content
- **Back buttons** on every page for easy navigation

### 🏠 Multi-Tab Dashboard
- **Matches**: 95% match scores, shared interests, "Say Hi" buttons
- **Learning Circles**: Tech, Wisdom Hour, Language Bridges categories
- **Weekly Challenges**: Earn Re:Points, submit entries, view feed
- **Memory Tree**: Growth stages (Sprout → Sapling → Young → Flourishing)
- **Badges**: 29 total achievements with locked/unlocked states

### 💬 Re:Chat Messages (FULLY FUNCTIONAL)
- Real-time conversations with typing indicators
- Switch between multiple chats
- Send and receive messages
- Translation feature (4 languages)
- Conversation starters for easy ice-breaking
- Voice message, photo, emoji options
- Safe chat filters & content monitoring
- Report inappropriate content

### 🔔 Notifications (CLICKABLE)
- Real-time notification dropdown
- Unread badges with count
- Mark all as read
- Different notification types (messages, matches, badges, circles)
- Keyboard shortcut: Alt+N

### 👤 Profile Page (COMPLETE)
**4 Tabs:**
1. **About**: Bio, location, languages spoken
2. **Interests & Skills**: What you teach/learn, hobbies
3. **Safety & Verification**:
   - ✓ NRIC verification status
   - Safe chat filters toggle
   - Activity monitoring
   - Public profile settings
   - Emergency contact
   - Report & block users
   - Safety tips
4. **Settings**:
   - Notification preferences (9 options)
   - Privacy settings (4 options)
   - Language selection
   - Screen reader support
   - Change password, download data, delete account

### 🛡️ Safety Features
- ✓ Identity verification (NRIC)
- Content moderation & monitoring
- Safe chat filters
- Block & report system
- Emergency contact storage
- Safety tips & guidelines

## 🆘 Troubleshooting

**"python3: command not found"**
 Try `python` instead of `python3`

**"Port 3000 already in use"**
 Edit `app.py`, change `PORT = 3000` to `PORT = 8000`
 Then use `http://localhost:8000/index.html`

**CSS not loading**
 Make sure `static/css/` folder exists with all CSS files

Need help? Contact Same support at support@same.new
