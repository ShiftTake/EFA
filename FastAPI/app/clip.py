
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import FileResponse
# In-memory storage for demo
clips_db = []

@router.get("/clips/download/{filename}")
def download_clip(filename: str):
    file_path = os.path.join(CLIPS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(file_path, media_type="video/mp4", filename=filename)
from typing import List
from .schemas import Clip

import uuid
import os
import ffmpeg

CLIPS_DIR = os.path.join(os.path.dirname(__file__), 'clips')
os.makedirs(CLIPS_DIR, exist_ok=True)

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
    if file:
        input_path = os.path.join(CLIPS_DIR, f"input_{uuid.uuid4()}_{file.filename}")
        with open(input_path, "wb") as f:
            f.write(await file.read())
        for clip in selected_templates:
            # Simulate start time as seconds
            start_sec = int(clip["start"].split(":")[0]) * 60 + int(clip["start"].split(":")[1])
            out_name = f"clip_{uuid.uuid4()}.mp4"
            out_path = os.path.join(CLIPS_DIR, out_name)
            try:
                (
                    ffmpeg
                    .input(input_path, ss=start_sec, t=10)  # 10s clip
                    .output(out_path, vcodec='libx264', acodec='aac')
                    .run(overwrite_output=True)
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"FFmpeg error: {e}")
            new_clip = {
                "id": str(uuid.uuid4()),
                "title": clip["title"] + (scanMode == "quick" and " - TURBO" or scanMode == "precision" and " - DEEP SCAN" or ""),
                "start": clip["start"],
                "score": clip["score"],
                "color": clip["color"],
                "sourceType": sourceType,
                "sourceUrl": sourceUrl,
                "fileName": file_name,
                "clipPath": out_name
            }
            new_clips.append(new_clip)
        os.remove(input_path)
    else:
        for clip in selected_templates:
            new_clip = {
                "id": str(uuid.uuid4()),
                "title": clip["title"] + (scanMode == "quick" and " - TURBO" or scanMode == "precision" and " - DEEP SCAN" or ""),
                "start": clip["start"],
                "score": clip["score"],
                "color": clip["color"],
                "sourceType": sourceType,
                "sourceUrl": sourceUrl,
                "fileName": file_name,
                "clipPath": ""
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
