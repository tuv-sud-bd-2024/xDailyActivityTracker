from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

from ..parse_pipeline import parse_whatsapp_block, merge_or_create_activity
from ..llm_client import get_llm_client
from ..db import get_session, engine
from ..models import ActivityParseLog, DailyActivity, Staff
from ..auth import get_user_from_token_optional
from sqlmodel import select, Session

router = APIRouter()
templates = Jinja2Templates(directory="backend/app/templates")


def get_user_from_cookie(request: Request) -> Optional:
    """Extract JWT token from cookie and authenticate."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        user = get_user_from_token_optional(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Auth error")


class PastePayload(BaseModel):
    paste: str


@router.post("/preview")
async def preview(payload: PastePayload, request: Request):
    user = get_user_from_cookie(request)
    parsed = parse_whatsapp_block(payload.paste)
    # Save parse log
    try:
        with Session(engine) as session:
            log = ActivityParseLog(raw_block=payload.paste, parsed_result=str(parsed.dict()), status="pending")
            session.add(log)
            session.commit()
    except Exception:
        pass
    return JSONResponse(content=parsed.dict())


@router.post("/apply")
async def apply(request: Request, paste: str = Form(...)):
    user = get_user_from_cookie(request)
    # For MVP: parse and create a DailyActivity per parsed item (auto_append policy will merge by staff+date)
    parsed = parse_whatsapp_block(paste)
    created = []
    try:
        for item in parsed.parsed_items:
            obj = merge_or_create_activity(item, paste)
            created.append(str(obj.id))
        return JSONResponse(content={"created": created})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
