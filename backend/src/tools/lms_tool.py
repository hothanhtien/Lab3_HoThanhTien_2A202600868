from typing import List, Dict

MOCK_DATA: List[Dict] = [
    {
        "type": "assignment",
        "title": "Lab 3: Chatbot vs ReAct Agent",
        "deadline": "2026-06-01 23:59",
        "points": 100,
        "submit_url": "https://lms.aivn.vn/courses/1/assignments/lab3",
        "description": "Implement a ReAct agent with at least 2 tools. Submit code + group report + individual report.",
    },
    {
        "type": "assignment",
        "title": "Lab 2: FastAPI + OpenAI Integration",
        "deadline": "2026-05-29 23:59",
        "points": 100,
        "submit_url": "https://lms.aivn.vn/courses/1/assignments/lab2",
        "description": "Build a REST API with FastAPI that integrates OpenAI chat completion.",
    },
    {
        "type": "rubric",
        "title": "Lab 3 Scoring Rubric",
        "content": (
            "Group Score (max 60): Chatbot Baseline 2pt, Agent v1 7pt, Agent v2 7pt, "
            "Tool Design 4pt, Trace Quality 9pt, Evaluation 7pt, Flowchart 5pt, Code Quality 4pt. "
            "Bonus (max +15): Extra Monitoring +3, Extra Tools +2, Failure Handling +3, Live Demo +5, Ablation +2. "
            "Individual Score (max 40): Technical Contribution 15pt, Debugging Case Study 10pt, "
            "Personal Insights 10pt, Future Improvements 5pt."
        ),
    },
    {
        "type": "course_info",
        "title": "Course Schedule",
        "content": (
            "Day 1 (28/05): Python + OpenAI API basics. "
            "Day 2 (29/05): AI Product Design. "
            "Day 3 (01/06): ReAct Agents. "
            "Day 4 (02/06): Multi-Agent Systems. "
            "Final Project deadline: 05/06/2026."
        ),
    },
]


def search(query: str) -> str:
    """Search LMS for assignments, deadlines, rubrics, and course info."""
    query_lower = query.lower()
    keywords = query_lower.split()
    results = [
        item for item in MOCK_DATA
        if any(kw in str(item).lower() for kw in keywords)
    ]
    if not results:
        return "No relevant LMS content found."
    output = []
    for r in results[:3]:
        if r["type"] == "assignment":
            output.append(
                f"[LMS Assignment] {r['title']}\n"
                f"Deadline: {r['deadline']} | Points: {r['points']}\n"
                f"Submit: {r['submit_url']}\n{r['description']}"
            )
        else:
            output.append(f"[LMS {r['type'].title()}] {r['title']}\n{r['content']}")
    return "\n\n".join(output)


TOOL_SPEC = {
    "name": "lms_tool",
    "description": (
        "Search the Learning Management System (LMS) for assignments, deadlines, "
        "rubrics, scoring criteria, and course schedule. "
        "Use for: submission deadlines, point breakdown, assignment requirements."
    ),
    "func": search,
}
