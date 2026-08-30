#!/usr/bin/env python3
"""Farm GitHub achievements: Pull Shark, YOLO, Quickdraw, Pair Extraordinaire.

Single script, two modes:
  default        -> Pull Shark + YOLO + Quickdraw (one account)
  --coauthor NAME/EMAIL -> merges commits signed with Co-authored-by, giving
                           Pair Extraordinaire to that co-author account.

Per cycle: branch -> edit README -> open PR (no review) -> merge
           + open/close issue within 5 min (Quickdraw).
Merged PRs => Pull Shark and YOLO.
Co-authored commits => Pair Extraordinaire for both author and co-author.

Usage:
  GH_TOKEN=... GH_OWNER=... python3 bot.py [--coauthor "NAME <email>"] [--count N] [--delay 4]
"""
import argparse, base64, os, sys, time
import requests

API = "https://api.github.com"


def headers(token):
    return {"Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"}


def req(token, method, path, expect=200, **kw):
    r = requests.request(method, API + path, headers=headers(token), **kw)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        sys.exit(f"[FATAL] rate limited: {r.text[:200]}")
    if r.status_code != expect:
        return r.status_code, r.text
    return r.status_code, (r.json() if r.text else {})


def ensure_repo(token, owner, repo, public=True):
    code, _ = req(token, "GET", f"/repos/{owner}/{repo}", expect=404)
    if code == 404:
        print(f"[repo] creating {owner}/{repo} {'public' if public else 'private'}")
        req(token, "POST", "/user/repos",
            json={"name": repo, "public": public, "auto_init": True,
                  "description": "achievement farm"}, expect=201)
        for _ in range(30):
            time.sleep(1)
            code, body = req(token, "GET", f"/repos/{owner}/{repo}", expect=200)
            if code == 200 and body.get("default_branch"):
                return body["default_branch"]
        sys.exit("[FATAL] repo did not initialize")
    _, body = req(token, "GET", f"/repos/{owner}/{repo}", expect=200)
    return body["default_branch"]


def get_file(token, owner, repo, path, branch):
    code, body = req(token, "GET", f"/repos/{owner}/{repo}/contents/{path}",
                     params={"ref": branch}, expect=200)
    if code == 404:
        return "", None
    return base64.b64decode(body["content"]).decode("utf-8"), body["sha"]


def create_branch(token, owner, repo, base, new):
    _, sha = req(token, "GET", f"/repos/{owner}/{repo}/git/ref/heads/{base}", expect=200)
    req(token, "POST", f"/repos/{owner}/{repo}/git/refs",
        json={"ref": f"refs/heads/{new}", "sha": sha["object"]["sha"]}, expect=201)


def update_file(token, owner, repo, path, branch, content, sha, msg):
    payload = {"message": msg,
               "content": base64.b64encode(content.encode()).decode(),
               "branch": branch}
    if sha:
        payload["sha"] = sha
    req(token, "PUT", f"/repos/{owner}/{repo}/contents/{path}",
        json=payload, expect=200)


def open_pr(token, owner, repo, head, base, n, coauthor):
    body = f"auto {n}" + (f"\n\nCo-authored-by: {coauthor}" if coauthor else "")
    _, pr = req(token, "POST", f"/repos/{owner}/{repo}/pulls",
                json={"title": f"auto PR {n}", "head": head, "base": base,
                      "body": body}, expect=201)
    return pr["number"]


def merge_pr(token, owner, repo, num, coauthor):
    payload = {"commit_title": f"merge PR #{num}"}
    if coauthor:
        payload["commit_message"] = f"merge PR #{num}\n\nCo-authored-by: {coauthor}"
    req(token, "PUT", f"/repos/{owner}/{repo}/pulls/{num}/merge", json=payload, expect=200)


def quickdraw(token, owner, repo, n):
    _, issue = req(token, "POST", f"/repos/{owner}/{repo}/issues",
                   json={"title": f"auto issue {n}", "body": f"auto {n}"}, expect=201)
    num = issue["number"]
    req(token, "PATCH", f"/repos/{owner}/{repo}/issues/{num}",
        json={"state": "closed"}, expect=200)
    return num


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=os.environ.get("GH_TOKEN"))
    ap.add_argument("--owner", default=os.environ.get("GH_OWNER"))
    ap.add_argument("--repo", default="achievement-farm")
    ap.add_argument("--file", default="README.md")
    ap.add_argument("--count", type=int, default=2)
    ap.add_argument("--delay", type=float, default=4)
    ap.add_argument("--coauthor",
                    help='"Name <email>" to sign commits with (Pair Extraordinaire)')
    args = ap.parse_args()

    if not args.token or not args.owner:
        sys.exit("set GH_TOKEN and GH_OWNER (or --token/--owner)")
    token, owner, coa = args.token, args.owner, args.coauthor

    base = ensure_repo(token, owner, args.repo)
    print(f"[ok] {owner}/{args.repo} base={base} file={args.file} coauthor={coa}\n")

    for n in range(1, args.count + 1):
        ts = int(time.time())
        br = f"auto-{n}-{ts}"
        print(f"[{n}/{args.count}] create branch {br}")
        create_branch(token, owner, args.repo, base, br)

        content, sha = get_file(token, owner, args.repo, args.file, br)
        content = (content or "") + "\n" + ("A" * n)
        msg = f"auto update {n}"
        if coa:
            msg += f"\n\nCo-authored-by: {coa}"
        update_file(token, owner, args.repo, args.file, br, content, sha, msg)
        print(f"[{n}/{args.count}] README updated (co-authored={bool(coa)})")

        pr = open_pr(token, owner, args.repo, br, base, n, coa)
        print(f"[{n}/{args.count}] opened PR #{pr}")
        merge_pr(token, owner, args.repo, pr, coa)
        print(f"[{n}/{args.count}] merged PR #{pr}  -> YOLO + Pull Shark"
              + (" + Pair Extraordinaire" if coa else ""))

        qi = quickdraw(token, owner, args.repo, n)
        print(f"[{n}/{args.count}] Quickdraw: issue #{qi} opened+closed in <5min")

    print(f"\n[done] {args.count} cycles. "
          + ("Badges: Quickdraw, YOLO, Pull Shark, Pair Extraordinaire." if coa
             else "Badges: Quickdraw, YOLO, Pull Shark."))


if __name__ == "__main__":
    main()
