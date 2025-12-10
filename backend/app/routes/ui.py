from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="backend/app/templates")


@router.get("/parse")
def parse_page(request: Request):
    return templates.TemplateResponse("parse_paste.html", {"request": request})
