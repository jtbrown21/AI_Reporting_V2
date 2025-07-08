# GitHub Pages Setup for Report Hosting

## 1. Create GitHub Repository
1. Create a new GitHub repository for hosting reports
2. Go to repository Settings > Pages
3. Set source to "Deploy from a branch"
4. Select "gh-pages" branch
5. Click Save

## 2. Generate GitHub Token
1. Go to GitHub Settings > Developer Settings > Personal Access Tokens
2. Generate a new token with these permissions:
   - repo (full control)
   - workflow
3. Copy the token for use in environment variables

## 3. Repository Structure
Your repository should have this structure:
```
your-repo/
├── index.html (latest report)
├── client-name-2024-01-01.html
├── client-name-2024-02-01.html
└── ...
```

## 4. Environment Variables
Set these in your Railway deployment:
- GITHUB_TOKEN: Your GitHub token
- GITHUB_REPO: username/repository-name
- GITHUB_PAGES_BRANCH: gh-pages (or main if you prefer)

## 5. Test Access
Your reports will be available at:
- https://username.github.io/repository-name/
- https://username.github.io/repository-name/specific-report.html
