"""Database layer for vehicle history and deduplication."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    func,
    select,
    delete,
    update,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from src.models.history import VehicleRecord, ScrapeEvent

logger = logging.getLogger(__name__)

Base = declarative_base()


class DbVehicleRecord(Base):
    """SQLAlchemy mapping for vehicle records."""

    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(50), nullable=False, index=True)
    scrape_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    status = Column(String(20), nullable=False, default="new")
    subasta = Column(String(100), default="")
    fin_subasta = Column(String(20), default="")
    cod_provincia = Column(Integer, default=0)
    valoracion = Column(Float, default=0.0)
    cargas = Column(Float, default=0.0)
    tipo = Column(Integer, default=0)
    matricula = Column(String(20), default="")
    bastidor = Column(String(30), default="")
    marca_modelo = Column(String(200), default="")
    plazas = Column(Integer, nullable=True)
    combustible = Column(String(10), default="")
    cilindrada = Column(Integer, nullable=True)
    años = Column(Float, nullable=True)
    unico_propietario = Column(Integer, default=0)
    uso = Column(Integer, nullable=True)
    fotos_count = Column(Integer, default=0)
    seen = Column(Boolean, default=False)


class DbScrapeEvent(Base):
    """SQLAlchemy mapping for scrape events."""

    __tablename__ = "scrapes"

    scrape_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    total_vehicles = Column(Integer, default=0)
    new_vehicles = Column(Integer, default=0)
    unchanged_vehicles = Column(Integer, default=0)
    disappeared_vehicles = Column(Integer, default=0)
    error = Column(Text, default="")


class HistoryDB:
    """Manages vehicle history database for deduplication."""

    def __init__(self, db_path: str = "data/history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def session(self) -> Session:
        return self.Session()

    def _db_record_to_model(self, db_record: DbVehicleRecord) -> VehicleRecord:
        """Convert SQLAlchemy record to Pydantic model."""
        return VehicleRecord(
            id=db_record.vehicle_id,
            scrape_id=db_record.scrape_id,
            timestamp=db_record.timestamp,
            status=db_record.status,
            subasta=db_record.subasta,
            fin_subasta=db_record.fin_subasta,
            cod_provincia=db_record.cod_provincia,
            valoracion=db_record.valoracion,
            cargas=db_record.cargas,
            tipo=db_record.tipo,
            matricula=db_record.matricula,
            bastidor=db_record.bastidor,
            marca_modelo=db_record.marca_modelo,
            plazas=db_record.plazas,
            combustible=db_record.combustible,
            cilindrada=db_record.cilindrada,
            años=db_record.años,
            unico_propietario=db_record.unico_propietario,
            uso=db_record.uso,
            seen=db_record.seen,
        )

    def record_scrape(self, vehicles: list, status_map: dict[str, str]) -> ScrapeEvent:
        """Record a new scrape with all vehicles and their status.
        
        Args:
            vehicles: List of Vehicle objects from current scrape
            status_map: Dict mapping vehicle_id -> status ("new", "unchanged", "disappeared")
        
        Returns:
            ScrapeEvent with summary stats
        """
        with self.session() as session:
            # Find max existing scrape_id
            result = session.execute(select(func.max(DbScrapeEvent.scrape_id)))
            max_id = result.scalar() or 0
            new_scrape_id = max_id + 1

            # Count statuses
            new_count = sum(1 for s in status_map.values() if s == "new")
            unchanged_count = sum(1 for s in status_map.values() if s == "unchanged")
            disappeared_count = sum(1 for s in status_map.values() if s == "disappeared")

            # Create scrape event (SQLAlchemy mapped object)
            db_event = DbScrapeEvent(
                scrape_id=new_scrape_id,
                total_vehicles=len(vehicles),
                new_vehicles=new_count,
                unchanged_vehicles=unchanged_count,
                disappeared_vehicles=disappeared_count,
            )
            session.add(db_event)

            # Store each vehicle
            now = datetime.now()
            for v in vehicles:
                status = status_map.get(v.id, "unchanged")
                record = DbVehicleRecord(
                    vehicle_id=v.id,
                    scrape_id=new_scrape_id,
                    timestamp=now,
                    status=status,
                    subasta=v.subasta,
                    fin_subasta=v.fin_subasta,
                    cod_provincia=v.cod_provincia,
                    valoracion=v.valoracion,
                    cargas=v.cargas,
                    tipo=v.tipo,
                    matricula=v.matricula or "",
                    bastidor=v.bastidor or "",
                    marca_modelo=v.marca_modelo,
                    plazas=v.plazas,
                    combustible=v.combustible or "",
                    cilindrada=v.cilindrada,
                    años=v.años,
                    unico_propietario=v.unico_propietario,
                    uso=v.uso,
                    fotos_count=len(v.fotos),
                )
                session.add(record)

            session.commit()
            logger.info(
                "Scrape #%d: %d vehicles (%d new, %d unchanged, %d disappeared)",
                new_scrape_id,
                len(vehicles),
                new_count,
                unchanged_count,
                disappeared_count,
            )
            # Return Pydantic model (not the SQLAlchemy object)
            return ScrapeEvent(
                scrape_id=new_scrape_id,
                total_vehicles=len(vehicles),
                new_vehicles=new_count,
                unchanged_vehicles=unchanged_count,
                disappeared_vehicles=disappeared_count,
            )

    def get_last_seen_vehicle(self, vehicle_id: str) -> Optional[VehicleRecord]:
        """Get the last seen version of a vehicle.
        
        Returns:
            VehicleRecord or None if never seen
        """
        with self.session() as session:
            result = session.execute(
                select(DbVehicleRecord).where(
                    DbVehicleRecord.vehicle_id == vehicle_id
                ).order_by(DbVehicleRecord.scrape_id.desc()).limit(1)
            ).scalars().first()
            if not result:
                return None
            return self._db_record_to_model(result)

    def get_disappeared_vehicles(self, last_scrape_id: int) -> list[VehicleRecord]:
        """Find vehicles that were present in last_scrape_id but not in current.
        
        Returns vehicles that were marked as 'disappeared'.
        """
        with self.session() as session:
            result = session.execute(
                select(DbVehicleRecord)
                .where(
                    DbVehicleRecord.status == "disappeared",
                    DbVehicleRecord.scrape_id == last_scrape_id,
                )
                .order_by(DbVehicleRecord.timestamp.desc())
            ).scalars().all()
            return [self._db_record_to_model(r) for r in result]

    def mark_seen(self, vehicle_id: str) -> None:
        """Mark a vehicle as having been notified."""
        with self.session() as session:
            session.execute(
                update(DbVehicleRecord)
                .where(DbVehicleRecord.vehicle_id == vehicle_id)
                .values(seen=True)
            )
            session.commit()

    def get_all_seen(self, limit: int = 100) -> list[VehicleRecord]:
        """Get vehicles that have been notified."""
        with self.session() as session:
            result = session.execute(
                select(DbVehicleRecord)
                .where(DbVehicleRecord.seen == True)
                .order_by(DbVehicleRecord.timestamp.desc())
                .limit(limit)
            ).scalars().all()
            return [self._db_record_to_model(r) for r in result]

    def get_history(
        self,
        province: Optional[int] = None,
        tipo: Optional[int] = None,
        since: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[VehicleRecord]:
        """Query history with optional filters."""
        with self.session() as session:
            query = select(DbVehicleRecord)
            if province:
                query = query.where(DbVehicleRecord.cod_provincia == province)
            if tipo:
                query = query.where(DbVehicleRecord.tipo == tipo)
            if since:
                query = query.where(DbVehicleRecord.timestamp >= since)
            query = query.order_by(DbVehicleRecord.timestamp.desc()).limit(limit)
            result = session.execute(query).scalars().all()
            return [self._db_record_to_model(r) for r in result]

    def cleanup_old_scrapes(self, keep_scrapes: int = 30) -> int:
        """Remove old scrape records, keeping only the last N scrapes.
        
        Returns number of records removed.
        """
        with self.session() as session:
            # Get scrape IDs to keep (most recent N)
            result = session.execute(
                select(DbScrapeEvent.scrape_id)
                .order_by(DbScrapeEvent.scrape_id.desc())
                .offset(keep_scrapes)
            )
            old_scrape_ids = [row[0] for row in result.all()]

            if not old_scrape_ids:
                return 0

            # Remove old vehicle records
            deleted_vehicles = session.execute(
                delete(DbVehicleRecord).where(DbVehicleRecord.scrape_id.in_(old_scrape_ids))
            ).rowcount

            # Remove old scrape events
            deleted_scrapes = session.execute(
                delete(DbScrapeEvent).where(DbScrapeEvent.scrape_id.in_(old_scrape_ids))
            ).rowcount

            session.commit()
            logger.info("Cleaned up %d vehicle records from %d old scrapes", deleted_vehicles, len(old_scrape_ids))
            return deleted_vehicles + deleted_scrapes

    def get_stats(self) -> dict:
        """Get database statistics."""
        with self.session() as session:
            total_scrapes = session.execute(select(func.count(DbScrapeEvent.scrape_id))).scalar() or 0
            total_vehicles = session.execute(select(func.count(DbVehicleRecord.id))).scalar() or 0
            new_count = session.execute(select(func.count(DbVehicleRecord.id)).where(DbVehicleRecord.status == "new")).scalar() or 0
            seen_count = session.execute(select(func.count(DbVehicleRecord.id)).where(DbVehicleRecord.seen == True)).scalar() or 0

            return {
                "total_scrapes": total_scrapes,
                "total_vehicles": total_vehicles,
                "new_vehicles": new_count,
                "notified_vehicles": seen_count,
            }
