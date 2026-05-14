from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class CertificateInfo(BaseModel):
    id: str
    name: str
    status: str = "Active"

class FactoryLocation(BaseModel):
    lat: float
    lng: float
    address: str

class ScanActivity(BaseModel):
    user: str
    location: str
    time: str

class ImportMilestone(BaseModel):
    step: str
    location: str
    date: str
    status: str

class BarcodeVerificationResponse(BaseModel):
    barcode: str
    product_name: str
    brand: str
    origin: str
    verified: bool = True
    batch_dna: str
    mfg_date: str
    expiry_date: str
    scans_24h: int
    factory: FactoryLocation
    certificates: List[CertificateInfo]
    recent_scans: List[ScanActivity]
    import_journey: List[ImportMilestone]
    brand_story: Optional[str] = None
    reward_label: Optional[str] = None
    reward_sub: Optional[str] = None
    # Elite V2.2: Regulatory Transparency
    notification_no: Optional[str] = None
    notification_date: Optional[str] = None
    notification_doc: Optional[str] = None
