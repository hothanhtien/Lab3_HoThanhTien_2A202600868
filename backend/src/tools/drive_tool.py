from typing import List, Dict

MOCK_DATA: List[Dict] = [
    {
        "type": "folder",
        "name": "Day 3 — ReAct Agents",
        "url": "https://drive.google.com/drive/folders/day3",
        "contents": ["Day3_ReAct_Agents_Lecture.pdf", "Lab3_Instructions.pdf", "Lab3_Demo_Video.mp4"],
    },
    {
        "type": "file",
        "name": "Day3_ReAct_Agents_Lecture.pdf",
        "url": "https://drive.google.com/file/day3-lecture",
        "uploaded": "2026-06-01",
        "description": "Lecture slides for Day 3: ReAct pattern, tool design, tracing and evaluation.",
    },
    {
        "type": "file",
        "name": "Lab3_Demo_Video.mp4",
        "url": "https://drive.google.com/file/lab3-demo",
        "uploaded": "2026-06-01",
        "description": "Demo video showing a working ReAct agent answering multi-step questions.",
    },
    {
        "type": "file",
        "name": "Course_Syllabus.pdf",
        "url": "https://drive.google.com/file/syllabus",
        "uploaded": "2026-05-28",
        "description": "Full course syllabus: schedule, grading policy, tools required.",
    },
    {
        "type": "folder",
        "name": "All Labs — Starter Code",
        "url": "https://drive.google.com/drive/folders/labs",
        "contents": ["Lab1_starter.zip", "Lab2_starter.zip", "Lab3_starter.zip"],
    },
]


def search(query: str) -> str:
    """Search Google Drive for course files and folders."""
    query_lower = query.lower()
    keywords = query_lower.split()
    results = [
        item for item in MOCK_DATA
        if any(kw in str(item).lower() for kw in keywords)
    ]
    if not results:
        return "No relevant Google Drive files found."
    output = []
    for r in results[:3]:
        if r["type"] == "folder":
            output.append(
                f"[Drive Folder] {r['name']}\nURL: {r['url']}\nContents: {', '.join(r['contents'])}"
            )
        else:
            output.append(
                f"[Drive File] {r['name']}\nURL: {r['url']} | Uploaded: {r.get('uploaded', 'N/A')}\n"
                f"{r.get('description', '')}"
            )
    return "\n\n".join(output)


TOOL_SPEC = {
    "name": "drive_tool",
    "description": (
        "Search Google Drive for course files, lecture slides, demo videos, and starter code zips. "
        "Use for: finding where slides are stored, downloading lab materials, video demos."
    ),
    "func": search,
}
