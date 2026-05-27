"""Vehicle data models for AEAT auction scrapers."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional


# Tipo de vehículo según el código AEAT
TIPO_VEHICULOS: dict[int, str] = {
    101: "Turismo",
    102: "Motocicleta",
    103: "Furgoneta",
    104: "Camión",
    105: "Todo Terreno",
    207: "Licencia de tabaco",
    208: "Mercaderías",
    299: "Participaciones sociales / Otros",
}

# Combustible
COMBUSTIBLE_MAP: dict[str, str] = {
    "D": "Diésel",
    "G": "Gasolina",
    "H": "Híbrido",
    "E": "Eléctrico",
    "GLP": "GLP",
    "GN": "Gas Natural",
}

# Uso
USO_MAP: dict[int, str] = {
    1: "Particular",
    6: "Profesional",
    9: "Alquiler sin conductor",
}


class Vehicle(BaseModel):
    """Model for a vehicle auction item from AEAT."""

    id: str = Field(description="ID único del vehículo")
    subasta: str = Field(description="Referencia de la subasta")
    fin_subasta: str = Field(alias="finSubasta", description="Fecha fin subasta (YYYY-MM-DD)")
    cod_provincia: int = Field(alias="codProvincia", description="Código provincia")
    valoracion: float = Field(description="Valoración en euros")
    cargas: float = Field(description="Cargas en euros")
    tipo: int = Field(description="Tipo de vehículo (101=Turismo, 103=Furgoneta, etc.)")
    matricula: Optional[str] = None
    bastidor: Optional[str] = None
    marca_modelo: str = Field(alias="marcaModelo", description="Marca y modelo")
    plazas: Optional[int] = None
    combustible: Optional[str] = None
    cilindrada: Optional[int] = None
    años: Optional[float] = None
    unico_propietario: int = Field(alias="unicoPropietario", description="0=no, 1=sí")
    uso: Optional[int] = None
    fotos: list[str] = Field(default_factory=list)

    @field_validator("tipo", mode="before")
    @classmethod
    def validate_tipo(cls, v):
        if v is None:
            return None
        return int(v)

    @property
    def tipo_descripcion(self) -> str:
        return TIPO_VEHICULOS.get(self.tipo, f"Tipo {self.tipo} (desconocido)")

    @property
    def combustible_descripcion(self) -> str:
        if self.combustible:
            return COMBUSTIBLE_MAP.get(self.combustible, self.combustible)
        return "Desconocido"

    @property
    def uso_descripcion(self) -> str:
        if self.uso is not None:
            return USO_MAP.get(self.uso, f"Uso {self.uso}")
        return "Desconocido"

    @property
    def valor_neto(self) -> float:
        return self.valoracion - self.cargas

    @property
    def dias_hasta_fin(self) -> Optional[int]:
        from datetime import datetime, date

        try:
            fin = datetime.strptime(self.fin_subasta, "%Y-%m-%d").date()
            return (fin - date.today()).days
        except (ValueError, TypeError):
            return None

    model_config = ConfigDict(populate_by_name=True, json_schema_mode_override="serialization")

    def to_dict(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True)

    def to_csv_row(self) -> dict:
        """Return a flat dict suitable for CSV output."""
        return {
            "id": self.id,
            "subasta": self.subasta,
            "fin_subasta": self.fin_subasta,
            "cod_provincia": self.cod_provincia,
            "valoracion": f"{self.valoracion:,.2f}€",
            "cargas": f"{self.cargas:,.2f}€",
            "valor_neto": f"{self.valor_neto:,.2f}€",
            "tipo": self.tipo_descripcion,
            "matricula": self.matricula or "",
            "bastidor": self.bastidor or "",
            "marca_modelo": self.marca_modelo,
            "plazas": self.plazas or "",
            "combustible": self.combustible_descripcion,
            "cilindrada": f"{self.cilindrada} cc" if self.cilindrada else "",
            "años": f"{self.años:.1f}" if self.años else "",
            "unico_propietario": "Sí" if self.unico_propietario else "No",
            "uso": self.uso_descripcion,
            "fotos_count": len(self.fotos),
            "dias_hasta_fin": self.dias_hasta_fin if self.dias_hasta_fin else "",
        }
