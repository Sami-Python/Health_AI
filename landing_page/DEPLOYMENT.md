# Firebase Hosting Deployment Guide

## Quick Setup

Firebase CLI has been installed successfully! Follow these steps to deploy:

### Step 1: Login to Firebase
```bash
firebase login
```
This will open your browser for Google authentication.

### Step 2: Initialize Firebase Hosting

Navigate to landing_page directory:
```bash
cd c:\Users\samih\code\health_ai\landing_page
firebase init hosting
```

**Configuration answers:**
- Select existing project OR create new one
- Public directory: `.` (current directory)
- Configure as single-page app: `No`
- Set up automatic builds: `No`
- Overwrite index.html: `No`

### Step 3: Deploy
```bash
firebase deploy --only hosting
```

Your site will be live at: `https://YOUR-PROJECT-ID.web.app`

---

## Alternative: Manual Steps

If you prefer, I can help you through each step interactively. Just provide:
1. Your Firebase project ID (e.g., `health-ai-12345`)
2. Confirmation that you've run `firebase login`

Then I can run the init and deploy commands for you!

---

## Troubleshooting

**"firebase: command not found"**
- Close and reopen your terminal
- Run: `npm install -g firebase-tools`

**"Not authorized"**
- Run: `firebase logout` then `firebase login`

**"No project selected"**
- Create project at: https://console.firebase.google.com
- Then run: `firebase use YOUR-PROJECT-ID`
