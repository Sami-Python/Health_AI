# Health AI Landing Page

Modern landing page for Health AI training application. Dark theme, responsive design, optimized for Firebase Hosting deployment.

## 📋 Contents

- **Hero Section** with clear CTA button
- **Navigation** with Login button (-> http://localhost:3000)
- **ECG Visualization** with heart rate curve
- **Features** (6 feature cards)
- **AI Analytics** machine learning visualization
- **App Store & Google Play** download buttons
- **Mobile-Friendly** responsive design

## 🚀 Usage (Local)

Open in browser:
```
landing_page/index.html
```

Or with local server:
```bash
cd landing_page
python -m http.server 8080
# Open: http://localhost:8080
```

## 🔥 Firebase Hosting Deployment

### 1. Install Firebase CLI
```bash
npm install -g firebase-tools
firebase login
```

### 2. Initialize Project
```bash
cd landing_page
firebase init hosting
```

**Answers:**
- Public directory: `.` (current directory)
- Single-page app: `No`
- Overwrite index.html: `No`

### 3. Deploy
```bash
firebase deploy --only hosting
```

Your site is now live at: `https://your-project-id.web.app`

### 4. Custom Domain (Optional)
Firebase Console → Hosting → "Add custom domain"

## 📁 Structure

```
landing_page/
├── index.html              # Main page (HTML)
├── styles.css              # Stylesheet (CSS)
├── assets/                 # Images
│   ├── ecg-heart-rate.png  # Heart rate curve
│   ├── hero-fitness.png    # Hero image
│   └── ai-analytics.png    # AI visualization
└── README.md               # This file
```

## 🎨 Design

- **Theme**: Dark Mode
- **Colors**: Indigo (#6366F1), Purple (#8B5CF6), Pink (#EC4899)
- **Typography**: Inter (Google Fonts)
- **Effects**: Glassmorphism, Gradients, Animations

## ⚙️ Before Production Deployment

1. **Update URLs:**
   - Change `http://localhost:3000` → production URL
   - Change `http://localhost:8001/docs` → production API docs

2. **Add Analytics:**
   - Google Analytics or Firebase Analytics

3. **SEO:**
   - Add `robots.txt`
   - Add `sitemap.xml`
   - Add Open Graph meta tags

4. **Optimize Images:**
   - Convert PNG → WebP (smaller file size)
   - Lazyload images

## 📱 Responsiveness

- ✅ Desktop (1280px+)
- ✅ Tablet (768px - 1024px)
- ✅ Mobile (< 768px)

## 🔗 Links

- **Frontend App**: Update to production URL before deployment
- **API Docs**: Update to production URL before deployment
- **GitHub**: Add your repository URL

---

**Ready to deploy!** 🚀
