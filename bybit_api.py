"""Módulo para manejar la comunicación con la API de Bybit.

Gestiona las solicitudes, autenticación y procesamiento básico de respuestas.
"""

import hashlib
import hmac
import time
from datetime import datetime

import pytz
import requests


class SymbolInvalidError(Exception):
    """Raised when Bybit reports that a symbol does not exist or is not supported."""


class BybitAPI:
    """Clase para manejar las comunicaciones con la API de Bybit."""

    def __init__(self, api_key=None, api_secret=None):
        """Inicializa la instancia de BybitAPI con credenciales opcionales."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bybit.com"

    def obtener_hora_gmt6(self):
        """Obtiene la hora y fecha actual en GMT-6."""
        gmt6 = pytz.timezone("America/Mexico_City")  # GMT-6
        ahora = datetime.now(gmt6)
        return ahora

    def generar_firma(self, params):
        """Genera la firma para la API de Bybit."""
        if not self.api_key or not self.api_secret:
            return None

        query_string = "&".join(
            [f"{key}={params[key]}" for key in sorted(params.keys())]
        )
        signature = hmac.new(
            bytes(self.api_secret, "utf-8"),
            bytes(query_string, "utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def obtener_datos_mercado(self, symbol, intervalo="15", limit=200):
        """Obtiene datos históricos del mercado usando la API de Bybit."""
        endpoint = "/v5/market/kline"
        params = {
            "symbol": symbol,
            "interval": intervalo,
            "limit": limit,
            "timestamp": int(time.time() * 1000),
        }

        if self.api_key and self.api_secret:
            params["api_key"] = self.api_key
            params["sign"] = self.generar_firma(params)

        response = requests.get(f"{self.base_url}{endpoint}", params=params)

        if response.status_code == 200:
            data = response.json()
            if data["retCode"] == 0:
                return data["result"]["list"]
            else:
                msg = data.get("retMsg", "")
                if "Symbol Is Invalid" in msg or "not support" in msg.lower():
                    raise SymbolInvalidError(f"{symbol}: {msg}")
                print(f"Error al obtener datos: {msg}")
                return None
        else:
            print(f"Error en la petición: {response.status_code}")
            return None

    def obtener_book_orders(self, symbol, limit=50):
        """Obtiene el order book para un símbolo específico."""
        endpoint = "/v5/market/orderbook"
        params = {"symbol": symbol, "limit": limit}

        response = requests.get(f"{self.base_url}{endpoint}", params=params)

        if response.status_code == 200:
            data = response.json()
            if data["retCode"] == 0:
                return data["result"]
            else:
                print(f"Error al obtener order book: {data['retMsg']}")
                return None
        else:
            print(f"Error en la petición: {response.status_code}")
            return None

    def obtener_trades_recientes(self, symbol, limit=50):
        """Obtiene trades recientes para un símbolo específico."""
        endpoint = "/v5/market/recent-trade"
        params = {"symbol": symbol, "limit": limit}

        response = requests.get(f"{self.base_url}{endpoint}", params=params)

        if response.status_code == 200:
            data = response.json()
            if data["retCode"] == 0:
                return data["result"]["list"]
            else:
                print(f"Error al obtener trades: {data['retMsg']}")
                return None
        else:
            print(f"Error en la petición: {response.status_code}")
            return None

    def obtener_tickers(self, category="linear"):
        """Obtiene tickers de todos los símbolos de una categoría."""
        endpoint = "/v5/market/tickers"
        params = {"category": category}

        response = requests.get(f"{self.base_url}{endpoint}", params=params)

        if response.status_code == 200:
            data = response.json()
            if data["retCode"] == 0:
                return data["result"]["list"]
            else:
                print(f"Error al obtener tickers: {data['retMsg']}")
                return None
        else:
            print(f"Error en la petición: {response.status_code}")
            return None

    def obtener_funding_rate(self, symbol, limit=50):
        """Obtiene el funding rate de un símbolo."""
        endpoint = "/v5/market/funding/history"
        params = {"symbol": symbol, "limit": limit}

        response = requests.get(f"{self.base_url}{endpoint}", params=params)

        if response.status_code == 200:
            data = response.json()
            if data["retCode"] == 0:
                return data["result"]["list"]
            else:
                print(f"Error al obtener funding rate: {data['retMsg']}")
                return None
        else:
            print(f"Error en la petición: {response.status_code}")
            return None
