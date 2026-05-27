"""Telegram notification module."""

from __future__ import annotations

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send notifications via Telegram Bot API."""

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.seen_ids: set[str] = set()

    def _send_message(self, text: str) -> dict:
        """Send a message to Telegram."""
        resp = requests.post(
            f"{self.base_url}/sendMessage",
            json={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def notify_vehicles(self, vehicles: list) -> None:
        """Send notification about matching vehicles."""
        if not vehicles:
            logger.info("No vehicles to notify")
            return

        lines = ["🚗 *Subastas AEAT - Nuevos vehículos*", ""]
        for v in vehicles:
            lines.append(f"📋 {v.marca_modelo}")
            lines.append(f"   Matrícula: {v.matricula or 'N/A'}")
            lines.append(f"   Tipo: {v.tipo_descripcion}")
            lines.append(f"   Valoración: {v.valoracion:,.2f}€")
            lines.append(f"   Fin subasta: {v.fin_subasta}")
            if v.dias_hasta_fin is not None:
                lines.append(f"   Días restantes: {v.dias_hasta_fin}")
            lines.append(f"   Provincia: {v.cod_provincia}")
            lines.append("")

        text = "\n".join(lines)
        logger.info("Sending Telegram notification for %d vehicles", len(vehicles))
        self._send_message(text)

        # Mark as seen
        for v in vehicles:
            self.seen_ids.add(v.id)

    def notify_error(self, error_msg: str) -> None:
        """Send error notification."""
        text = f"❌ *Error en scraper AEAT*\n\n{error_msg}"
        try:
            self._send_message(text)
        except Exception as e:
            logger.error("Failed to send error notification: %s", e)

    def notify_summary(self, vehicles: list, total: int) -> None:
        """Send a summary notification."""
        lines = [
            f"📊 *Resumen AEAT*",
            f"",
            f"Total vehículos scrapeados: {total}",
            f"Vehículos que coinciden: {len(vehicles)}",
        ]
        if vehicles:
            lines.append(f"")
            lines.append("Vehículos coincidentes:")
            for v in vehicles[:20]:
                lines.append(f"  • {v.marca_modelo} - {v.valoracion:,.2f}€")
        text = "\n".join(lines)
        self._send_message(text)
