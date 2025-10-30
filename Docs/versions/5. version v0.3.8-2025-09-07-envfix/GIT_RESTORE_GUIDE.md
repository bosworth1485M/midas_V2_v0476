# GIT_RESTORE_GUIDE.md

Simple, safe recipes you can copy/paste on Windows PowerShell (no `&&`, no pipes).

## 0) Create a restore point (optional but recommended)
```
git add -A
git commit -m "WIP before restore" --allow-empty
```

## 1) Create a version (tag) at your current state
```
git add -A
git commit -m "vX.Y.Z: message" --allow-empty
git tag -a vX.Y.Z -m "message"
git push
git push --tags
```

## 2) Restore an entire version exactly (frozen snapshot)
```
git fetch --all --tags
git checkout -b restore/vX.Y.Z vX.Y.Z
```

## 3) Restore specific folders/files from a known-good version
```
git fetch --all --tags
git checkout vX.Y.Z -- scripts Docs config src
git add -A
git commit -m "Restore scripts+Docs+config+src from vX.Y.Z"
```

## 4) Verify what's in a version
```
git show vX.Y.Z --name-only --decorate --oneline
```

## 5) Optional: zip a version for archiving
```
git archive --format=zip --output ".\Midas_V2_vX.Y.Z.zip" vX.Y.Z
```

## Notes
- Files in `.gitignore` (e.g., `.env`, `out\...`, `data\samples\*.csv`) are not included in versions by default.
- Keep `.env` in the project root and a backup `.env.bak` if desired.
