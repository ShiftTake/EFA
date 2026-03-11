
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from .schemas import Clip
import uuid

router = APIRouter()

# In-memory storage for demo
clips_db = []

@router.get("/clips", response_model=List[Clip])
def get_clips():
    return clips_db

@router.post("/clips", response_model=List[Clip])
async def create_clips(
    sourceType: str = Form(...),
    sourceUrl: str = Form(""),
    scanMode: str = Form("balanced"),
    aiInstructions: str = Form(""),
    file: UploadFile = File(None)
):
    # Validation
    if sourceType not in ["live", "link", "upload"]:
        raise HTTPException(status_code=400, detail="Invalid sourceType")
    if sourceType in ["live", "link"] and not sourceUrl:
        raise HTTPException(status_code=400, detail="URL required for live/link source")
    if sourceType == "upload":
        if not file:
            raise HTTPException(status_code=400, detail="File required for upload source")
        if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            raise HTTPException(status_code=400, detail="Unsupported file type")

    templates = [
        {"title": "HOOK MOMENT", "start": "00:12", "score": 94, "color": "#FFDE59"},
        {"title": "FUNNY REACTION", "start": "01:03", "score": 86, "color": "#FF914D"},
        {"title": "HIGH ENERGY CUT", "start": "02:11", "score": 89, "color": "#8C52FF"},
        {"title": "VALUE PACKED SEGMENT", "start": "03:09", "score": 81, "color": "#00BF63"}
    ]
    selected_templates = templates
    if "funny" in aiInstructions.lower() or "laugh" in aiInstructions.lower():
        selected_templates = [
            {"title": "FUNNY MOMENT", "start": "00:42", "score": 92, "color": "#FF914D"},
            {"title": "REACTION CLIP", "start": "01:30", "score": 87, "color": "#FFDE59"},
            {"title": "CHAT LOSING IT", "start": "02:16", "score": 84, "color": "#8C52FF"}
        ]
    elif "hook" in aiInstructions.lower() or "energy" in aiInstructions.lower() or "viral" in aiInstructions.lower():
        selected_templates = [
            {"title": "VIRAL HOOK", "start": "00:08", "score": 96, "color": "#FFDE59"},
            {"title": "ENERGY SPIKE", "start": "01:14", "score": 90, "color": "#8C52FF"},
            {"title": "BIG PAYOFF", "start": "02:28", "score": 88, "color": "#00BF63"}
        ]
    file_name = file.filename if file else ""
    new_clips = []
    for clip in selected_templates:
        new_clip = {
            "id": str(uuid.uuid4()),
            "title": clip["title"] + (scanMode == "quick" and " - TURBO" or scanMode == "precision" and " - DEEP SCAN" or ""),
            "start": clip["start"],
            "score": clip["score"],
            "color": clip["color"],
            "sourceType": sourceType,
            "sourceUrl": sourceUrl,
            "fileName": file_name
        }
        new_clips.append(new_clip)
    clips_db.clear()
    clips_db.extend(new_clips)
    return clips_db

@router.delete("/clips/{clip_id}")
def delete_clip(clip_id: str):
    global clips_db
    before = len(clips_db)
    clips_db = [clip for clip in clips_db if clip["id"] != clip_id]
    after = len(clips_db)
    if before == after:
        raise HTTPException(status_code=404, detail="Clip not found")
    return {"detail": "Clip deleted"}
