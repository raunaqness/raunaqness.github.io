# Repository Documentation for raunaqness.com

## Overview
This repository hosts the source code and build artifacts for **raunaqness.com**, a personal portfolio and blog built with [Hugo](https://gohugo.io/). The site uses the **PaperMod** theme.

## Key Configuration
The site is configured via `config.yml`. A critical setting to note is:
```yaml
publishDir: "."
```
This means the **build artifacts (HTML, XML, generated directories) are output directly to the root directory**, mixing with the source code.

## Directory Structure

### Source Directories
*   **`content/`**: Contains all the markdown content for the site.
    *   `posts/`: Blog posts.
    *   `about.md`: About page.
    *   `food/`, `blog/`, `photos/`: Specific sections of the site.
*   **`staticfiles/`**: This is the `staticDir`. Files here are copied to the root upon build.
    *   `images/`: Profile pictures and other assets.
    *   `files/`: Downloadable files like resumes.
*   **`themes/PaperMod/`**: The theme submodule.
*   **`config.yml`**: Main configuration file.

### Build Artifacts (Generated)
Since `publishDir` is `.` the following are generated/updated when running `hugo`:
*   `index.html`
*   `404.html`
*   `sitemap.xml`
*   Directories like `food/`, `blog/`, `resume/`, `photos/` (these mirrored names in root contain the generated HTML for those sections).

## Content Management
*   **New Posts**: Create markdown files in `content/posts/`.
*   **Pages**: Create markdown files in `content/` (e.g., `content/new-page.md`).
*   **Static Assets**: Place in `staticfiles/`. Reference as `/images/foo.jpg`.

## Development & Deployment
### Local Development
Run the local server with live reload:
```bash
hugo server
```

### Production Build
To build the site for production:
```bash
hugo
```
This generates the static files in the root directory.

### Deployment
The site is hosted on GitHub Pages. Since the build artifacts are in the root directory, committing and pushing the changes to the `main` branch triggers the deployment (or serves the files directly if configured for root).
