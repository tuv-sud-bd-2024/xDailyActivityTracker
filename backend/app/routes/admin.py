from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from ..db import engine
from ..models import Staff, Client, Deal
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


@router.get("/staff")
def list_staff(request: Request, current_user=Depends(get_auth_user)):
    with Session(engine) as session:
        staff = session.exec(select(Staff)).all()
    return templates.TemplateResponse("admin_staff.html", {"request": request, "staff": staff})


@router.post("/staff/create")
def create_staff(code: str = Form(...), name: str = Form(...), request: Request = None, current_user=Depends(get_auth_user)):
    with Session(engine) as session:
        s = Staff(code=code, name=name)
        session.add(s)
        session.commit()
    return RedirectResponse(url="/admin/staff", status_code=302)


@router.get("/clients")
def list_clients(request: Request, current_user=Depends(get_auth_user)):
    with Session(engine) as session:
        clients = session.exec(select(Client)).all()
    return templates.TemplateResponse("admin_clients.html", {"request": request, "clients": clients})


@router.post("/clients/create")
def create_client(name: str = Form(...), external_id: str = Form(None), request: Request = None, current_user=Depends(get_auth_user)):
    with Session(engine) as session:
        c = Client(name=name, external_id=external_id)
        session.add(c)
        session.commit()
    return RedirectResponse(url="/admin/clients", status_code=302)


@router.get("/deals")
def list_deals(request: Request, current_user=Depends(get_auth_user)):
    with Session(engine) as session:
        deals = session.exec(select(Deal)).all()
    return templates.TemplateResponse("admin_deals.html", {"request": request, "deals": deals})


@router.post("/deals/create")
def create_deal(name: str = Form(...), client_id: str = Form(None), request: Request = None, current_user=Depends(get_auth_user)):
    with Session(engine) as session:
        d = Deal(name=name, client_id=client_id)
        session.add(d)
        session.commit()
    return RedirectResponse(url="/admin/deals", status_code=302)
