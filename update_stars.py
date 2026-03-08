import os
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
    """Categorize repositories by topic keywords, falling back to primary language."""
    categorized = defaultdict(list)

    # Custom categories based on tags (topics)
    type_keywords = {
        "Frontend Frameworks & Libraries": ["react", "vue", "angular", "svelte", "js", "frontend", "css", "ui", "tailwind", "next", "nuxt", "solid", "preact", "components", "web-components", "html"],
        "Backend Frameworks & Libraries": ["backend", "api", "server", "express", "django", "flask", "fastapi", "spring", "nest", "laravel", "ruby-on-rails", "graphql", "rest"],
        "Databases & ORMs": ["database", "sql", "nosql", "postgresql", "mysql", "mongodb", "redis", "prisma", "orm", "sqlite", "graphql", "drizzle", "supabase", "firebase"],
        "Machine Learning & AI": ["machine-learning", "ai", "deep-learning", "llm", "nlp", "computer-vision", "neural-network", "tensorflow", "pytorch", "keras", "scikit-learn", "openai", "huggingface", "generative-ai", "stable-diffusion"],
        "Data Science & Analytics": ["data-science", "analytics", "pandas", "numpy", "jupyter", "visualization", "matplotlib", "seaborn", "dashboard", "d3", "streamlit"],
        "DevOps & Infrastructure": ["devops", "docker", "kubernetes", "kubernetes-ingress", "terraform", "ansible", "ci-cd", "github-actions", "aws", "infrastructure", "cloud", "serverless", "deployment"],
        "CLI Tools & Utilities": ["cli", "terminal", "command-line", "tool", "utility", "shell", "bash", "zsh", "tui", "dotfiles"],
        "Security & Cryptography": ["security", "cryptography", "hacking", "pentesting", "authentication", "authorization", "oauth", "jwt", "malware", "cybersecurity"],
        "Game Development": ["game-engine", "gamedev", "unity", "unreal-engine", "godot", "phaser", "pygame", "webgl", "threejs"],
        "Mobile Development": ["mobile", "android", "ios", "react-native", "flutter", "swift", "kotlin", "capacitor", "ionic"],
        "Web3 & Blockchain": ["web3", "blockchain", "crypto", "ethereum", "smart-contracts", "solidity", "bitcoin", "nft", "defi"],
        "Testing & QA": ["testing", "qa", "jest", "cypress", "playwright", "selenium", "mocha", "vitest", "automation", "e2e"],
        "Guides & Tutorials": ["awesome", "tutorial", "guide", "education", "learning", "course", "roadmap", "books", "resources", "interview"],
        "Design & Graphics": ["design", "graphics", "ui-ux", "figma", "svg", "animation", "motion", "canvas"],
        "Productivity & Notes": ["productivity", "notes", "markdown", "obsidian", "notion", "knowledge-base", "todo", "pkm"],
        "Editors & IDEs": ["editor", "ide", "vim", "neovim", "emacs", "vscode", "plugins", "theme"],
        "Languages & Compilers": ["programming-language", "compiler", "interpreter", "ast", "parser"]
    }

    for repo in repos:
        name = repo['full_name']
        url = repo['html_url']
        desc = repo.get('description') or "No description provided."
        topics = repo.get('topics', [])
        language = repo.get('language') or "Unknown"

        # Try to categorize by topic keywords
        assigned_category = None
        for category, keywords in type_keywords.items():
            if any(keyword in topics for keyword in keywords):
                assigned_category = category
                break

        # Fall back to the primary programming language
        if not assigned_category:
            assigned_category = f"Language: {language}"

        categorized[assigned_category].append(f"- [{name}]({url}) — {desc}")

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