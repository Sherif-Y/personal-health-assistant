from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class LabResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fhir_id: str = Field(index=True, unique=True)
    loinc_code: Optional[str] = Field(default=None, index=True)
    display_name: str
    category: Optional[str] = Field(default=None, index=True)

    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None

    reference_range_low: Optional[float] = None
    reference_range_high: Optional[float] = None
    reference_range_text: Optional[str] = None

    collected_at: Optional[datetime] = Field(default=None, index=True)
    source: str = Field(default="epic")


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fhir_id: str = Field(index=True, unique=True)
    resource_type: str  # "DiagnosticReport" or "DocumentReference"
    report_type: Optional[str] = Field(default=None, index=True)  # Radiology, Pathology, Cardiology, Clinical Note...
    title: str

    narrative_text: Optional[str] = None
    source_attachment_url: Optional[str] = None
    source_attachment_content_type: Optional[str] = None

    collected_at: Optional[datetime] = Field(default=None, index=True)
    source: str = Field(default="epic")


class SyncMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    resource_type: str = Field(index=True, unique=True)
    last_synced_at: datetime
