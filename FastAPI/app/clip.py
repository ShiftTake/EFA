from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
import numpy as np
import cv2

import yt_dlp
import uuid
import os
import ffmpeg
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import FileResponse
from typing import List
from .schemas import Clip

CLIPS_DIR = os.path.join(os.path.dirname(__file__), 'clips')
os.makedirs(CLIPS_DIR, exist_ok=True)

router = APIRouter()

# In-memory storage for demo
clips_db = []

@router.get("/clips/download/{filename}")
def download_clip(filename: str):
    file_path = os.path.join(CLIPS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(file_path, media_type="video/mp4", filename=filename)

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
    input_path = None
    if sourceType == "link":
        # Download video using yt-dlp
        ydl_opts = {
            'outtmpl': os.path.join(CLIPS_DIR, f"input_%(id)s.%(ext)s"),
            'format': 'mp4/bestvideo+bestaudio/best',
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(sourceUrl, download=True)
                input_path = ydl.prepare_filename(info)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"yt-dlp error: {e}")
    elif sourceType == "upload":
        if not file:
            raise HTTPException(status_code=400, detail="File required for upload source")
        if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            raise HTTPException(status_code=400, detail="Unsupported file type")
        input_path = os.path.join(CLIPS_DIR, f"input_{uuid.uuid4()}_{file.filename}")
        with open(input_path, "wb") as f:
            f.write(await file.read())

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
    if input_path:
        # AI highlight extraction (energy-based placeholder)
        highlights = []
        cap = cv2.VideoCapture(input_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        window = int(fps * 2)  # 2-second window
        energies = []
        for i in range(frame_count):
            ret, frame = cap.read()
            if not ret:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            energy = np.sum(gray.astype(np.float32) ** 2)
            energies.append(energy)
        cap.release()
        energies = np.array(energies)
        # Find peaks in energy
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(energies, distance=window, prominence=np.max(energies)*0.2)
        for idx, peak in enumerate(peaks):
            start_sec = int(max(0, peak - window//2) / fps)
            duration = int(window / fps)
            out_name = f"clip_{uuid.uuid4()}.mp4"
            out_path = os.path.join(CLIPS_DIR, out_name)
            try:
                (
                    ffmpeg
                    .input(input_path, ss=start_sec, t=duration)
                    .output(out_path, vcodec='libx264', acodec='aac')
                    .run(overwrite_output=True)
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"FFmpeg error: {e}")
            new_clip = {
                "id": str(uuid.uuid4()),
                "title": f"AI Highlight {idx+1}",
                "start": f"{start_sec//60:02d}:{start_sec%60:02d}",
                "score": 95,
                "color": "#8C52FF",
                "sourceType": sourceType,
                "sourceUrl": sourceUrl,
                "fileName": file_name,
                "clipPath": out_name
            }
            new_clips.append(new_clip)
        # Fallback to scene detection if no highlights
        if not new_clips:
            video_manager = VideoManager([input_path])
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector())
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            scene_list = scene_manager.get_scene_list()
            video_manager.release()
            if not scene_list:
                scene_list = [(0, 10)]
            for i, (start, end) in enumerate(scene_list):
                start_sec = int(start.get_seconds())
                duration = int(end.get_seconds()) - start_sec
                out_name = f"clip_{uuid.uuid4()}.mp4"
                out_path = os.path.join(CLIPS_DIR, out_name)
                try:
                    (
                        ffmpeg
                        .input(input_path, ss=start_sec, t=duration if duration > 0 else 10)
                        .output(out_path, vcodec='libx264', acodec='aac')
                        .run(overwrite_output=True)
                    )
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"FFmpeg error: {e}")
                new_clip = {
                    "id": str(uuid.uuid4()),
                    "title": f"Scene {i+1}",
                    "start": f"{start_sec//60:02d}:{start_sec%60:02d}",
                    "score": 80,
                    "color": "#FFDE59",
                    "sourceType": sourceType,
                    "sourceUrl": sourceUrl,
                    "fileName": file_name,
                    "clipPath": out_name
                }
                new_clips.append(new_clip)
        if sourceType == "upload":
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
