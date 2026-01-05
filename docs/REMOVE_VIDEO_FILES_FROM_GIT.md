# Removing Large Video Files from Git

## Problem

Large video files (2GB+) are in git history, causing slow `git push` operations. Even though they're now in `.gitignore`, they're still in the repository history.

## Solution Options

### Option 1: Quick Fix (If Files Are Still Tracked)

If video files are still in the current index:

```bash
# Remove from git tracking (keeps local files)
git rm --cached tests/fixtures/test_footage/*.MP4
git rm --cached tests/fixtures/test_footage/*.mov
git rm --cached tests/fixtures/test_footage/*.mxf
git rm --cached tests/fixtures/test_footage/*.mts

# Commit the removal
git commit -m "Remove large video files from git tracking"

# Push (this will still be slow if files are in history)
git push
```

### Option 2: Remove from Entire History (Recommended)

**⚠️ WARNING: This rewrites git history and requires force push!**

Use the provided script:

```bash
./scripts/remove_video_files_from_git.sh
```

Or manually:

```bash
# 1. Create backup branch
git branch backup-before-remove-videos

# 2. Remove from all history
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch tests/fixtures/test_footage/*.MP4 tests/fixtures/test_footage/*.mp4 tests/fixtures/test_footage/*.MOV tests/fixtures/test_footage/*.mov tests/fixtures/test_footage/*.MKV tests/fixtures/test_footage/*.mkv tests/fixtures/test_footage/*.MXF tests/fixtures/test_footage/*.mxf tests/fixtures/test_footage/*.MTS tests/fixtures/test_footage/*.mts' \
  --prune-empty --tag-name-filter cat -- --all

# 3. Clean up refs
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d

# 4. Garbage collect
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 5. Force push (⚠️ DESTRUCTIVE)
git push --force --all
git push --force --tags
```

### Option 3: Use Git LFS (For Future)

If you need to track video files, use Git LFS:

```bash
# Install git-lfs
git lfs install

# Track video files with LFS
git lfs track "tests/fixtures/test_footage/*.MP4"
git lfs track "tests/fixtures/test_footage/*.mov"

# Add .gitattributes
git add .gitattributes
git commit -m "Track video files with Git LFS"
```

## Verification

After removing files:

```bash
# Check if files are still in history
git log --all --full-history -- tests/fixtures/test_footage/*.MP4

# Check repository size
du -sh .git/

# Check what's being pushed
git count-objects -vH
```

## Impact

- **Before**: Repository contains 5GB+ of video files in history
- **After**: Repository only contains code and small test files
- **Push speed**: Should be 10-100x faster

## Important Notes

1. **Force push required**: Removing from history requires `git push --force`
2. **Collaborators**: All collaborators must re-clone or rebase their work
3. **Backup**: Always create a backup branch before rewriting history
4. **Local files**: The script keeps local files, only removes from git

## Current Status

Check if files are still tracked:

```bash
git ls-files tests/fixtures/test_footage/*.MP4
```

If empty, files are already untracked but still in history (need Option 2).
If files listed, they're still tracked (use Option 1 first, then Option 2).


