import datetime
import uuid
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(index=True, nullable=False)
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    roles: Optional[str] = Field(default='["viewer"]')
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: Optional[datetime.datetime] = None


class Staff(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    code: str = Field(index=True, nullable=False)
    name: str
    whatsapp_aliases: Optional[str] = None
    email: Optional[str] = None
    active: bool = True
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: Optional[datetime.datetime] = None


class Client(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, nullable=False)
    external_id: Optional[str] = None
    extra_data: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: Optional[datetime.datetime] = None


class Deal(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    deal_id: Optional[str] = Field(index=True)
    client_id: Optional[uuid.UUID] = Field(default=None, foreign_key="client.id")
    name: str
    description: Optional[str] = None
    status: str = Field(default="open")
    amount: Optional[float] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: Optional[datetime.datetime] = None


class DailyActivity(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    staff_id: uuid.UUID = Field(default=None, foreign_key="staff.id", index=True)
    activity_date: datetime.date = Field(default_factory=datetime.date.today, index=True)
    source_sender_raw: Optional[str] = None
    source_message_timestamp: Optional[datetime.datetime] = None
    start_time: Optional[datetime.time] = None
    end_time: Optional[datetime.time] = None
    description: str
    planned_activities: Optional[str] = None
    executed_activities: Optional[str] = None
    remarks: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: float = 1.0
    status: str = Field(default="parsed")
    created_by: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: Optional[datetime.datetime] = None


class ClientActivity(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    daily_activity_id: uuid.UUID = Field(default=None, foreign_key="dailyactivity.id", index=True)
    client_id: Optional[uuid.UUID] = Field(default=None, foreign_key="client.id", index=True)
    deal_id: Optional[uuid.UUID] = Field(default=None, foreign_key="deal.id", index=True)
    activity_date: Optional[datetime.date] = None
    activity_description: Optional[str] = None
    deal_status: Optional[str] = None
    amount: Optional[float] = None
    logged_by: Optional[uuid.UUID] = Field(default=None, foreign_key="staff.id")
    source_info: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: Optional[datetime.datetime] = None


class ActivityParseLog(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    raw_block: str
    received_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    parsed_result: Optional[str] = None
    parser_version: Optional[str] = None
    status: str = Field(default="pending")
    processed_by: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    notes: Optional[str] = None
