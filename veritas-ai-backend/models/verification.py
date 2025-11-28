"""
Verification model
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from services.database import Base


class InputType(str, PyEnum):
    """Input type enumeration"""
    ARTICLE = "article"
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class VerificationStatus(str, PyEnum):
    """Verification status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class Verification(Base):
    """Verification table model"""
    __tablename__ = "verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    input_type = Column(SQLEnum(InputType), nullable=False)
    status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    claims = relationship("Claim", back_populates="verification", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Verification(id={self.id}, type={self.input_type}, status={self.status})>"

