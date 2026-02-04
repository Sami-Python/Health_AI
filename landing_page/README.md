# Health AI Landing Page

Modern landing page for Health AI training application. Dark theme, responsive design, deployed on Cloudflare Pages.

## 📋 Contents

- **Hero Section** with clear CTA button
- **Navigation** with Login button (→ https://app.personalaicoach.ai)
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

## ☁️ Cloudflare Pages Deployment

See **[CLOUDFLARE_DEPLOYMENT.md](CLOUDFLARE_DEPLOYMENT.md)** for complete deployment guide.

### Quick Deploy

1. **Create Cloudflare Pages project**
   - Connect GitHub repository
   - Build output directory: `landing_page`
   - No build command needed (static site)

2. **Configure custom domain**
   - Add `www.personalaicoach.ai` in Pages dashboard
   - Cloudflare automatically configures DNS

3. **Set up SSL/TLS**
   - Enable Full (Strict) mode
   - Enable Always Use HTTPS

4. **Configure email routing**
   - Set up `info@personalaicoach.ai` forwarding

**Live URL:** https://www.personalaicoach.ai


## 📁 Structure

```
landing_page/
├── index.html              # Main page (HTML)
├── styles.css              # Stylesheet (CSS)
├── assets/                 # Images
│   ├── ecg-heart-rate.webp  # Heart rate curve
│   ├── hero-fitness.webp    # Hero image
│   └── ai-analytics.webp    # AI visualization
└── README.md               # This file
```

## 🎨 Design

- **Theme**: Dark Mode
- **Colors**: Indigo (#6366F1), Purple (#8B5CF6), Pink (#EC4899)
- **Typography**: Inter (Google Fonts)
- **Effects**: Glassmorphism, Gradients, Animations

## ⚙️ Production Status

1. **URLs:**
   - ✅ Updated to production URLs
   - Frontend App: `https://app.personalaicoach.ai`
   - Backend API: `https://health-ai-backend-35976089058.europe-north1.run.app`

2. **Analytics:**
   - ✅ Firebase Analytics integrated

3. **SEO:**
   - ⏳ Add `robots.txt`
   - ⏳ Add `sitemap.xml`
   - ⏳ Add Open Graph meta tags

4. **Images:**
   - ✅ Optimized WebP format
   - ✅ Lazy loading enabled


## 📱 Responsiveness

- ✅ Desktop (1280px+)
- ✅ Tablet (768px - 1024px)
- ✅ Mobile (< 768px)

## 🔗 Production Links

- **Landing Page**: https://www.personalaicoach.ai
- **Frontend App**: https://app.personalaicoach.ai
- **API Docs**: https://health-ai-backend-35976089058.europe-north1.run.app/docs
- **Email**: info@personalaicoach.ai

---

**Ready to deploy!** 🚀

