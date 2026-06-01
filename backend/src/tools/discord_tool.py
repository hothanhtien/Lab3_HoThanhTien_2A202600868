from typing import List, Dict

MOCK_DATA: List[Dict] = [
    {
        "channel": "#announcements",
        "date": "2026-06-01",
        "author": "TA_Minh",
        "content": "Lab 3 deadline is TODAY 01/06/2026 at 23:59. Submit via LMS. No late submissions accepted.",
    },
    {
        "channel": "#announcements",
        "date": "2026-05-30",
        "author": "TA_Minh",
        "content": "Lab 3 has been released! Fork the starter repo at github.com/aivn-course/lab3 and start from branch 'main'.",
    },
    {
        "channel": "#general",
        "date": "2026-06-01",
        "author": "TA_Linh",
        "content": "Reminder: individual report must be placed in report/individual_reports/ folder before submitting.",
    },
    {
        "channel": "#q-and-a",
        "date": "2026-05-31",
        "author": "TA_Minh",
        "content": "For Lab 3, you need at least 2 tools to get Agent v1 points. More tools = bonus points.",
    },
    {
        "channel": "#general",
        "date": "2026-05-29",
        "author": "Instructor_Nam",
        "content": "Day 3 lecture slides have been uploaded to Google Drive. Check the #resources channel for the link.",
    },
    {
        "channel": "#resources",
        "date": "2026-05-29",
        "author": "TA_Linh",
        "content": "Slide Day 3: https://drive.google.com/drive/folders/day3 — includes lecture PDF and demo video.",
    },
]


def search(query: str) -> str:
    """Search Discord messages for relevant information."""
    query_lower = query.lower()
    keywords = query_lower.split()
    results = [
        item for item in MOCK_DATA
        if any(kw in item["content"].lower() or kw in item["channel"].lower() for kw in keywords)
    ]
    if not results:
        return "No relevant Discord messages found."
    output = []
    for r in results[:3]:
        output.append(f"[Discord {r['channel']} | {r['date']} | {r['author']}]\n{r['content']}")
    return "\n\n".join(output)


TOOL_SPEC = {
    "name": "discord_tool",
    "description": (
        "Search Discord announcements and Q&A messages from TAs and instructors. "
        "Use for: latest announcements, deadline reminders, TA tips, class updates."
    ),
    "func": search,
}
