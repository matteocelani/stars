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
    """Categorize repositories using keyword scoring across topics, description, name.

    Each keyword that matches contributes:
      +2 if it appears as an exact GitHub topic
      +1 if it appears as a word-boundary match in the description
      +1 if it appears as a word-boundary match in the repo name
    The category with the strictly highest score wins. Repos with score 0
    (no signal at all) fall into "Other Projects".

    Category order below is intentional: on ties, the earlier category wins,
    so put more specific/distinctive categories first.
    """
    categorized = defaultdict(list)

    type_keywords = {
        "Web3, Blockchain & Crypto": [
            "web3", "blockchain", "crypto", "cryptocurrency", "dapp", "token",
            "evm", "wallet",
            "ethereum", "bitcoin", "nostr", "lightning-network",
            "solidity", "vyper", "smart-contract", "smart-contracts", "hardhat",
            "foundry", "wagmi", "viem", "ethers", "ethersjs", "rainbowkit",
            "connectkit", "multicall", "openzeppelin",
            "aave", "uniswap", "flash-loan", "nft", "defi", "erc20", "erc721",
            "solhint", "slither",
        ],
        "Machine Learning & AI": [
            "ai", "artificial-intelligence", "machine-learning", "deep-learning",
            "neural-network", "nlp", "computer-vision", "generative",
            "generative-ai", "language-model",
            "llm", "llms", "gpt", "gpt-3", "gpt-4", "gpt-5", "chatgpt", "claude",
            "anthropic", "deepseek", "gemini", "openai", "ollama",
            "stable-diffusion",
            "tensorflow", "pytorch", "keras", "scikit-learn", "huggingface",
            "langchain", "rag", "lm-evaluation", "mlx",
            "agent", "agents", "ai-agents", "ai-tools", "agentic", "skills",
            "mcp", "claude-code", "chatbot", "assistant",
        ],
        "Data Science & Analytics": [
            "data-science", "datascience", "data-analysis", "analytics",
            "pandas", "numpy", "polars", "jupyter", "matplotlib", "seaborn",
            "scipy", "statsmodels", "dataframe", "etl", "time-series",
            "data-engineering", "visualisation",
            "f1", "motorsport",
        ],
        "Security & Privacy": [
            "security", "cybersecurity", "infosec", "cryptography", "hacking",
            "pentesting", "osint", "reconnaissance", "static-analysis",
            "authentication", "authorization", "auth", "oauth", "oauth2", "jwt",
            "malware", "credentials", "secret", "social-engineer", "trufflehog",
            "vulnerability", "encryption",
        ],
        "Self-Hosting & Home Server": [
            "self-hosted", "homelab", "home-server", "home-cloud",
            "personal-cloud", "personal-server", "home-automation", "ha-addon",
            "homeassistant", "home-assistant", "smart-home", "iot",
            "firmware", "zigbee", "esp32", "esp8266", "raspberry-pi",
            "casaos", "umbrel", "iptv", "media-server",
        ],
        "SEO & Marketing": [
            "seo", "marketing", "marketing-automation", "growth", "copywriting",
            "social-media", "scheduling", "scheduling-tool",
            "social-media-scheduling-tool",
        ],
        "Mobile & Desktop Development": [
            "mobile", "android", "ios", "react-native", "flutter", "dart",
            "swift", "swiftui", "kotlin", "macos", "windows",
            "cross-platform", "capacitor", "ionic", "apple-silicon",
            "localsend", "electron", "tauri",
        ],
        "DevOps, Cloud & Infrastructure": [
            "devops", "docker", "kubernetes", "k8s", "helm", "terraform",
            "ansible", "ci-cd", "github-actions", "gitlab-ci", "jenkins",
            "aws", "gcp", "azure", "cloud", "serverless", "deployment",
            "infrastructure", "monitoring", "observability", "prometheus",
            "grafana",
        ],
        "Backend, APIs & Databases": [
            "backend", "api", "server", "express", "expressjs", "fastapi",
            "django", "flask", "graphql", "rest", "nest", "laravel", "spring",
            "ruby-on-rails", "microservices", "nodejs", "websockets",
            "notification", "notifications",
            "database", "sql", "nosql", "postgresql", "mysql", "mongodb",
            "redis", "prisma", "orm", "sqlite", "drizzle", "supabase",
            "firebase",
        ],
        "Frontend & UI": [
            "react", "reactjs", "vue", "angular", "svelte", "solid", "preact",
            "next", "nextjs", "nuxt", "gatsby",
            "css", "ui", "tailwind", "tailwindcss", "components",
            "component-library", "web-components", "html", "shadcn-ui",
            "heroui", "nextui", "frontend",
            "animation", "animations", "motion", "glassmorphism", "datepicker",
            "mafs", "hooks", "hook", "fetch", "query", "swr",
            "chart", "charts", "charting-library", "d3", "visualization",
            "data-visualization", "data-viz", "dashboard", "recharts",
            "echarts", "plotly",
            "maps", "leaflet", "mapbox", "webgl", "formula1",
        ],
        "Developer Tools": [
            "cli", "terminal", "command-line", "utility", "shell", "bash",
            "zsh", "tui", "dotfiles",
            "editor", "ide", "vim", "neovim", "emacs", "vscode", "theme",
            "themes", "terminal-themes", "color-schemes", "plugins",
            "markdown", "remark", "ast", "parser", "compiler", "interpreter",
            "i18n", "l10n", "internationalization", "localization",
            "translation",
            "keyboard", "remap", "nuphy",
            "readme", "profile-readme", "readme-generator", "readme-stats",
            "obsidian", "notion", "knowledge-base", "todo", "pkm", "notes",
            "productivity", "programming-language",
            "testing", "test", "e2e", "jest", "cypress", "playwright",
            "vitest", "mocha", "qa", "mock", "mocking", "faker",
        ],
        "Guides, Books & Resources": [
            "awesome", "awesome-list", "curated-list",
            "tutorial", "guide", "education", "learning", "course",
            "roadmap", "books", "book", "resources", "interview", "handbook",
            "documentation",
        ],
    }

    for repo in repos:
        name = repo["full_name"]
        url = repo["html_url"]
        desc = repo.get("description") or "No description provided."
        topics = [t.lower() for t in repo.get("topics", [])]
        language = repo.get("language") or "Unknown"

        repo_name_lower = name.lower().split("/")[-1]
        desc_lower = desc.lower()

        best_category = None
        best_score = 0

        for category, keywords in type_keywords.items():
            score = 0
            for kw in keywords:
                if kw in topics:
                    score += 2
                if re.search(r"\b" + re.escape(kw) + r"\b", desc_lower):
                    score += 1
                if re.search(r"\b" + re.escape(kw) + r"\b", repo_name_lower):
                    score += 1

            # Strict ">" so ties keep the earlier (more specific) category.
            # Score must be > 0 to assign — otherwise fall to "Other Projects".
            if score > best_score:
                best_score = score
                best_category = category

        if best_category:
            categorized[best_category].append(f"- [{name}]({url}) — {desc}")
        else:
            lang_suffix = f" ({language})" if language != "Unknown" else ""
            categorized["Other Projects"].append(
                f"- [{name}]({url}) — {desc}{lang_suffix}"
            )

    return categorized

def _github_anchor(heading):
    """Generate a GitHub-compatible heading anchor.

    Mirrors GitHub's algorithm: lowercase, drop non-word/non-space/non-hyphen
    characters, then replace spaces with hyphens. Consecutive hyphens are
    preserved (GitHub does not collapse them).
    """
    anchor = heading.lower()
    anchor = re.sub(r"[^\w\s-]", "", anchor)
    anchor = re.sub(r"\s", "-", anchor)
    return anchor

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
        f.write("by topic, automatically updating this README.\n\n")
        f.write(f"> **{total_repos}** starred repositories across **{len(sorted_categories)}** categories — last updated on **{timestamp}**\n\n")

        # Table of contents
        f.write("---\n\n")
        f.write("## Table of Contents\n\n")
        for category in sorted_categories:
            anchor = _github_anchor(category)
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