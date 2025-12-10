import re
import datetime
from typing import List, Dict, Any

from .schemas import LLMResponse, ParsedItem
from .llm_client import get_llm_client
from .models import DailyActivity, Staff, ActivityParseLog
from sqlmodel import Session, select
from .db import engine


HEADER_RE = re.compile(r"^\[(?P<time>\d{1,2}:\d{2}),\s*(?P<date>\d{1,2}/\d{1,2}/\d{2,4})\]\s*(?P<sender>[^:]+):\s*(?P<message>.*)$")
ITEM_RE = re.compile(r"(?m)^\s*(?P<num>\d+)[\.)\-]\s*(?P<item>.+)$")
MENTION_RE = re.compile(r"@~?(?P<name>[\w\-\s]+)")


def parse_whatsapp_block(block: str) -> LLMResponse:
    # Try deterministic parse first
    lines = block.strip().splitlines()
    parsed_items: List[ParsedItem] = []
    overall_conf = 0.0

    for line in lines:
        m = HEADER_RE.match(line)
        if m:
            time = m.group('time')
            date = m.group('date')
            sender = m.group('sender').strip()
            message = m.group('message').strip()

            # attempt to split numbered items
            items = ITEM_RE.findall(message)
            if items:
                for idx, item in items:
                    desc = item.strip()
                    candidates = MENTION_RE.findall(desc)
                    parsed_items.append(ParsedItem(
                        item_id=idx,
                        source_sender=sender,
                        source_timestamp=None,
                        activity_date=parse_date(date),
                        start_time=None,
                        end_time=None,
                        description=desc,
                        is_client_activity=bool(candidates),
                        client_candidates=[{"client_name":c.strip(), "client_match_score":0.9} for c in candidates],
                        deal_candidates=[],
                        parsing_notes="deterministic",
                        confidence=0.9
                    ))
                    overall_conf = max(overall_conf, 0.9)
            else:
                # single message
                candidates = MENTION_RE.findall(message)
                parsed_items.append(ParsedItem(
                    item_id="1",
                    source_sender=sender,
                    source_timestamp=None,
                    activity_date=parse_date(date),
                    start_time=None,
                    end_time=None,
                    description=message,
                    is_client_activity=bool(candidates),
                    client_candidates=[{"client_name":c.strip(), "client_match_score":0.9} for c in candidates],
                    deal_candidates=[],
                    parsing_notes="deterministic",
                    confidence=0.85
                ))
                overall_conf = max(overall_conf, 0.85)

    if not parsed_items:
        # fallback to LLM
        llm = get_llm_client()
        return llm.parse_block(block)

    return LLMResponse(source_block=block, parsed_items=parsed_items, overall_confidence=overall_conf)


def parse_date(date_str: str):
    # Expecting D/M/YYYY or D/M/YY. Convert to date.
    try:
        parts = [int(p) for p in date_str.split('/')]
        if parts[2] < 100:
            parts[2] += 2000
        return datetime.date(parts[2], parts[1], parts[0])
    except Exception:
        return None


def append_unique_list_field(existing_text: str | None, new_item: str) -> str:
    """Append new_item to existing_text (newline-separated) if not duplicate.
    Return updated text."""
    if not existing_text:
        return new_item
    # simple exact dedupe
    items = [s.strip() for s in existing_text.split('\n') if s.strip()]
    if new_item.strip() in items:
        return existing_text
    items.append(new_item.strip())
    return "\n".join(items)


def merge_or_create_activity(parsed_item: ParsedItem, raw_block: str) -> DailyActivity:
    """Merge parsed_item into existing DailyActivity (by staff+date) or create new one.
    Uses auto-append policy: append to planned or executed based on raw_block keywords.
    Returns the created or updated DailyActivity object.
    Note: this function uses its own DB session for simplicity."""
    with Session(engine) as session:
        # find staff by exact code or alias
        staff = None
        if parsed_item.source_sender:
            staff = session.exec(select(Staff).where(Staff.code == parsed_item.source_sender)).first()
            if not staff:
                # try matching alias
                staff = session.exec(select(Staff).where(Staff.whatsapp_aliases.contains(parsed_item.source_sender))).first()

        staff_id = staff.id if staff else None

        # determine column: plan vs update heuristic
        raw_lower = (raw_block or "").lower()
        is_plan = False
        if "plan" in raw_lower or "work plan" in raw_lower or "today's plan" in raw_lower:
            is_plan = True
        elif "update" in raw_lower or "work update" in raw_lower or "today's update" in raw_lower:
            is_plan = False
        # look for existing activity row
        existing = None
        if staff_id and parsed_item.activity_date:
            existing = session.exec(select(DailyActivity).where(
                DailyActivity.staff_id == staff_id,
                DailyActivity.activity_date == parsed_item.activity_date
            )).first()

        if existing:
            # append description
            existing.description = append_unique_list_field(existing.description, parsed_item.description or "")
            # append to planned or executed
            if is_plan:
                existing.planned_activities = append_unique_list_field(existing.planned_activities, parsed_item.description or "")
            else:
                existing.executed_activities = append_unique_list_field(existing.executed_activities, parsed_item.description or "")
            # update raw_text and confidence
            existing.raw_text = (existing.raw_text or "") + "\n---\n" + (parsed_item.description or raw_block)
            existing.confidence = max(existing.confidence or 0.0, parsed_item.confidence or 0.0)
            existing.status = "parsed"
            existing.updated_at = datetime.datetime.utcnow()
            session.add(existing)
            session.commit()
            session.refresh(existing)
            # log parse
            log = ActivityParseLog(raw_block=raw_block, parsed_result=str(parsed_item.dict()), status="processed")
            session.add(log)
            session.commit()
            return existing

        # create new
        new = DailyActivity(
            staff_id=staff_id,
            activity_date=parsed_item.activity_date or datetime.date.today(),
            source_sender_raw=parsed_item.source_sender,
            description=parsed_item.description or "",
            planned_activities=(parsed_item.description if is_plan else None),
            executed_activities=(parsed_item.description if not is_plan else None),
            raw_text=parsed_item.description or raw_block,
            confidence=parsed_item.confidence or 0.0,
            status="parsed",
        )
        session.add(new)
        session.commit()
        session.refresh(new)
        # log parse
        log = ActivityParseLog(raw_block=raw_block, parsed_result=str(parsed_item.dict()), status="processed")
        session.add(log)
        session.commit()
        return new
