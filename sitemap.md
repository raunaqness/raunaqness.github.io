# Hugo Site Sitemap & Repository Guide

## Overview
This is a **Hugo static site** for **Raunaq Singh's personal portfolio** (raunaqness.com). The site uses the **PaperMod theme** and is configured for **GitHub Pages** deployment.

## Repository Structure

```
raunaqness.github.io/
├── config.yml                 # Main Hugo configuration
├── CNAME                      # Custom domain configuration
├── .hugo_build.lock          # Hugo build lock file
├── sitemap.md               # This file - repository documentation
├── archetypes/              # Content templates
│   └── default.md           # Default content template
├── content/                  # Site content (markdown files)
│   ├── about.md             # About page
│   ├── elements.md          # Elements page (draft)
│   └── posts/               # Blog posts
│       └── my-first-post.md # Sample blog post
├── staticfiles/             # Static assets (images, files)
│   ├── files/
│   │   └── resume.pdf       # Resume download
│   └── images/
│       ├── dp.jpg           # Profile image
│       └── dp-blurred.jpg   # Blurred profile image
├── themes/                  # Hugo themes
│   ├── ananke/             # Alternative theme (unused)
│   └── PaperMod/           # Active theme
├── public/                 # Build output (GitHub Pages via Actions)
├── docs/                   # Legacy build output (no longer used)
└── .git/                   # Git repository
```

## Configuration Details

### Main Configuration (`config.yml`)
- **Base URL**: https://raunaqness.com
- **Theme**: PaperMod
- **Publish Directory**: public/ (for GitHub Actions)
- **Static Directory**: staticfiles/
- **Language**: en-us

### Site Parameters
- **Profile Mode**: Enabled with custom image and buttons
- **Theme Toggle**: Enabled (light/dark mode)
- **Social Icons**: Instagram, LinkedIn, GitHub, Email
- **Profile Image**: /images/dp-blurred.jpg (200x200px)

## Content Structure

### Pages (`content/`)
1. **About Page** (`about.md`)
   - Professional background and career timeline
   - Current role and location
   - Contact information
   - Career highlights from 2015-2023

2. **Elements Page** (`elements.md`)
   - Currently in draft status
   - Placeholder for additional content

3. **Blog Posts** (`content/posts/`)
   - `my-first-post.md`: Sample post with basic markdown
   - More posts can be added here

### Static Assets (`staticfiles/`)
- **Resume**: `/files/resume.pdf` (50KB)
- **Profile Images**: 
  - `/images/dp.jpg` (1.3MB)
  - `/images/dp-blurred.jpg` (1.8MB)

## Adding New Content

### Creating a New Page
1. Create a new `.md` file in `content/`
2. Use the front matter template:
```yaml
---
title: "Page Title"
date: YYYY-MM-DDTHH:MM:SS+05:30
draft: false
---
```

### Creating a New Blog Post
1. Create a new `.md` file in `content/posts/`
2. Use the same front matter template as pages
3. Posts will automatically appear in the blog section

### Adding Static Files
1. Place files in `staticfiles/`
2. Images go in `staticfiles/images/`
3. Documents go in `staticfiles/files/`
4. Reference them in content as `/images/filename.jpg` or `/files/filename.pdf`

### Modifying Site Configuration
- Edit `config.yml` for site-wide changes
- Theme customization goes in `themes/PaperMod/`
- Custom CSS/JS can be added to `staticfiles/`

## Theme Customization

### PaperMod Theme Features
- **Profile Mode**: Clean landing page with profile image
- **Social Icons**: Configurable social media links
- **Theme Toggle**: Light/dark mode switching
- **Responsive Design**: Mobile-friendly layout
- **SEO Optimized**: Built-in SEO features

### Customization Points
- **Profile Image**: Update `staticfiles/images/dp-blurred.jpg`
- **Resume**: Replace `staticfiles/files/resume.pdf`
- **Social Links**: Modify in `config.yml` under `params.socialIcons`
- **Profile Info**: Update in `config.yml` under `params.profileMode`

## Deployment

### GitHub Pages Setup
- **Source**: GitHub Actions (automatic deployment)
- **Custom Domain**: raunaqness.com
- **Build Process**: GitHub Action builds Hugo site to public/
- **Branch**: main (triggers automatic deployment)

### Local Development
1. Install Hugo
2. Run `hugo server` for local development
3. Run `hugo` to build for production
4. Commit and push to deploy

## Common Tasks for LLMs

### Adding a New Section
1. Create content file in `content/`
2. Update navigation if needed
3. Add any required static assets
4. Test locally with `hugo server`

### Modifying the Theme
1. Check `themes/PaperMod/` for theme files
2. Override theme files by copying to site root
3. Custom CSS/JS goes in `staticfiles/`

### Updating Profile Information
1. Edit `config.yml` for profile mode settings
2. Update `content/about.md` for detailed information
3. Replace profile images in `staticfiles/images/`

### Adding Blog Content
1. Create new `.md` file in `content/posts/`
2. Use proper front matter
3. Include images in `staticfiles/images/` if needed
4. Reference images as `/images/filename.jpg`

## File Types and Extensions
- **Content**: Markdown (`.md`) files
- **Configuration**: YAML (`.yml`) files
- **Static Assets**: Images (`.jpg`, `.png`, `.svg`), PDFs, etc.
- **Theme**: HTML templates, CSS, JavaScript

## Important Notes
- All content is in `content/` directory
- Static assets go in `staticfiles/`
- Build output goes to `public/` (for GitHub Actions)
- Theme is PaperMod (located in `themes/PaperMod/`)
- Custom domain is raunaqness.com
- Site is configured for automatic GitHub Actions deployment

This sitemap provides complete context for understanding and modifying the Hugo site structure. 