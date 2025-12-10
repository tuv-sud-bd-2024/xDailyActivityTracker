"""Routes for activity listing, filtering, and export."""
from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from datetime import date
import io

from ..db import engine
from ..models import DailyActivity, Staff, Client, ClientActivity
from ..auth import get_user_from_token_optional

router = APIRouter()
templates = Jinja2Templates(directory="backend/app/templates")


def get_auth_user(request: Request):
    """Check for valid auth token in cookie."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = get_user_from_token_optional(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@router.get("/activities")
def list_activities(
    request: Request,
    staff_id: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    current_user=None,
):
    """List daily activities with filtering and pagination."""
    user = get_auth_user(request)
    
    with Session(engine) as session:
        query = select(DailyActivity)
        
        # Apply filters
        if staff_id:
            query = query.where(DailyActivity.staff_id == staff_id)
        if date_from:
            try:
                df = date.fromisoformat(date_from)
                query = query.where(DailyActivity.activity_date >= df)
            except ValueError:
                pass
        if date_to:
            try:
                dt = date.fromisoformat(date_to)
                query = query.where(DailyActivity.activity_date <= dt)
            except ValueError:
                pass
        if status:
            query = query.where(DailyActivity.status == status)
        
        # Count and paginate
        total = session.exec(query).all().__len__()
        activities = session.exec(
            query.offset((page - 1) * page_size).limit(page_size)
        ).all()
        
        # Fetch related staff names
        staff_map = {}
        for a in activities:
            if a.staff_id and a.staff_id not in staff_map:
                s = session.get(Staff, a.staff_id)
                staff_map[a.staff_id] = s.name if s else "Unknown"
        
    return templates.TemplateResponse("activity_list.html", {
        "request": request,
        "activities": activities,
        "staff_map": staff_map,
        "page": page,
        "page_size": page_size,
        "total": total,
        "date_from": date_from,
        "date_to": date_to,
        "status": status,
    })


@router.get("/activities/export")
def export_activities(
    request: Request,
    staff_id: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    status: str | None = Query(None),
    format: str = Query("xlsx"),
    current_user=None,
):
    """Export activities to Excel or CSV."""
    user = get_auth_user(request)
    
    with Session(engine) as session:
        query = select(DailyActivity)
        if staff_id:
            query = query.where(DailyActivity.staff_id == staff_id)
        if date_from:
            try:
                df = date.fromisoformat(date_from)
                query = query.where(DailyActivity.activity_date >= df)
            except ValueError:
                pass
        if date_to:
            try:
                dt = date.fromisoformat(date_to)
                query = query.where(DailyActivity.activity_date <= dt)
            except ValueError:
                pass
        if status:
            query = query.where(DailyActivity.status == status)
        
        activities = session.exec(query).all()
        
        # Fetch staff names
        staff_names = {}
        for a in activities:
            if a.staff_id and a.staff_id not in staff_names:
                s = session.get(Staff, a.staff_id)
                staff_names[a.staff_id] = s.name if s else "Unknown"
    
    # Export to Excel using pandas
    try:
        import pandas as pd
        
        data = []
        for a in activities:
            data.append({
                "Date": a.activity_date,
                "Staff": staff_names.get(a.staff_id, "Unknown"),
                "Description": a.description,
                "Planned": (a.planned_activities or "").replace("\n", "; "),
                "Executed": (a.executed_activities or "").replace("\n", "; "),
                "Remarks": a.remarks or "",
                "Confidence": f"{a.confidence:.2f}",
                "Status": a.status,
            })
        
        df = pd.DataFrame(data)
        
        if format == "csv":
            output = io.StringIO()
            df.to_csv(output, index=False)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=activities.csv"}
            )
        else:  # xlsx
            output = io.BytesIO()
            df.to_excel(output, index=False, engine="openpyxl")
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=activities.xlsx"}
            )
    except ImportError:
        raise HTTPException(status_code=500, detail="pandas/openpyxl not installed")
