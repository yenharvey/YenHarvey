#!/usr/bin/env python3
"""从 README.template.md 生成 README.md。

数据来源：
- data/projects.json   项目 → 仓库列表
- GitHub API           每个仓库的 commit 数（需要能看到私有仓库的 token）
- tokei                浅克隆后按语言统计代码行
- 博客 RSS             最新文章列表
- data/stats.json      上一次成功的结果，作为任何一步失败时的回退
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "README.template.md"
OUTPUT = ROOT / "README.md"
PROJECTS = ROOT / "data" / "projects.json"
CACHE = ROOT / "data" / "stats.json"
BLOG_RSS = "https://yenharvey.com/rss.xml"
BLOG_LIMIT = 5

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
# 只把这些算作「代码」，配置、标记和样式不计入
CODE_LANGS = {
    "Rust", "TypeScript", "TSX", "JavaScript", "JSX", "Svelte", "Python", "Dart",
    "Go", "C", "C++", "C#", "Kotlin", "Swift", "Java", "SQL", "Vue",
}
# tokei 名称 → 展示名称
DISPLAY = {"TSX": "TypeScript", "JSX": "JavaScript"}


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def api(path: str) -> tuple[dict | list | None, dict]:
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read() or b"null"), dict(resp.headers)
    except Exception as exc:  # noqa: BLE001
        log(f"  api {path}: {exc}")
        return None, {}


def commit_count(repo: str) -> int | None:
    data, headers = api(f"/repos/{repo}/commits?per_page=1")
    if data is None:
        return None
    link = headers.get("Link", "")
    m = re.search(r'page=(\d+)>; rel="last"', link)
    return int(m.group(1)) if m else len(data)


def clone_and_count(repo: str, workdir: Path) -> dict[str, int] | None:
    dest = workdir / repo.replace("/", "__")
    url = f"https://x-access-token:{TOKEN}@github.com/{repo}.git" if TOKEN else f"https://github.com/{repo}.git"
    r = subprocess.run(
        ["git", "clone", "--depth", "1", "--quiet", url, str(dest)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        log(f"  clone {repo}: {r.stderr.strip().splitlines()[-1] if r.stderr else 'failed'}")
        return None
    r = subprocess.run(
        ["tokei", "--output", "json", "--exclude", "vendor", "--exclude", "node_modules", str(dest)],
        capture_output=True, text=True,
    )
    shutil.rmtree(dest, ignore_errors=True)
    if r.returncode != 0:
        log(f"  tokei {repo}: {r.stderr.strip()}")
        return None
    out: dict[str, int] = {}
    for lang, info in json.loads(r.stdout).items():
        if lang in CODE_LANGS:
            name = DISPLAY.get(lang, lang)
            out[name] = out.get(name, 0) + int(info["code"])
    return out


def fmt_k(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{round(n / 1_000)}k"
    return str(n)


def summarize(lines: dict[str, int], top: int = 2) -> str:
    ranked = sorted(lines.items(), key=lambda kv: -kv[1])[:top]
    return " · ".join(f"{fmt_k(n)} {lang}" for lang, n in ranked if n > 0)


def collect_projects(cache: dict) -> dict:
    projects = json.loads(PROJECTS.read_text(encoding="utf-8"))
    result: dict = {}
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        for key, spec in projects.items():
            log(f"[{key}]")
            commits = 0
            lines: dict[str, int] = {}
            ok = True
            for repo in spec["repos"]:
                c = commit_count(repo)
                l = clone_and_count(repo, workdir)
                if c is None or l is None:
                    ok = False
                    break
                commits += c
                for lang, n in l.items():
                    lines[lang] = lines.get(lang, 0) + n
            if ok:
                result[key] = {"commits": commits, "lines": lines}
                log(f"  {commits} commits, {summarize(lines, 3)}")
            elif key in cache.get("projects", {}):
                result[key] = cache["projects"][key]
                log("  fell back to cached stats")
            else:
                result[key] = {"commits": 0, "lines": {}}
                log("  no data")
    return result


def collect_blog(cache: dict) -> list[dict]:
    try:
        req = urllib.request.Request(BLOG_RSS, headers={"User-Agent": "Mozilla/5.0 (profile-readme-builder)"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            root = ET.fromstring(resp.read())
        posts = []
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            date = ""
            for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
                try:
                    date = datetime.strptime(pub, fmt).strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue
            if title and link:
                posts.append({"title": title, "link": link, "date": date})
        return posts[:BLOG_LIMIT]
    except Exception as exc:  # noqa: BLE001
        log(f"blog rss: {exc}")
        return cache.get("blog", [])


def render(stats: dict) -> str:
    text = TEMPLATE.read_text(encoding="utf-8")
    values: dict[str, str] = {}
    for key, s in stats["projects"].items():
        values[f"{key}.commits"] = f"{s['commits']:,}"
        values[f"{key}.lines"] = summarize(s["lines"]) or "—"
        for lang, n in s["lines"].items():
            values[f"{key}.lines.{lang.lower()}"] = fmt_k(n)
    blog_lines = [
        f"- {p['date']} · [{p['title']}]({p['link']})" if p["date"] else f"- [{p['title']}]({p['link']})"
        for p in stats["blog"]
    ]
    values["blog_posts"] = "\n".join(blog_lines) if blog_lines else "_No posts yet._"
    values["updated_at"] = stats["updated_at"]

    def sub(m: re.Match) -> str:
        key = m.group(1).strip()
        if key not in values:
            log(f"template: unknown placeholder {{{{{key}}}}}")
            return "—"
        return values[key]

    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", sub, text)


def main() -> int:
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    stats = {
        "projects": collect_projects(cache),
        "blog": collect_blog(cache),
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    CACHE.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT.write_text(render(stats), encoding="utf-8")
    log(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
