from typing import List, Dict

MOCK_DATA: List[Dict] = [
    {
        "repo": "aivn-course/lab3",
        "type": "repo",
        "url": "https://github.com/aivn-course/lab3",
        "description": "Lab 3 starter code: Chatbot vs ReAct Agent. Fork this repo to start.",
        "default_branch": "main",
        "submit_branch": "Fork the repo, work on main, submit your GitHub link on LMS.",
    },
    {
        "repo": "aivn-course/lab3",
        "type": "file",
        "path": "src/agent/agent.py",
        "description": "ReActAgent skeleton class. Implement the run() method and _execute_tool() method.",
    },
    {
        "repo": "aivn-course/lab3",
        "type": "file",
        "path": "requirements.txt",
        "description": "Dependencies: fastapi, uvicorn, openai, python-dotenv, pydantic.",
    },
    {
        "repo": "aivn-course/lab3",
        "type": "issue",
        "title": "How to run locally without Docker?",
        "answer": "cd backend && pip install -r requirements.txt && uvicorn main:app --reload",
    },
    {
        "repo": "aivn-course/lab3",
        "type": "issue",
        "title": "Which branch to submit?",
        "answer": "Fork the repo to your own GitHub account, push to main, then submit the forked repo URL on LMS.",
    },
    {
        "repo": "aivn-course/lab2",
        "type": "repo",
        "url": "https://github.com/aivn-course/lab2",
        "description": "Lab 2 reference solution: FastAPI + OpenAI. You can reuse the provider pattern.",
    },
]


def search(query: str) -> str:
    """Search GitHub repos, files, and issues for course code."""
    query_lower = query.lower()
    keywords = query_lower.split()
    results = [
        item for item in MOCK_DATA
        if any(kw in str(item).lower() for kw in keywords)
    ]
    if not results:
        return "No relevant GitHub content found."
    output = []
    for r in results[:3]:
        if r["type"] == "repo":
            output.append(
                f"[GitHub Repo] {r['repo']}\nURL: {r['url']}\n{r['description']}\n"
                f"Branch: {r.get('default_branch', 'main')} | {r.get('submit_branch', '')}"
            )
        elif r["type"] == "file":
            output.append(f"[GitHub File] {r['repo']}/{r['path']}\n{r['description']}")
        else:
            output.append(f"[GitHub Issue] {r['title']}\nAnswer: {r['answer']}")
    return "\n\n".join(output)


TOOL_SPEC = {
    "name": "github_tool",
    "description": (
        "Search GitHub repositories, files, and issues for course code and starter templates. "
        "Use for: starter repo links, which branch to use, how to run code, file structure questions."
    ),
    "func": search,
}
