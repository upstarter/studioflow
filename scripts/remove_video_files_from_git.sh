#!/bin/bash
# Remove large video files from git history
# WARNING: This rewrites git history and requires force push

set -e

echo "⚠️  WARNING: This will rewrite git history!"
echo "All collaborators will need to re-clone the repository."
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Create backup branch first
echo "Creating backup branch..."
git branch backup-before-remove-videos || true

# Remove video files from all branches and history
echo "Removing video files from git history..."

# Use git filter-branch to remove all video files
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch tests/fixtures/test_footage/*.MP4 tests/fixtures/test_footage/*.mp4 tests/fixtures/test_footage/*.MOV tests/fixtures/test_footage/*.mov tests/fixtures/test_footage/*.MKV tests/fixtures/test_footage/*.mkv tests/fixtures/test_footage/*.MXF tests/fixtures/test_footage/*.mxf tests/fixtures/test_footage/*.MTS tests/fixtures/test_footage/*.mts' \
  --prune-empty --tag-name-filter cat -- --all

# Clean up refs
echo "Cleaning up refs..."
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d

# Expire reflog and garbage collect
echo "Running garbage collection..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "✅ Video files removed from git history!"
echo ""
echo "Next steps:"
echo "1. Verify with: git log --all --full-history -- tests/fixtures/test_footage/*.MP4"
echo "2. Force push: git push --force --all"
echo "3. Force push tags: git push --force --tags"
echo ""
echo "⚠️  WARNING: Force push will overwrite remote history!"
echo "All collaborators must re-clone or rebase their work."


