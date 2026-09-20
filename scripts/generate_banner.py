#!/usr/bin/env python3
"""
Generates a sleek "Aurora Glassmorphism" GitHub profile banner.
"""
import os
import sys
import json
import urllib.request
import datetime
import math
import re

def ordinal_suffix(day):
    if 11 <= day <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

def format_ist_now():
    utc = datetime.datetime.now(datetime.timezone.utc)
    ist = utc + datetime.timedelta(hours=5, minutes=30)
    suffix = ordinal_suffix(ist.day)
    return ist.strftime(f"%d{suffix} %B %Y · %I:%M %p IST")

USERNAME = os.environ.get("GITHUB_USERNAME", "paninieywa")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

def api_call(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "paninieywa-banner-generator")
    if TOKEN:
        req.add_header("Authorization", f"token {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            link = resp.headers.get("Link", "")
            return data, link
    except Exception as e:
        print(f"API error for {url}: {e}", file=sys.stderr)
        return [], ""

def get_total_commits(repo_name, default_branch):
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits?sha={default_branch}&per_page=1"
    data, link = api_call(url)
    if link:
        matches = re.findall(r'<[^>]*[?&]page=(\d+)[^>]*>;\s*rel="last"', link)
        if matches:
            return int(matches[-1])
    if isinstance(data, list):
        return len(data)
    return 0

def fetch_all_repos():
    all_repos = []
    page = 1
    while page <= 10:
        url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&page={page}&sort=updated"
        repos, _ = api_call(url)
        if not isinstance(repos, list) or not repos:
            break
        all_repos.extend(repos)
        if len(repos) < 100:
            break
        page += 1
    return all_repos

def fetch_stats():
    user, _ = api_call(f"https://api.github.com/users/{USERNAME}")
    repos = fetch_all_repos()

    lang_stats = {}
    total_bytes = 0
    stars = 0
    total_commits = 0

    SKIP_LANGS = {"Markdown", "JSON", "YAML", "TOML", "TeX", "BitBake", "Batchfile", "PowerShell", "Jupyter Notebook"}

    for r in repos:
        stars += r.get("stargazers_count", 0)
        default = r.get("default_branch") or "main"
        try:
            total_commits += get_total_commits(r["name"], default)
        except Exception:
            pass

        lang_url = r.get("languages_url")
        if lang_url:
            langs, _ = api_call(lang_url)
            if isinstance(langs, dict):
                for lang, bytes_count in langs.items():
                    if lang in SKIP_LANGS:
                        continue
                    lang_stats[lang] = lang_stats.get(lang, 0) + bytes_count
                    total_bytes += bytes_count

    sorted_langs = sorted(lang_stats.items(), key=lambda x: x[1], reverse=True)[:6]
    total_for_pct = total_bytes or 1
    lang_percentages = []
    for lang, bytes_count in sorted_langs:
        pct = round((bytes_count / total_for_pct) * 100, 1)
        lang_percentages.append((lang, pct))

    # LOC Calculation
    LANG_DIVISOR = {"TypeScript": 22, "JavaScript": 22, "Python": 24, "Java": 22, "C++": 20, "C": 20, "C#": 22, "Go": 22, "Rust": 22, "Ruby": 24, "PHP": 22, "Swift": 22, "Kotlin": 22, "Dockerfile": 30, "Shell": 28, "HTML": 30, "CSS": 28}
    estimated_loc = 0
    for lang, b in lang_stats.items():
        estimated_loc += b // LANG_DIVISOR.get(lang, 22)

    return {
        "repos": len(repos),
        "stars": stars,
        "commits": total_commits,
        "loc_str": f"{estimated_loc:,}",
        "languages": lang_percentages,
        "name": user.get("name", USERNAME) or USERNAME,
    }

LANG_COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "HTML": "#e34c26",
    "CSS": "#563d7c", "Python": "#3776ab", "C++": "#f34b7d",
    "Java": "#b07219", "Dockerfile": "#384d54", "Shell": "#89e051",
    "Go": "#00add8", "Rust": "#dea584", "Ruby": "#cc342d",
    "PHP": "#4f5d95", "Swift": "#ffac45", "Kotlin": "#a97bff",
    "C": "#555555", "C#": "#178600",
}

def get_lang_color(lang):
    return LANG_COLORS.get(lang, "#8b949e")

def donut_chart(cx, cy, r, languages, stroke_width=14):
    if not languages:
        return ""
    circumference = 2 * math.pi * r
    segments = []
    offset = 0
    for lang, pct in languages:
        color = get_lang_color(lang)
        seg_len = (pct / 100) * circumference
        gap = circumference - seg_len
        dasharray = f"{seg_len:.2f} {gap:.2f}"
        rotate = -90 + (offset / circumference) * 360
        segments.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="{stroke_width}" stroke-dasharray="{dasharray}" '
            f'stroke-linecap="butt" transform="rotate({rotate:.2f} {cx} {cy})" opacity="0.95"/>'
        )
        offset += seg_len
    return "\n    ".join(segments)

def generate_svg(stats):
    langs = stats["languages"]
    now = format_ist_now()
    name_text = stats.get("name", USERNAME) or USERNAME

    donut_cx, donut_cy, donut_r = 690, 380, 50
    donut = donut_chart(donut_cx, donut_cy, donut_r, langs, stroke_width=14)

    # Legend
    legend_items = []
    for i, (lang, pct) in enumerate(langs[:6]):
        y = 330 + i * 25
        color = get_lang_color(lang)
        legend_items.append(
            f'<circle cx="0" cy="{y}" r="5" fill="{color}"/>'
            f'<text x="14" y="{y+4}" font-family="IBM Plex Sans, sans-serif" font-size="12" fill="#c9d1d9">{lang}</text>'
            f'<text x="120" y="{y+4}" font-family="IBM Plex Mono, monospace" font-size="12" fill="#8b949e">{pct:.1f}%</text>'
        )
    legend_svg = "\n    ".join(legend_items)

    contacts = [
        ("Reddit", "paninieywa"),
        ("Facebook", "Panini Eywa"),
        ("Email", "archivrx@gmail.com"),
        ("Google Play", "xijongputin"),
    ]
    contact_svg = ""
    for i, (label, value) in enumerate(contacts):
        y = 210 + i * 24
        contact_svg += (
            f'<text x="70" y="{y}" font-family="IBM Plex Sans, sans-serif" font-size="13" fill="#c9d1d9">'
            f'<tspan font-weight="600" fill="#ffffff">{label}</tspan>  ·  {value}</text>'
        )

    svg_template = """<?xml version="1.0" encoding="UTF-8"?>
<svg viewBox="0 0 1200 480" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#161b22"/>
    </linearGradient>
    <linearGradient id="glassGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.02"/>
    </linearGradient>
    <filter id="blurGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="40"/>
    </filter>
  </defs>

  <rect width="1200" height="480" fill="url(#bgGrad)"/>
  <circle cx="200" cy="100" r="150" fill="#7c3aed" opacity="0.15" filter="url(#blurGlow)"/>
  <circle cx="1000" cy="400" r="180" fill="#06b6d4" opacity="0.15" filter="url(#blurGlow)"/>
  <circle cx="900" cy="80" r="120" fill="#ec4899" opacity="0.1" filter="url(#blurGlow)"/>
  
  <g stroke="#ffffff" stroke-width="0.5" opacity="0.03">
    <line x1="0" y1="120" x2="1200" y2="120"/>
    <line x1="0" y1="240" x2="1200" y2="240"/>
    <line x1="0" y1="360" x2="1200" y2="360"/>
    <line x1="300" y1="0" x2="300" y2="480"/>
    <line x1="600" y1="0" x2="600" y2="480"/>
    <line x1="900" y1="0" x2="900" y2="480"/>
  </g>

  <rect x="40" y="40" width="520" height="400" rx="16" fill="url(#glassGrad)" stroke="#ffffff" stroke-opacity="0.1"/>
  <rect x="580" y="40" width="580" height="400" rx="16" fill="url(#glassGrad)" stroke="#ffffff" stroke-opacity="0.1"/>

  <!-- LEFT PANEL -->
  <text x="70" y="100" font-family="Space Grotesk, sans-serif" font-size="34" font-weight="700" fill="#ffffff" letter-spacing="0.5">{name}</text>
  <text x="70" y="130" font-family="IBM Plex Sans, sans-serif" font-size="14" fill="#8b949e">कृत्य । सहिष्णुता । मोक्षः</text>
  <line x1="70" y1="155" x2="530" y2="155" stroke="#ffffff" stroke-opacity="0.1"/>
  
  <text x="70" y="185" font-family="IBM Plex Sans, sans-serif" font-size="13" font-weight="600" fill="#58a6ff">CONNECT</text>
  {contacts}

  <line x1="70" y1="310" x2="530" y2="310" stroke="#ffffff" stroke-opacity="0.1"/>

  <text x="70" y="340" font-family="IBM Plex Sans, sans-serif" font-size="13" font-weight="600" fill="#58a6ff">PROGRAMMING</text>
  <text x="70" y="362" font-family="IBM Plex Sans, sans-serif" font-size="12" fill="#8b949e">HTML · CSS · JavaScript · TypeScript · Python · C · C++</text>

  <text x="70" y="400" font-family="IBM Plex Sans, sans-serif" font-size="13" font-weight="600" fill="#58a6ff">FRAMEWORKS</text>
  <text x="70" y="422" font-family="IBM Plex Sans, sans-serif" font-size="12" fill="#8b949e">React · Docker · Express · FastAPI · REST · GitHub · RAG</text>

  <!-- RIGHT PANEL -->
  <g transform="translate(610, 80)">
    <rect x="0" y="0" width="250" height="100" rx="12" fill="rgba(255,255,255,0.03)" stroke="#ffffff" stroke-opacity="0.08"/>
    <text x="20" y="40" font-family="IBM Plex Mono, monospace" font-size="32" font-weight="700" fill="#ffffff">{repos}</text>
    <text x="20" y="70" font-family="IBM Plex Sans, sans-serif" font-size="12" fill="#8b949e">Public Repos</text>
    
    <rect x="270" y="0" width="250" height="100" rx="12" fill="rgba(255,255,255,0.03)" stroke="#ffffff" stroke-opacity="0.08"/>
    <text x="290" y="40" font-family="IBM Plex Mono, monospace" font-size="32" font-weight="700" fill="#ffffff">{stars}</text>
    <text x="290" y="70" font-family="IBM Plex Sans, sans-serif" font-size="12" fill="#8b949e">Total Stars</text>
    
    <rect x="0" y="120" width="250" height="100" rx="12" fill="rgba(255,255,255,0.03)" stroke="#ffffff" stroke-opacity="0.08"/>
    <text x="20" y="160" font-family="IBM Plex Mono, monospace" font-size="32" font-weight="700" fill="#ffffff">{commits}</text>
    <text x="20" y="190" font-family="IBM Plex Sans, sans-serif" font-size="12" fill="#8b949e">Total Commits</text>
    
    <rect x="270" y="120" width="250" height="100" rx="12" fill="rgba(255,255,255,0.03)" stroke="#ffffff" stroke-opacity="0.08"/>
    <text x="290" y="160" font-family="IBM Plex Mono, monospace" font-size="26" font-weight="700" fill="#ffffff">{loc}</text>
    <text x="290" y="190" font-family="IBM Plex Sans, sans-serif" font-size="12" fill="#8b949e">Lines of Code</text>
  </g>

  <text x="610" y="290" font-family="IBM Plex Sans, sans-serif" font-size="13" font-weight="600" fill="#58a6ff">CODE BREAKDOWN</text>
  <line x1="610" y1="300" x2="1140" y2="300" stroke="#ffffff" stroke-opacity="0.1"/>
  
  <circle cx="{dcx}" cy="{dcy}" r="{dr}" fill="none" stroke="#ffffff" stroke-opacity="0.1" stroke-width="14"/>
  {donut}
  
  <text x="{dcx}" y="{dcy}-2" text-anchor="middle" font-family="IBM Plex Sans, sans-serif" font-size="14" font-weight="700" fill="#ffffff">Top</text>
  <text x="{dcx}" y="{dcy}+16" text-anchor="middle" font-family="IBM Plex Sans, sans-serif" font-size="10" fill="#8b949e">Languages</text>

  <g transform="translate(800, 0)">
    {legend}
  </g>

  <text x="1140" y="450" text-anchor="end" font-family="IBM Plex Mono, monospace" font-size="9" fill="#8b949e">Updated: {updated}</text>
</svg>"""

    svg = svg_template.format(
        contacts=contact_svg,
        name=name_text,
        repos=stats["repos"],
        stars=stats["stars"],
        commits=stats["commits"],
        loc=stats["loc_str"],
        donut=donut,
        dcx=donut_cx,
        dcy=donut_cy,
        dr=donut_r,
        legend=legend_svg,
        updated=now,
    )
    return svg

def main():
    print("Fetching GitHub stats...")
    stats = fetch_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")
    svg = generate_svg(stats)
    out_path = "assets/github-banner.svg"
    os.makedirs("assets", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Banner written to {out_path}")

if __name__ == "__main__":
    main()
