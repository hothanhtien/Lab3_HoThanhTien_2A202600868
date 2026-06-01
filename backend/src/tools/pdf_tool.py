from typing import List, Dict

MOCK_DATA: List[Dict] = [
    {
        "file": "Day3_ReAct_Agents_Lecture.pdf",
        "page": 5,
        "content": (
            "ReAct = Reasoning + Acting. The agent alternates between Thought (reasoning), "
            "Action (tool call), and Observation (tool result). This loop continues until "
            "the agent produces a Final Answer."
        ),
    },
    {
        "file": "Day3_ReAct_Agents_Lecture.pdf",
        "page": 12,
        "content": (
            "System Prompt Template for ReAct:\n"
            "You have access to: [list tools]. Use format:\n"
            "Thought: your reasoning\nAction: tool_name(argument)\n"
            "Observation: tool result\nFinal Answer: your answer"
        ),
    },
    {
        "file": "Lab3_Instructions.pdf",
        "page": 1,
        "content": (
            "Lab 3 Objectives: 1) Build chatbot baseline. 2) Implement ReAct loop with 2+ tools. "
            "3) Compare chatbot vs agent performance. 4) Document failure traces. "
            "5) Submit group report + individual report."
        ),
    },
    {
        "file": "Lab3_Instructions.pdf",
        "page": 3,
        "content": (
            "Grading: Group score max 60 (base 45 + bonus 15). Individual score max 40. "
            "Total = MIN(60, group_base + group_bonus) + individual. "
            "Fail Early Learn Fast: document your failures — it's worth points!"
        ),
    },
    {
        "file": "Course_Syllabus.pdf",
        "page": 2,
        "content": (
            "Course: Agentic AI Bootcamp (5 days). Tools used: Python, FastAPI, OpenAI API, "
            "Docker, LangGraph (Day 4-5). Evaluation: 5 labs (100pts each) + final project."
        ),
    },
]


def search(query: str) -> str:
    """Search PDF documents (lecture slides, lab instructions, syllabus)."""
    query_lower = query.lower()
    keywords = query_lower.split()
    results = [
        item for item in MOCK_DATA
        if any(kw in item["content"].lower() or kw in item["file"].lower() for kw in keywords)
    ]
    if not results:
        return "No relevant PDF content found."
    output = []
    for r in results[:3]:
        output.append(f"[PDF: {r['file']} | Page {r['page']}]\n{r['content']}")
    return "\n\n".join(output)


TOOL_SPEC = {
    "name": "pdf_tool",
    "description": (
        "Search PDF documents including lecture slides, lab instruction PDFs, and course syllabus. "
        "Use for: concept explanations, lab objectives, grading criteria from official documents."
    ),
    "func": search,
}
