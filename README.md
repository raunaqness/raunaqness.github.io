# Raunaq Singh - Personal Portfolio

A modern, responsive personal portfolio website built with [Hugo](https://gohugo.io/) and the [PaperMod](https://github.com/adityatelange/hugo-PaperMod) theme. Deployed automatically via GitHub Actions to GitHub Pages.

🌐 **Live Site**: [raunaqness.com](https://raunaqness.com)

## 🚀 Features

- **Modern Design**: Clean, minimalist design with PaperMod theme
- **Responsive**: Mobile-friendly layout
- **Dark/Light Mode**: Theme toggle functionality
- **Profile Mode**: Professional landing page with social links
- **Blog Ready**: Built-in blog section for articles
- **SEO Optimized**: Built-in SEO features
- **Automatic Deployment**: GitHub Actions for seamless deployment

## 🛠️ Tech Stack

- **Static Site Generator**: Hugo
- **Theme**: PaperMod
- **Hosting**: GitHub Pages
- **Deployment**: GitHub Actions
- **Domain**: Custom domain (raunaqness.com)

## 📁 Project Structure

```
raunaqness.github.io/
├── .github/workflows/     # GitHub Actions for deployment
├── content/               # Site content (markdown files)
│   ├── about.md          # About page
│   ├── elements.md       # Elements page (draft)
│   └── posts/            # Blog posts
├── staticfiles/          # Static assets
│   ├── files/           # Documents (resume, etc.)
│   └── images/          # Images
├── themes/              # Hugo themes
├── config.yml           # Hugo configuration
└── README.md           # This file
```

## 🚀 Quick Start

### Prerequisites

- [Hugo](https://gohugo.io/installation/) (Extended version recommended)
- [Git](https://git-scm.com/)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/raunaqness/raunaqness.github.io.git
   cd raunaqness.github.io
   ```

2. **Install Hugo** (if not already installed)
   ```bash
   # macOS
   brew install hugo
   
   # Windows
   choco install hugo-extended
   
   # Linux
   sudo apt-get install hugo
   ```

3. **Run development server**
   ```bash
   hugo server --bind 0.0.0.0 --port 1313
   ```

4. **Open in browser**
   Navigate to `http://localhost:1313`

## 📝 Content Management

### Adding New Pages

1. Create a new `.md` file in `content/`
2. Use the front matter template:
   ```yaml
   ---
   title: "Page Title"
   date: 2024-01-01T00:00:00+05:30
   draft: false
   ---
   ```

### Adding Blog Posts

1. Create a new `.md` file in `content/posts/`
2. Use the same front matter template as pages
3. Posts will automatically appear in the blog section

### Adding Static Files

- **Images**: Place in `staticfiles/images/` and reference as `/images/filename.jpg`
- **Documents**: Place in `staticfiles/files/` and reference as `/files/filename.pdf`

## 🎨 Customization

### CSS and JavaScript Customizations

**IMPORTANT**: Hugo uses template files, not static HTML files. For CSS and JavaScript customizations:

- **CSS Customizations**: Edit `layouts/partials/extend_head.html`
- **JavaScript**: Add to `layouts/partials/extend_head.html` or create new partial files
- **Template Overrides**: Place files in `layouts/` directory to override theme templates

**⚠️ Key Discovery**: Hugo serves from template files in `layouts/partials/`, NOT from the static `index.html` file. Always edit the template files for changes to take effect.

### Recent Customizations

- **Navigation Buttons**: Added custom navigation buttons in header
- **Mobile Menu**: Added hamburger menu with dropdown for mobile
- **Profile Image**: Customized profile image styling (rounded corners instead of circular)
- **Mobile Menu Margin**: Added 14px margin to mobile menu container for proper spacing

### Updating Profile Information

1. **Profile Mode Settings**: Edit `config.yml` under `params.profileMode`
2. **About Page**: Update `content/about.md`
3. **Profile Images**: Replace files in `staticfiles/images/`
4. **Resume**: Replace `staticfiles/files/resume.pdf`

## 🚀 Deployment

### Automatic Deployment (Recommended)

The site uses GitHub Actions for automatic deployment:

1. **Push changes** to the `main` branch
2. **GitHub Actions** automatically builds and deploys
3. **Site updates** within minutes

### Manual Deployment

If you need to build locally:

```bash
# Build for production
hugo

# Check build output
ls public/

# Commit and push
git add .
git commit -m "Update site content"
git push origin main
```

## ⚙️ Configuration

### Main Configuration (`config.yml`)

- **Base URL**: https://raunaqness.com
- **Theme**: PaperMod
- **Publish Directory**: public/
- **Static Directory**: staticfiles/

### Customization Points

- **Profile Image**: Update `staticfiles/images/dp-blurred.jpg`
- **Social Links**: Modify in `config.yml` under `params.socialIcons`
- **Theme Settings**: Edit `config.yml` under `params`
- **Custom CSS/JS**: Add to `staticfiles/`

## 🎨 Theme Features

### PaperMod Theme

- **Profile Mode**: Clean landing page with profile image
- **Social Icons**: Configurable social media links
- **Theme Toggle**: Light/dark mode switching
- **Responsive Design**: Mobile-friendly layout
- **SEO Optimized**: Built-in SEO features

### Available Sections

- **About**: Professional background and career timeline
- **Blog**: Articles and posts
- **Resume**: Downloadable PDF resume
- **Social Links**: Instagram, LinkedIn, GitHub, Email

## 🔧 Development Workflow

### Making Changes

1. **Edit content** in `content/` directory
2. **Test locally** with `hugo server`
3. **Commit changes** to Git
4. **Push to GitHub** - automatic deployment

### Common Tasks

- **Add new page**: Create `.md` file in `content/`
- **Add blog post**: Create `.md` file in `content/posts/`
- **Update profile**: Edit `config.yml` and `content/about.md`
- **Add images**: Place in `staticfiles/images/`
- **Custom styling**: Add CSS to `staticfiles/`

## 📊 Performance

- **Static Site**: Fast loading times
- **Optimized Images**: Compressed and optimized
- **Minified Assets**: Production-ready builds
- **CDN**: GitHub Pages global CDN

## 🔍 SEO

- **Meta Tags**: Built-in SEO optimization
- **Sitemap**: Automatic sitemap generation
- **Structured Data**: Schema markup support
- **Social Media**: Open Graph and Twitter Cards

## 🤝 Contributing

This is a personal portfolio site, but if you find any issues or have suggestions:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is for personal use. The PaperMod theme is licensed under the MIT License.

## 📞 Contact

- **Website**: [raunaqness.com](https://raunaqness.com)
- **Email**: raunaqness@gmail.com
- **LinkedIn**: [Gur Raunaq Singh](https://www.linkedin.com/in/gurraunaqsingh/)
- **GitHub**: [@raunaqness](https://github.com/raunaqness)

---

Built with ❤️ using [Hugo](https://gohugo.io/) and [PaperMod](https://github.com/adityatelange/hugo-PaperMod) 