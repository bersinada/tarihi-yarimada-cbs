"""
Tarihi Yarimada CBS - Notes API
/api/v1/notes endpoints for user notes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from ..db.database import get_db
from ..db.models import UserNote, HeritageAsset
from ..schemas.segment import NoteCreate, NoteResponse

router = APIRouter(prefix="/api/v1/notes", tags=["notes"])


# ==================================================
# List Notes
# ==================================================

@router.get("", response_model=List[NoteResponse])
async def get_notes(
    asset_id: Optional[int] = None,
    user_identifier: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get list of user notes with optional filtering.

    - **asset_id**: Filter by asset
    - **user_identifier**: Filter by user
    """
    query = db.query(UserNote)

    if asset_id:
        query = query.filter(UserNote.asset_id == asset_id)
    if user_identifier:
        query = query.filter(UserNote.user_identifier == user_identifier)

    notes = query.order_by(UserNote.created_at.desc()).offset(offset).limit(limit).all()
    return notes


@router.get("/by-asset/{asset_id}", response_model=List[NoteResponse])
async def get_notes_by_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """Get all notes for a specific asset"""
    asset = db.query(HeritageAsset).filter(HeritageAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    notes = db.query(UserNote).filter(
        UserNote.asset_id == asset_id
    ).order_by(UserNote.created_at.desc()).all()

    return notes


# ==================================================
# Single Note CRUD
# ==================================================

@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int, db: Session = Depends(get_db)):
    """Get a single note by ID"""
    note = db.query(UserNote).filter(UserNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.post("", response_model=NoteResponse, status_code=201)
async def create_note(note_data: NoteCreate, db: Session = Depends(get_db)):
    """Create a new note for an asset"""
    # Check if asset exists
    asset = db.query(HeritageAsset).filter(HeritageAsset.id == note_data.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    note = UserNote(
        asset_id=note_data.asset_id,
        user_identifier=note_data.user_identifier,
        note_text=note_data.note_text
    )

    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note"""
    note = db.query(UserNote).filter(UserNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(note)
    db.commit()
    return None


# ==================================================
# Statistics
# ==================================================

@router.get("/stats/summary")
async def get_notes_statistics(db: Session = Depends(get_db)):
    """Get statistics about user notes"""
    total = db.query(UserNote).count()

    by_asset = db.query(
        UserNote.asset_id,
        func.count(UserNote.id).label("count")
    ).group_by(UserNote.asset_id).all()

    # Get asset names
    assets_with_notes = []
    for asset_id, count in by_asset:
        asset = db.query(HeritageAsset).filter(HeritageAsset.id == asset_id).first()
        if asset:
            assets_with_notes.append({
                "asset_id": asset_id,
                "asset_name_tr": asset.name_tr,
                "note_count": count
            })

    return {
        "total_notes": total,
        "assets_with_notes": assets_with_notes
    }
