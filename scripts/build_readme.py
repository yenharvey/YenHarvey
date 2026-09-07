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


def warn(msg: str) -> None:
    """在 GitHub Actions 里显示为黄色 warning 注解。"""
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::warning::{msg}", flush=True)
    log(f"WARNING: {msg}")


def check_token() -> None:
    """token 缺失、无效或 14 天内过期时发出 warning。"""
    if not TOKEN:
        warn("No token: private repositories will not be counted; cached stats will be used.")
        return
    data, headers = api("/user")
    if data is None:
        warn("Token rejected by GitHub API; cached stats will be used.")
        return
    exp = headers.get("github-authentication-token-expiration") or headers.get("GitHub-Authentication-Token-Expiration")
    if not exp:
        return
    try:
        expires = datetime.strptime(exp.split(" UTC")[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        log(f"token expires: {exp}")
        return
    days = (expires - datetime.now(timezone.utc)).days
    if days <= 14:
        warn(f"METRICS_TOKEN expires in {days} days ({exp}). Create a new PAT and run: gh secret set METRICS_TOKEN -R yenharvey/yenharvey")
    else:
        log(f"token ok, expires in {days} days")


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
        ["tokei", "--output", "json", "--exclude", "vendor", "--exclude", "node_modules",
         "--exclude", "dist", "--exclude", "build", "--exclude", ".next", "--exclude", "*.min.js", str(dest)],
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
                warn(f"project '{key}': some repositories unreachable, cached stats used.")
            else:
                result[key] = {"commits": 0, "lines": {}}
                log("  no data")
    return result


LANG_COLORS = {
    "Rust": "#dea584", "TypeScript": "#3178c6", "Python": "#3572A5", "Svelte": "#ff3e00",
    "JavaScript": "#f1e05a", "Dart": "#00B4AB", "Go": "#00ADD8", "C": "#555555",
    "C++": "#f34b7d", "C#": "#178600", "Vue": "#41b883", "SQL": "#e38c00",
    "Kotlin": "#A97BFF", "Swift": "#F05138", "Java": "#b07219",
}
SKIP_REPOS = {"yenharvey/yenharvey"}


def list_all_repos() -> list[str] | None:
    """当前 token 能看到的全部非 fork、非归档仓库（个人 + 协作 + 组织）。"""
    repos: list[str] = []
    page = 1
    while True:
        data, _ = api(f"/user/repos?per_page=100&page={page}&affiliation=owner,collaborator,organization_member")
        if data is None:
            return None
        if not data:
            break
        for r in data:
            if r.get("fork") or r.get("archived") or r["full_name"] in SKIP_REPOS:
                continue
            repos.append(r["full_name"])
        page += 1
    return repos


def collect_languages(cache: dict) -> dict:
    repos = list_all_repos()
    if not repos:
        log("languages: cannot list repos, using cache")
        return cache.get("languages", {"repos": 0, "lines": {}})
    log(f"[languages] {len(repos)} repos")
    lines: dict[str, int] = {}
    counted = 0
    with tempfile.TemporaryDirectory() as tmp:
        for repo in repos:
            l = clone_and_count(repo, Path(tmp))
            if l is None:
                continue
            counted += 1
            for lang, n in l.items():
                lines[lang] = lines.get(lang, 0) + n
    log(f"  counted {counted} repos, {summarize(lines, 4)}")
    failed = len(repos) - counted
    if failed:
        warn(f"{failed} of {len(repos)} repositories could not be cloned; check the token and org PAT policies.")
    cached = cache.get("languages", {})
    if counted < cached.get("repos", 0):
        log(f"  fewer repos than cached ({cached['repos']}), keeping cached languages")
        return cached
    return {"repos": counted, "lines": lines}


def render_language_card(langs: dict, dark: bool) -> str:
    """一张自托管的语言分布卡片：堆叠条 + 图例。"""
    fg, muted, bg, border = ("#e6edf3", "#8b949e", "#0d1117", "#30363d") if dark else ("#1f2328", "#59636e", "#ffffff", "#d0d7de")
    items = sorted(langs["lines"].items(), key=lambda kv: -kv[1])
    total = sum(n for _, n in items) or 1
    top = items[:8]
    other = total - sum(n for _, n in top)
    if other > 0:
        top.append(("Other", other))
    width, pad = 800, 24
    bar_w = width - pad * 2
    rows = (len(top) + 1) // 2
    height = 96 + rows * 26 + 20
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="ui-sans-serif, -apple-system, \'Segoe UI\', Helvetica, Arial, sans-serif">']
    out.append(f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="12" fill="{bg}" stroke="{border}"/>')
    out.append(f'<text x="{pad}" y="38" font-size="18" font-weight="600" fill="{fg}">Languages</text>')
    out.append(f'<text x="{width-pad}" y="38" font-size="13" text-anchor="end" fill="{muted}">{langs["repos"]} repositories · {fmt_k(total)} lines of code · private &amp; org repos included</text>')
    out.append(f'<clipPath id="bar"><rect x="{pad}" y="54" width="{bar_w}" height="12" rx="6"/></clipPath>')
    x = float(pad)
    for lang, n in top:
        w = bar_w * n / total
        out.append(f'<rect x="{x:.1f}" y="54" width="{w:.1f}" height="12" fill="{LANG_COLORS.get(lang, "#8b949e")}" clip-path="url(#bar)"/>')
        x += w
    for i, (lang, n) in enumerate(top):
        col, row = i % 2, i // 2
        lx = pad + col * (bar_w // 2)
        ly = 96 + row * 26
        out.append(f'<circle cx="{lx+6}" cy="{ly-4}" r="6" fill="{LANG_COLORS.get(lang, "#8b949e")}"/>')
        out.append(f'<text x="{lx+20}" y="{ly}" font-size="14" fill="{fg}">{lang}</text>')
        out.append(f'<text x="{lx+150}" y="{ly}" font-size="14" fill="{muted}">{100*n/total:.1f}%</text>')
        out.append(f'<text x="{lx+215}" y="{ly}" font-size="14" fill="{muted}">{fmt_k(n)} lines</text>')
    out.append("</svg>\n")
    return "\n".join(out)


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
    values["languages.repos"] = str(stats["languages"]["repos"])

    def sub(m: re.Match) -> str:
        key = m.group(1).strip()
        if key not in values:
            log(f"template: unknown placeholder {{{{{key}}}}}")
            return "—"
        return values[key]

    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", sub, text)


def main() -> int:
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    if "--from-cache" in sys.argv:
        if not cache:
            log("no cache to render from")
            return 1
        stats = cache
    else:
        check_token()
        stats = {
            "projects": collect_projects(cache),
            "languages": collect_languages(cache),
            "blog": collect_blog(cache),
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
    CACHE.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT.write_text(render(stats), encoding="utf-8")
    for dark in (False, True):
        card = ROOT / "assets" / f"languages-{'dark' if dark else 'light'}.svg"
        card.write_text(render_language_card(stats["languages"], dark), encoding="utf-8")
    log(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
