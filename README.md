# Achievement Farm

Automation tooling for GitHub contribution achievements — built for learning, testing GitHub API workflows, and simulating contribution activity.

> ⚠️ **Note**: This repo exists as a sandbox for testing GitHub automation (branch/PR/merge flows, co-authoring, issue lifecycle). The commit history is deliberately generated activity, not a real project.

## What it tests

- **PR lifecycle** — create branch → edit file → open PR → merge (no review)
- **Issue lifecycle** — open & close issue within minutes
- **Co-authored commits** — `Co-authored-by:` trailer in commit messages
- **GitHub API automation** — `requests`-based, raw REST endpoints

## Badges farmed

| Badge | Method |
|-------|--------|
| Pull Shark | merged PRs |
| YOLO | merge without review |
| Quickdraw | close issue within 5 min |
| Pair Extraordinaire | co-authored merged PR |

## Structure

```
bot.py          # main automation loop (Pull Shark / YOLO / Quickdraw / Pair)
README.md
```

## Usage

```bash
GH_TOKEN=... GH_OWNER=... python3 bot.py --count 10 --delay 2
GH_TOKEN=... GH_OWNER=... python3 bot.py --coauthor "Name <email>" --count 5
```

---

*Sandbox for GitHub API automation experiments.*
