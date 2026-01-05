#!/bin/bash
# Fresh git init - removes .git and starts clean
# WARNING: This deletes ALL git history!

set -e

echo "⚠️  WARNING: This will DELETE all git history!"
echo ""
echo "Current status:"
echo "  - Commits: $(git log --oneline | wc -l)"
echo "  - Branches: $(git branch -a | wc -l)"
echo "  - Remote: $(git remote get-url origin 2>/dev/null || echo 'none')"
echo ""
echo "This will:"
echo "  1. Remove .git directory (all history)"
echo "  2. Initialize new git repo"
echo "  3. Add all current files"
echo "  4. Create initial commit"
echo "  5. Set up remote (you'll need to force push)"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Save remote URL if exists
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")

# Remove .git
echo "Removing .git directory..."
rm -rf .git

# Initialize new repo
echo "Initializing new git repository..."
git init

# Add all files (respects .gitignore)
echo "Adding files..."
git add .

# Create initial commit
echo "Creating initial commit..."
git commit -m "Initial commit: StudioFlow v1.0 (fresh start, video files excluded)"

# Set up remote if it existed
if [ -n "$REMOTE_URL" ]; then
    echo "Setting up remote..."
    git remote add origin "$REMOTE_URL"
    echo ""
    echo "✅ Fresh git repository created!"
    echo ""
    echo "Next steps:"
    echo "  1. Verify: git log"
    echo "  2. Force push: git push --force origin main"
    echo "  3. Set upstream: git branch --set-upstream-to=origin/main main"
    echo ""
    echo "⚠️  WARNING: Force push will overwrite remote history!"
else
    echo ""
    echo "✅ Fresh git repository created (no remote configured)!"
    echo ""
    echo "To add remote:"
    echo "  git remote add origin <url>"
    echo "  git push -u origin main"
fi


