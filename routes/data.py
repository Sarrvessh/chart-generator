from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uuid
from config import settings
from services.data_handler import data_handler
from models.schemas import UploadResponse, DataMetadata

router = APIRouter(prefix="/api/data", tags=["data"])

# In-memory store for session data (use Redis/database in production)
active_sessions = {}

@router.post("/upload/{session_id}")
async def upload_data(session_id: str, file: UploadFile = File(...)) -> UploadResponse:
    """Upload and validate CSV/JSON/Excel file"""
    try:
        # Validate file type
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {settings.ALLOWED_FILE_TYPES}"
            )

        # Validate file size
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
            )

        # Load and validate data
        df = await data_handler.load_data(content, file_extension)

        # Validate data structure
        is_valid, message = data_handler.validate_data(df)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)

        # Analyze data structure
        metadata = data_handler.analyze_data_structure(df)

        # Store in session
        active_sessions[session_id] = {
            'dataframe': df,
            'filename': file.filename,
            'metadata': metadata,
        }

        return UploadResponse(
            session_id=session_id,
            filename=file.filename,
            row_count=len(df),
            column_count=len(df.columns),
            columns=list(df.columns),
            metadata=DataMetadata(**metadata)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@router.post("/upload")
async def upload_data_legacy(file: UploadFile = File(...)) -> UploadResponse:
    """Legacy endpoint: Upload and validate CSV/JSON/Excel file (for backwards compatibility)"""
    try:
        # Validate file type
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {settings.ALLOWED_FILE_TYPES}"
            )

        # Validate file size
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
            )

        # Load and validate data
        df = await data_handler.load_data(content, file_extension)

        # Validate data structure
        is_valid, message = data_handler.validate_data(df)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)

        # Analyze data structure
        metadata = data_handler.analyze_data_structure(df)

        # Create session
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = {
            'dataframe': df,
            'filename': file.filename,
            'metadata': metadata,
        }

        return UploadResponse(
            session_id=session_id,
            filename=file.filename,
            row_count=len(df),
            column_count=len(df.columns),
            columns=list(df.columns),
            metadata=DataMetadata(**metadata)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@router.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    metadata = session['metadata']

    return {
        "session_id": session_id,
        "filename": session['filename'],
        "row_count": len(session['dataframe']),
        "column_count": len(session['dataframe'].columns),
        "columns": list(session['dataframe'].columns),
        "metadata": metadata,
    }

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and free memory"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del active_sessions[session_id]
    return {"message": f"Session {session_id} deleted"}
