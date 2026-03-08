import os
import re
import requests
from collections import defaultdict
from datetime import datetime, timezone

# Fetches your username and token automatically from GitHub Actions
USERNAME = os.getenv("GITHUB_ACTOR")
TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_starred_repos():
    """Fetch all starred repositories for the authenticated user, handling pagination."""
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{USERNAME}/starred?per_page=100&page={page}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"API request failed on page {page} (HTTP {response.status_code})")
            break
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def categorize_repos(repos):
    """Categorize repositories using deep text analysis with scoring-based assignment.

    Matches keywords against three sources per repo: topics, description, and
    the repository name. Each repo is assigned to the category with the highest
    cumulative keyword-match score. Repos that match no category are placed in
    a consolidated "Other Projects" bucket with the primary language appended.
    """
    categorized = defaultdict(list)

    # ------------------------------------------------------------------
    # Expanded taxonomy — keywords are matched case-insensitively against
    # topics (exact token match) AND description/repo-name (substring).
    # ------------------------------------------------------------------
    type_keywords = {
        "Web3, Blockchain & Crypto": [
            "web3", "blockchain", "crypto", "ethereum", "solidity", "bitcoin",
            "nft", "defi", "smart-contract", "smart-contracts", "hardhat",
            "foundry", "wagmi", "viem", "rainbowkit", "connectkit", "aave",
            "uniswap", "flash-loan", "dapp", "openzeppelin", "vyper",
            "multicall", "nostr", "lightning-network", "token", "erc20",
            "erc721", "solhint", "slither",
        ],
        "Machine Learning & AI": [
            "machine-learning", "ai", "deep-learning", "llm", "nlp",
            "computer-vision", "neural-network", "tensorflow", "pytorch",
            "keras", "scikit-learn", "openai", "huggingface", "generative-ai",
            "generative", "stable-diffusion", "deepseek", "claude", "gpt",
            "mlx", "ollama", "langchain", "rag", "lm-evaluation",
            "language-model", "anthropic", "gemini",
        ],
        "SEO & Marketing": [
            "seo", "marketing", "growth", "social-media", "scheduling",
        ],
        "Data Science & Analytics": [
            "data-science", "analytics", "pandas", "numpy", "jupyter",
            "visualization", "matplotlib", "seaborn", "dashboard", "d3",
            "streamlit", "echarts", "chart", "recharts", "plotly",
        ],
        "Frontend & UI Frameworks": [
            "react", "vue", "angular", "svelte", "frontend", "css", "ui",
            "tailwind", "next", "nuxt", "solid", "preact", "components",
            "web-components", "html", "animation", "motion", "glassmorphism",
            "datepicker", "heroui", "mafs", "nextui",
        ],
        "Backend & APIs": [
            "backend", "api", "server", "express", "django", "flask",
            "fastapi", "graphql", "rest", "nest", "laravel", "spring",
            "ruby-on-rails", "microservices",
        ],
        "Databases & Data Layer": [
            "database", "sql", "nosql", "postgresql", "mysql", "mongodb",
            "redis", "prisma", "orm", "sqlite", "drizzle", "supabase",
            "firebase",
        ],
        "DevOps, Cloud & Infrastructure": [
            "devops", "docker", "kubernetes", "terraform", "ansible", "ci-cd",
            "github-actions", "aws", "cloud", "serverless", "deployment",
            "infrastructure", "monitoring", "observability",
        ],
        "Self-Hosting & Home Server": [
            "self-hosted", "homelab", "home-server", "casaos", "umbrel",
            "personal-cloud", "iptv", "media-server",
        ],
        "Security & Cryptography": [
            "security", "cryptography", "hacking", "pentesting",
            "authentication", "authorization", "oauth", "jwt", "malware",
            "cybersecurity", "credentials", "trufflehog", "social-engineer",
            "linting", "analyzer",
        ],
        "CLI Tools & Utilities": [
            "cli", "terminal", "command-line", "utility", "shell",
            "bash", "zsh", "tui", "dotfiles", "sherlock",
        ],
        "Mobile & Desktop Development": [
            "mobile", "android", "ios", "react-native", "flutter", "swift",
            "swiftui", "kotlin", "macos", "windows", "cross-platform",
            "capacitor", "ionic", "apple-silicon", "localsend", "container",
        ],
        "Game Development & Maps": [
            "game-engine", "gamedev", "unity", "unreal-engine", "godot",
            "phaser", "pygame", "webgl", "threejs", "mapbox", "leaflet",
            "maps", "geospatial",
        ],
        "Guides, Tutorials & Resources": [
            "awesome", "tutorial", "guide", "education", "learning", "course",
            "roadmap", "books", "resources", "interview", "handbook",
            "documentation",
        ],
        "Internationalization & Localization": [
            "i18n", "l10n", "internationalization", "localization", "lingui",
            "translation",
        ],
        "Productivity & Notes": [
            "productivity", "notes", "markdown", "obsidian", "notion",
            "knowledge-base", "todo", "pkm", "remark",
        ],
        "Testing & QA": [
            "testing", "qa", "jest", "cypress", "playwright", "selenium",
            "mocha", "vitest", "automation", "e2e",
        ],
        "Editors & IDEs": [
            "editor", "ide", "vim", "neovim", "emacs", "vscode", "plugins",
            "theme",
        ],
        "Languages & Compilers": [
            "programming-language", "compiler", "interpreter", "ast", "parser",
        ],
    }

    for repo in repos:
        name = repo["full_name"]
        url = repo["html_url"]
        desc = repo.get("description") or "No description provided."
        topics = [t.lower() for t in repo.get("topics", [])]
        language = repo.get("language") or "Unknown"

        # Build a lowercase search corpus from description and repo name
        repo_name_lower = name.lower().split("/")[-1]   # e.g. "deepseek-v3"
        desc_lower = desc.lower()

        # --- Scoring: count keyword hits across topics, description, name ---
        best_category = None
        best_score = 0

        for category, keywords in type_keywords.items():
            score = 0
            for kw in keywords:
                # Exact match in topics list (highest confidence)
                if kw in topics:
                    score += 2
                # Word-boundary match in description (avoids partial matches)
                if re.search(r"\b" + re.escape(kw) + r"\b", desc_lower):
                    score += 1
                # Word-boundary match in repository name
                if re.search(r"\b" + re.escape(kw) + r"\b", repo_name_lower):
                    score += 1

            if score >= best_score:
                best_score = score
                best_category = category

        # --- Assign to best category or fall back to "Other Projects" ---
        if best_category:
            categorized[best_category].append(f"- [{name}]({url}) — {desc}")
        else:
            lang_suffix = f" ({language})" if language != "Unknown" else ""
            categorized["Other Projects"].append(
                f"- [{name}]({url}) — {desc}{lang_suffix}"
            )

    return categorized

def write_readme(categorized):
    """Generate a clean, well-structured README.md from categorized repositories."""
    total_repos = sum(len(items) for items in categorized.values())
    sorted_categories = sorted(categorized.keys())
    timestamp = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")

    with open("README.md", "w", encoding="utf-8") as f:
        # Header
        f.write("# Matteo's Stars\n\n")
        f.write("An automated, categorized list of my GitHub stars.\n\n")
        f.write("This repository uses a GitHub Action to run a Python script daily. ")
        f.write("The script fetches all my starred repositories and categorizes them ")
        f.write("by topic or programming language, automatically updating this README.\n\n")
        f.write(f"> **{total_repos}** starred repositories across **{len(sorted_categories)}** categories — last updated on **{timestamp}**\n\n")

        # Table of contents
        f.write("---\n\n")
        f.write("## Table of Contents\n\n")
        for category in sorted_categories:
            # Generate a GitHub-compatible anchor link
            anchor = category.lower().replace(" ", "-").replace("&", "").replace(":", "").replace("--", "-")
            count = len(categorized[category])
            f.write(f"- [{category}](#{anchor}) ({count})\n")
        f.write("\n")

        # Category sections
        f.write("---\n\n")
        for category in sorted_categories:
            f.write(f"## {category}\n\n")
            for item in categorized[category]:
                f.write(f"{item}\n")
            f.write("\n")

if __name__ == "__main__":
    print(f"Fetching stars for {USERNAME}...")
    repos = get_starred_repos()
    print(f"Found {len(repos)} starred repositories. Categorizing...")
    categorized_data = categorize_repos(repos)
    write_readme(categorized_data)
    print("README.md successfully updated!")