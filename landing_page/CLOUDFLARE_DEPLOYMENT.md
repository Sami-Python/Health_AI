# Cloudflare Pages Deployment Guide

This guide covers deploying the Health AI landing page to Cloudflare Pages with custom domain configuration.

## Prerequisites

- Cloudflare account with domain `personalaicoach.ai` registered
- Git repository access
- Cloudflare Pages enabled

## Quick Start

### 1. Create Cloudflare Pages Project

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **Workers & Pages** → **Create application** → **Pages**
3. Connect to your Git repository (GitHub)
4. Select the repository: `health_ai`
5. Configure build settings:
   - **Project name**: `personalaicoach-landing`
   - **Production branch**: `main`
   - **Build command**: (leave empty - static site)
   - **Build output directory**: `landing_page`
   - **Root directory**: `landing_page`

6. Click **Save and Deploy**

### 2. Configure Custom Domain

After the initial deployment:

1. Go to your Pages project → **Custom domains**
2. Click **Set up a custom domain**
3. Add `www.personalaicoach.ai`
4. Cloudflare will automatically configure DNS records
5. Add apex domain `personalaicoach.ai` (will redirect to www)

**DNS Records (Automatic):**
```
www.personalaicoach.ai  CNAME  personalaicoach-landing.pages.dev
personalaicoach.ai      CNAME  personalaicoach-landing.pages.dev
```

### 3. Configure SSL/TLS

1. Navigate to **SSL/TLS** in Cloudflare dashboard
2. Set encryption mode to **Full (strict)**
3. Enable **Always Use HTTPS** under SSL/TLS → Edge Certificates
4. Enable **Automatic HTTPS Rewrites**

### 4. Set Up Email Routing (info@personalaicoach.ai)

1. Go to **Email** → **Email Routing** in Cloudflare dashboard
2. Click **Get started**
3. Add destination email address (your personal email)
4. Create routing rule:
   - **Type**: Custom address
   - **Address**: `info@personalaicoach.ai`
   - **Action**: Send to your verified destination email
5. Cloudflare will automatically add MX records

**Test email routing:**
```bash
# Send a test email to info@personalaicoach.ai
# Verify it arrives at your destination email
```

## Frontend App Configuration (app.personalaicoach.ai)

To host the Next.js frontend app at `https://app.personalaicoach.ai`:

### Option 1: Firebase Hosting with Custom Domain

1. In Firebase Console, go to **Hosting**
2. Click **Add custom domain**
3. Enter `app.personalaicoach.ai`
4. Add the provided DNS records to Cloudflare:
   ```
   app.personalaicoach.ai  A      <Firebase IP>
   app.personalaicoach.ai  AAAA   <Firebase IPv6>
   ```

### Option 2: Cloudflare Pages (Recommended)

1. Create a new Pages project for the frontend
2. Configure build settings:
   - **Build command**: `npm run build`
   - **Build output directory**: `.next`
   - **Root directory**: `frontend`
3. Add custom domain `app.personalaicoach.ai`

## Backend API Custom Domain (Optional)

To use `api.personalaicoach.ai` instead of the long Cloud Run URL:

### Configure DNS for Cloud Run

1. In Cloudflare DNS, add CNAME record:
   ```
   api.personalaicoach.ai  CNAME  ghs.googlehosted.com
   ```

2. In Google Cloud Console:
   - Go to **Cloud Run** → Select your service
   - Click **Manage Custom Domains**
   - Add `api.personalaicoach.ai`
   - Verify domain ownership (TXT record)

3. Update landing page links to use `https://api.personalaicoach.ai/docs`

## Deployment Workflow

### Automatic Deployments

Cloudflare Pages automatically deploys when you push to the `main` branch:

```bash
git add .
git commit -m "Update landing page"
git push origin main
```

### Manual Deployment

You can also deploy manually via Wrangler CLI:

```bash
cd landing_page
npx wrangler pages deploy . --project-name=personalaicoach-landing
```

## Environment Variables

Currently, no environment variables are needed for the landing page. Firebase configuration is embedded in the HTML.

If you need to add environment variables in the future:

1. Go to Pages project → **Settings** → **Environment variables**
2. Add variables for Production/Preview environments

## Performance Optimization

Cloudflare Pages automatically provides:

- ✅ Global CDN distribution
- ✅ HTTP/2 and HTTP/3 support
- ✅ Brotli compression
- ✅ Asset caching (configured in headers)
- ✅ DDoS protection
- ✅ Web Application Firewall (WAF)

### Cache Headers

The landing page already includes optimized cache headers in `firebase.json`:

- **Images/CSS/JS**: 1 year cache (immutable)
- **HTML**: 1 hour cache

These headers are respected by Cloudflare's CDN.

## Monitoring & Analytics

### Cloudflare Analytics

View traffic analytics in Cloudflare dashboard:
- **Analytics & Logs** → **Web Analytics**
- Real-time visitor data
- Geographic distribution
- Performance metrics

### Firebase Analytics

The landing page includes Firebase Analytics tracking:
- Page views
- CTA button clicks
- Store badge clicks
- Login button clicks

View analytics in [Firebase Console](https://console.firebase.google.com/)

## Troubleshooting

### DNS Propagation

DNS changes can take up to 48 hours to propagate globally. Check status:

```bash
# Check DNS resolution
nslookup www.personalaicoach.ai
nslookup app.personalaicoach.ai

# Check from multiple locations
https://dnschecker.org/
```

### SSL Certificate Issues

If you see "Your connection is not private":

1. Wait 10-15 minutes for certificate provisioning
2. Verify SSL/TLS mode is set to **Full (strict)**
3. Clear browser cache and try incognito mode

### Email Routing Not Working

1. Verify MX records are configured correctly
2. Check SPF/DKIM records in Cloudflare Email settings
3. Verify destination email is verified
4. Check spam folder

### Build Failures

If Cloudflare Pages build fails:

1. Check build logs in Pages dashboard
2. Verify `landing_page` directory exists
3. Ensure no build command is set (static site)
4. Check file permissions

## URLs Summary

After deployment, your URLs will be:

- **Landing Page**: https://www.personalaicoach.ai
- **Landing Page (apex)**: https://personalaicoach.ai → redirects to www
- **Frontend App**: https://app.personalaicoach.ai
- **Backend API**: https://health-ai-backend-35976089058.europe-north1.run.app
- **Backend API (custom)**: https://api.personalaicoach.ai (optional)
- **Email**: info@personalaicoach.ai

## Next Steps

1. ✅ Deploy landing page to Cloudflare Pages
2. ✅ Configure custom domain www.personalaicoach.ai
3. ✅ Set up SSL/TLS
4. ✅ Configure email routing
5. ⏳ Deploy frontend app to app.personalaicoach.ai
6. ⏳ (Optional) Configure api.personalaicoach.ai custom domain
7. ⏳ Test all links and functionality
8. ⏳ Monitor analytics and performance

## Support

- [Cloudflare Pages Documentation](https://developers.cloudflare.com/pages/)
- [Cloudflare Email Routing](https://developers.cloudflare.com/email-routing/)
- [Custom Domains Guide](https://developers.cloudflare.com/pages/platform/custom-domains/)
