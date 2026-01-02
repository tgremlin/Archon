# Upstream Sync Workflow

This document describes how to keep this fork synchronized with the upstream Archon repository.

## Remote Configuration

```
origin   → https://github.com/tgremlin/Archon.git     (your fork)
upstream → https://github.com/coleam00/archon.git    (original repo)
```

## Branch Strategy

| Branch | Purpose | Sync Frequency |
|--------|---------|----------------|
| `main` | Track upstream main | Weekly or as needed |
| `stable` | Your customizations + upstream stable | After testing upstream changes |

## Sync Workflow

### 1. Fetch Upstream Changes

```bash
# Fetch all upstream branches
git fetch upstream

# See what's new
git log HEAD..upstream/main --oneline
```

### 2. Sync Main Branch

```bash
# Switch to main
git checkout main

# Merge upstream main (fast-forward when possible)
git merge upstream/main

# Push to your fork
git push origin main
```

### 3. Sync Stable Branch (with customizations)

```bash
# Switch to stable
git checkout stable

# Merge upstream stable
git merge upstream/stable

# Resolve any conflicts (see below)
# Then push
git push origin stable
```

## Conflict Resolution

### High-Risk Areas for Conflicts

Based on our customizations, watch for conflicts in:

| Area | Files | Resolution Strategy |
|------|-------|---------------------|
| Crawling | `python/src/server/services/crawling/strategies/` | Keep our URL filtering enhancements |
| Tests | `python/tests/` | Merge both, ensure tests pass |
| Config | `.gitignore`, `pyproject.toml` | Merge both additions |

### Resolution Steps

1. **Identify conflict type**:
   ```bash
   git status  # Shows conflicted files
   ```

2. **For each conflict**:
   - Open the file and find `<<<<<<<`, `=======`, `>>>>>>>` markers
   - Decide: keep ours, keep theirs, or merge both
   - Remove conflict markers

3. **After resolving**:
   ```bash
   git add <resolved-files>
   git commit -m "Merge upstream/stable, resolve conflicts in <area>"
   ```

### When to Keep Our Changes

- URL exclusion patterns in `recursive.py`
- Custom recrawl scripts in `scripts/`
- Our `.gitattributes` configuration
- Any fork-specific configurations

### When to Take Upstream Changes

- Bug fixes
- Security updates
- New features we want
- Dependency updates

## Merge vs Rebase

**We use MERGE, not rebase** for syncing:

| Approach | Pros | Cons |
|----------|------|------|
| **Merge (recommended)** | Preserves history, safe for shared branches | More merge commits |
| Rebase | Linear history | Rewrites history, dangerous for pushed branches |

```bash
# DO THIS
git merge upstream/stable

# DON'T DO THIS (unless you know what you're doing)
git rebase upstream/stable  # Rewrites history!
```

## Quick Reference

```bash
# Full sync workflow
git fetch upstream
git checkout main && git merge upstream/main && git push origin main
git checkout stable && git merge upstream/stable
# Resolve any conflicts...
git push origin stable

# Check sync status
git log --oneline origin/stable..upstream/stable  # Commits we're behind
git log --oneline upstream/stable..origin/stable  # Our custom commits

# Compare branches
git diff upstream/stable..stable --stat  # See all differences
```

## Automation (Optional)

For frequent syncing, consider adding a script:

```bash
#!/bin/bash
# scripts/sync-upstream.sh

set -e
git fetch upstream
echo "Upstream changes:"
git log --oneline HEAD..upstream/main | head -10
echo ""
read -p "Merge upstream/main into main? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git checkout main
    git merge upstream/main
    git push origin main
    echo "Main synced!"
fi
```

## Troubleshooting

### "Already up to date" but GitHub shows differences

```bash
# Force fetch to update refs
git fetch upstream --prune
```

### Accidental commit to wrong branch

```bash
# Move commit to correct branch
git checkout correct-branch
git cherry-pick <commit-hash>
git checkout wrong-branch
git reset --hard HEAD~1  # Remove from wrong branch
```

### Merge went wrong, need to undo

```bash
# Abort during merge
git merge --abort

# After merge is complete (before push)
git reset --hard HEAD~1
```
