"""
Claim model
"""
import uuid
from sqlalchemy import Column, String, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from services.database import Base


class Claim(Base):
    """Claim table model"""
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    verification_id = Column(UUID(as_uuid=True), ForeignKey("verifications.id"), nullable=False)
    text = Column(String, nullable=False)
    verdict = Column(String, nullable=True)  # true, false, uncertain
    confidence = Column(Float, nullable=True)
    evidence = Column(JSONB, nullable=True)  # JSON field for evidence data

    # Relationships
    verification = relationship("Verification", back_populates="claims")

    def __repr__(self):
        return f"<Claim(id={self.id}, text={self.text[:50]}..., verdict={self.verdict})>"

