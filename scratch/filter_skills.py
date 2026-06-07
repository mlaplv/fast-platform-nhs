import json

# Paths
index_path = "/home/lv/.gemini/antigravity/antigravity-skills/skills_index.json"

# List of skill IDs to keep
keep_skills = {
    "using-superpowers",
    "brainstorming",
    "planning-with-files",
    "writing-plans",
    "executing-plans",
    "subagent-driven-development",
    "verification-before-completion",
    "requesting-code-review",
    "receiving-code-review",
    "finishing-a-development-branch",
    "systematic-debugging",
    "test-driven-development",
    "webapp-testing",
    "frontend-design",
    "ui-ux-pro-max",
    "web-design-guidelines",
    "web-artifacts-builder",
    "supabase-postgres-best-practices",
    "claude-api",
    "mcp-builder",
    "context-compression",
    "context-optimization",
    "context-fundamentals",
    "context-degradation",
    "multi-agent-patterns",
    "dispatching-parallel-agents",
    "rtk"
}

# New skills to add
new_skills = [
    {
        "id": "svelte-runes-best-practices",
        "path": "skills/svelte-runes-best-practices",
        "name": "svelte-runes-best-practices",
        "description": "Best practices for SvelteKit 5 and Svelte Runes ($state, $derived, $effect, $props). Use this skill when writing Svelte components, SvelteKit routing, state management, page loads, or client-side logic. Enforces strict TypeScript typing and forbids Svelte 4 writable/readable stores."
    },
    {
        "id": "pydantic-ai-best-practices",
        "path": "skills/pydantic-ai-best-practices",
        "name": "pydantic-ai-best-practices",
        "description": "Best practices for PydanticAI (V2 only) and LiteLLM integrations. Use this skill when implementing AI agents, LLM tool calls, structured outputs, prompt templates, or agentic workflows."
    },
    {
        "id": "litestar-sqlalchemy-python314",
        "path": "skills/litestar-sqlalchemy-python314",
        "name": "litestar-sqlalchemy-python314",
        "description": "Best practices for Python 3.14, Litestar, and SQLAlchemy 2.0. Use this skill when writing backend API routes, controllers, database models, repository layers, or executing database migrations."
    },
    {
        "id": "advanced-review-testing-pro",
        "path": "skills/advanced-review-testing-pro",
        "name": "advanced-review-testing-pro",
        "description": "Advanced code review, bug testing, and technological reconnaissance. Use this skill when reviewing code changes, debugging complex issues, verifying performance, writing automated tests, or analyzing architecture for modern high-tier solutions."
    }
]

# Load current index
with open(index_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Filter
filtered = [item for item in data if item["id"] in keep_skills]

# Add new ones
filtered.extend(new_skills)

# Sort by id alphabetically to keep index clean
filtered.sort(key=lambda x: x["id"])

# Write back
with open(index_path, "w", encoding="utf-8") as f:
    json.dump(filtered, f, indent=2, ensure_ascii=False)

print(f"Success! Kept {len(filtered) - len(new_skills)} skills, added {len(new_skills)} new skills. Total: {len(filtered)} skills.")
