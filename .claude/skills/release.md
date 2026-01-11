# Release Process

## Pre-Release

1. **Run all tests** (must pass)
   ```bash
   uv run pytest tests/ -v
   ```

## Release Steps

1. **Update version files** (semantic versioning)
   ```bash
   # Edit pyproject.toml: version = "X.Y.Z"
   # Edit src/imggen/version.py: __version__ = "X.Y.Z"
   ```

2. **Update RELEASES.md** (add at TOP)
   ```markdown
   ## vX.Y.Z - YYYY-MM-DD

   ### Features
   - Feature one

   ### Fixes
   - Bug fix one

   ### Breaking Changes
   - (if any)
   ```

3. **Commit and tag**
   ```bash
   git commit -m "Bump version to X.Y.Z"
   git tag vX.Y.Z
   git push origin main
   git push origin vX.Y.Z
   ```

## Critical: Always push tags to remote

Tags required for `imggen check-update` and version management. Never skip this step.

## Verification

```bash
git tag -l
imggen --version
imggen check-update
```
