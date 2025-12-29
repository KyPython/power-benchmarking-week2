# Vercel Deployment Guide

## Configuration

The project is configured for Vercel deployment with the following setup:

### Files Created

1. **`vercel.json`** - Vercel configuration
   - Routes root (`/`) to `landing-page.html`
   - Uses static file serving
   - Output directory: `docs`

2. **`package.json`** - Node.js package configuration
   - Required by Vercel for build detection
   - Minimal build script (static site)

3. **`.vercelignore`** - Files to exclude from deployment
   - Excludes Python code, scripts, and development files
   - Only deploys `docs/` directory

## Deployment

### Automatic (GitHub Integration)

1. Push to `main` branch
2. Vercel automatically detects changes
3. Builds and deploys the site

### Manual Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Production deployment
vercel --prod
```

## Site Structure

```
/
├── landing-page.html (main landing page)
├── *.md (documentation files)
└── *.html (other HTML pages)
```

## Custom Domain

To add a custom domain:

1. Go to Vercel Dashboard → Project Settings → Domains
2. Add your domain
3. Update DNS records as instructed

## Build Output

The deployment serves static files from the `docs/` directory:
- Landing page at root (`/`)
- Documentation files accessible via their paths
- All files served with proper MIME types

## Troubleshooting

### Build completes but no files deployed

- Check `.vercelignore` - ensure `docs/` is not ignored
- Verify `vercel.json` output directory matches actual structure
- Check Vercel build logs for errors

### 404 errors

- Verify `vercel.json` routes are correct
- Check file paths in `docs/` directory
- Ensure `landing-page.html` exists

### Blue theme not showing

- Verify CSS is included in HTML files
- Check that inline styles are preserved
- Ensure Rich console colors are for CLI only (not web)


