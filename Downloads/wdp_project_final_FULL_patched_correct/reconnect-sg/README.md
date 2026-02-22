# Re:Connect SG

Bridge Generations. Build Real Connections.

## Tech Stack
- **HTML** - Structure
- **CSS** - Styling with custom teal & orange theme
- **Python** - Simple HTTP server (no dependencies needed!)

## Setup Instructions

1. Run the server:
```bash
python3 app.py
```

2. Open your browser to `http://localhost:3000/index.html`

## Features
- ✅ Duolingo-style design
- ✅ Solid Teal (#12B8A6) and Orange (#FF9F43) colors (no gradients)
- ✅ Responsive design
- ✅ **Before Login**: Public pages only (Home, How It Works, Explore preview, About)
- ✅ **After Login**: Full dashboard (Home, Connect, Explore, Messages, Perks, Profile)
- ✅ Login & Sign Up pages
- ✅ 3-step Onboarding (user type, interests, availability)
- ✅ Explore page with event listings
- ✅ Dashboard with Welcome animation
- ✅ Profile avatar with notification dot

## Project Structure
```
reconnect-sg/
├── index.html          # Homepage
├── dashboard.html      # Dashboard page
├── app.py             # Flask server
├── static/
│   ├── css/
│   │   ├── styles.css      # Main styles
│   │   └── dashboard.css   # Dashboard styles
│   └── js/
│       └── dashboard.js    # Dashboard JavaScript
└── requirements.txt    # Python dependencies
```
