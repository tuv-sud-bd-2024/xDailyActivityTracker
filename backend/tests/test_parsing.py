"""Unit tests for parsing and merge logic."""
import pytest
from backend.app.parse_pipeline import parse_whatsapp_block, append_unique_list_field, parse_date
from backend.app.db import engine, init_db
from backend.app.models import Staff, DailyActivity
from sqlmodel import Session, select
import datetime


@pytest.fixture(scope="function")
def setup_db():
    """Initialize DB and create test staff."""
    init_db()
    with Session(engine) as session:
        staff1 = Staff(code="Staff-01", name="John Doe")
        staff2 = Staff(code="Staff-02", name="Jane Smith")
        session.add_all([staff1, staff2])
        session.commit()
    yield
    # Cleanup would go here


def test_parse_date():
    """Test date parsing from WhatsApp format."""
    assert parse_date("12/10/2025") == datetime.date(2025, 10, 12)
    assert parse_date("1/1/25") == datetime.date(2025, 1, 1)
    assert parse_date("31/12/2024") == datetime.date(2024, 12, 31)
    assert parse_date("invalid") is None


def test_append_unique_list_field():
    """Test deduplication and appending to list fields."""
    # Empty existing
    result = append_unique_list_field(None, "item 1")
    assert result == "item 1"
    
    # Append to existing
    result = append_unique_list_field("item 1", "item 2")
    assert "item 1" in result and "item 2" in result
    
    # Avoid duplicate
    result = append_unique_list_field("item 1", "item 1")
    assert result.count("item 1") == 1


def test_parse_single_message():
    """Test parsing a single message."""
    msg = "[09:34, 12/10/2025] Staff-01: Good morning mates!"
    result = parse_whatsapp_block(msg)
    assert len(result.parsed_items) > 0
    assert result.parsed_items[0].source_sender == "Staff-01"
    assert result.parsed_items[0].description


def test_parse_numbered_items():
    """Test parsing numbered list items."""
    msg = "[09:40, 12/10/2025] Staff-02: 1) Follow up client A 2) attend meeting 3) work on project"
    result = parse_whatsapp_block(msg)
    assert len(result.parsed_items) >= 1
    assert any("Follow up client A" in item.description for item in result.parsed_items)


def test_parse_with_mentions():
    """Test parsing messages with @mentions."""
    msg = "[08:00, 12/10/2025] Staff-02: Called @~ClientA about PO"
    result = parse_whatsapp_block(msg)
    assert len(result.parsed_items) > 0
    item = result.parsed_items[0]
    assert item.is_client_activity
    assert len(item.client_candidates) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
