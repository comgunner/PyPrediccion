"""Módulo para analizar y procesar los datos de mercado.

Calcula indicadores técnicos y prepara los datos para el modelado predictivo.
"""

from datetime import timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler


class AnalizadorDatos:
    """Clase para procesar y analizar datos de mercado."""

    def __init__(self):
        """Inicializa el analizador con modelos y escaladores."""
        self.model_long = None
        self.model_short = None
        self.scaler = StandardScaler()
        self.mm_scaler = MinMaxScaler()
        self.umbral_prob = 0.65  # Umbral de probabilidad para señales

    def procesar_klines(self, kline_data):
        """Procesa los datos de k-lines a un DataFrame estructurado."""
        if not kline_data:
            return None

        # Convertir lista a DataFrame
        df = pd.DataFrame(
            kline_data,
            columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"],
        )

        # Convertir columnas numéricas a float (los datos de API vienen como strings)
        numeric_cols = [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "turnover",
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Validar timestamps antes de convertir
        # Timestamps válidos están entre 2020 y 2030 en milisegundos
        min_valid_ts = 1577836800000  # 2020-01-01
        max_valid_ts = 1893456000000  # 2030-01-01

        # Filtrar timestamps inválidos
        invalid_mask = (df["timestamp"] < min_valid_ts) | (
            df["timestamp"] > max_valid_ts
        )
        if invalid_mask.any():
            print(f"Advertencia: {invalid_mask.sum()} timestamps fuera de rango válido")
            df = df[~invalid_mask]

        # Convertir timestamp a datetime
        # Workaround para pandas 3.0+: convertir a segundos primero para evitar overflow
        try:
            # Intentar conversión directa con ms
            df["datetime"] = pd.to_datetime(
                df["timestamp"].astype(float), unit="ms", utc=True
            )
        except (OverflowError, ValueError) as e:
            print(f"Overflow en conversión datetime, usando fallback a segundos: {e}")
            # Fallback: convertir a segundos
            df["datetime"] = pd.to_datetime(
                df["timestamp"].astype(float) / 1000, unit="s", utc=True
            )

        df = df.sort_values("datetime")

        return df

    def calcular_indicadores(self, df):
        """Calcula indicadores técnicos a partir de datos de precio."""
        if df is None or df.empty:
            return None

        # Copiar para no modificar el original
        df_ind = df.copy()

        # Asegurar que las columnas numéricas sean float (pueden venir como strings)
        numeric_cols = ["open", "high", "low", "close", "volume"]
        for col in numeric_cols:
            if col in df_ind.columns:
                df_ind[col] = pd.to_numeric(df_ind[col], errors="coerce")

        # Retornos y volatilidad
        df_ind["returns"] = df_ind["close"].pct_change()
        df_ind["volatility_14"] = df_ind["returns"].rolling(window=14).std()
        df_ind["volatility_7"] = df_ind["returns"].rolling(window=7).std()

        # Medias móviles
        df_ind["ma7"] = df_ind["close"].rolling(window=7).mean()
        df_ind["ma21"] = df_ind["close"].rolling(window=21).mean()
        df_ind["ma50"] = df_ind["close"].rolling(window=50).mean()
        df_ind["ma100"] = df_ind["close"].rolling(window=100).mean()

        # Cruces de medias móviles
        df_ind["ma_cross_7_21"] = (df_ind["ma7"] > df_ind["ma21"]).astype(int)
        df_ind["ma_cross_21_50"] = (df_ind["ma21"] > df_ind["ma50"]).astype(int)

        # Distancia porcentual de precio a medias móviles
        df_ind["price_to_ma7"] = (df_ind["close"] / df_ind["ma7"] - 1) * 100
        df_ind["price_to_ma21"] = (df_ind["close"] / df_ind["ma21"] - 1) * 100
        df_ind["price_to_ma50"] = (df_ind["close"] / df_ind["ma50"] - 1) * 100

        # RSI (Relative Strength Index)
        delta = df_ind["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df_ind["rsi"] = 100 - (100 / (1 + rs))

        # Stochastic Oscillator
        periodo = 14
        df_ind["lowest_low"] = df_ind["low"].rolling(window=periodo).min()
        df_ind["highest_high"] = df_ind["high"].rolling(window=periodo).max()
        df_ind["stoch_k"] = 100 * (
            (df_ind["close"] - df_ind["lowest_low"])
            / (df_ind["highest_high"] - df_ind["lowest_low"])
        )
        df_ind["stoch_d"] = df_ind["stoch_k"].rolling(window=3).mean()

        # Bandas de Bollinger
        df_ind["bb_middle"] = df_ind["ma21"]  # Banda media (SMA 21)
        std_dev = df_ind["close"].rolling(window=21).std()
        df_ind["bb_upper"] = df_ind["bb_middle"] + (std_dev * 2)  # Banda superior
        df_ind["bb_lower"] = df_ind["bb_middle"] - (std_dev * 2)  # Banda inferior
        df_ind["bb_width"] = (df_ind["bb_upper"] - df_ind["bb_lower"]) / df_ind[
            "bb_middle"
        ]  # Ancho de bandas

        # MACD (Moving Average Convergence Divergence)
        df_ind["ema12"] = df_ind["close"].ewm(span=12, adjust=False).mean()
        df_ind["ema26"] = df_ind["close"].ewm(span=26, adjust=False).mean()
        df_ind["macd"] = df_ind["ema12"] - df_ind["ema26"]
        df_ind["macd_signal"] = df_ind["macd"].ewm(span=9, adjust=False).mean()
        df_ind["macd_hist"] = df_ind["macd"] - df_ind["macd_signal"]

        # Tendencia (1 si sube, -1 si baja, 0 neutral) basado en EMA
        df_ind["trend"] = np.where(
            df_ind["ema12"] > df_ind["ema26"],
            1,
            np.where(df_ind["ema12"] < df_ind["ema26"], -1, 0),
        )

        # ATR (Average True Range) - Indicador de volatilidad
        high_low = df_ind["high"] - df_ind["low"]
        high_close = abs(df_ind["high"] - df_ind["close"].shift())
        low_close = abs(df_ind["low"] - df_ind["close"].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df_ind["atr"] = true_range.rolling(14).mean()
        df_ind["atr_percent"] = (
            df_ind["atr"] / df_ind["close"]
        ) * 100  # ATR como porcentaje del precio

        # ADX (Average Directional Index) - Fuerza de tendencia
        plus_dm = df_ind["high"].diff()
        minus_dm = df_ind["low"].diff(-1).abs()
        plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm), 0)
        minus_dm = minus_dm.where((minus_dm > 0) & (minus_dm > plus_dm), 0)

        tr = pd.DataFrame(
            {
                "high-low": df_ind["high"] - df_ind["low"],
                "high-prevclose": abs(df_ind["high"] - df_ind["close"].shift(1)),
                "low-prevclose": abs(df_ind["low"] - df_ind["close"].shift(1)),
            }
        ).max(axis=1)

        atr_14 = tr.rolling(window=14).mean()
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr_14)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr_14)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        df_ind["adx"] = dx.rolling(window=14).mean()
        df_ind["plus_di"] = plus_di
        df_ind["minus_di"] = minus_di

        # OBV (On-Balance Volume)
        df_ind["obv"] = (
            (df_ind["volume"] * (np.sign(df_ind["close"].diff()))).fillna(0).cumsum()
        )

        # Momentum
        df_ind["momentum"] = df_ind["close"] - df_ind["close"].shift(10)
        df_ind["momentum_percent"] = (
            df_ind["close"] / df_ind["close"].shift(10) - 1
        ) * 100

        # Canales de Donchian
        df_ind["donchian_high"] = df_ind["high"].rolling(window=20).max()
        df_ind["donchian_low"] = df_ind["low"].rolling(window=20).min()
        df_ind["donchian_mid"] = (df_ind["donchian_high"] + df_ind["donchian_low"]) / 2

        # Variación rango (diferencia entre máximos y mínimos)
        df_ind["range"] = df_ind["high"] - df_ind["low"]
        df_ind["range_ma"] = df_ind["range"].rolling(window=14).mean()
        df_ind["range_percent"] = (df_ind["range"] / df_ind["close"]) * 100

        # Fisher Transform del RSI
        rsi_scaled = (df_ind["rsi"] / 100) * 2 - 1  # Escalar RSI de 0-100 a -1 a 1
        fisher_rsi = 0.5 * np.log((1 + rsi_scaled) / (1 - rsi_scaled))
        df_ind["fisher_rsi"] = fisher_rsi.replace([np.inf, -np.inf], np.nan).fillna(0)

        # Variables objetivo para machine learning (n periodos hacia adelante)
        n_periodos = 3

        # Calcular volatilidad histórica para ajustar umbrales dinámicamente
        volatility = df_ind["returns"].std()
        umbral_long = volatility * 0.5  # Umbral dinámico basado en volatilidad
        umbral_short = -volatility * 0.5

        # Target para Long (1 si sube más del umbral en los próximos n_periodos)
        df_ind["target_long"] = (
            df_ind["close"].shift(-n_periodos).pct_change(n_periodos) > umbral_long
        )
        df_ind["target_long"] = df_ind["target_long"].astype(int)

        # Target para Short (1 si baja más del umbral en los próximos n_periodos)
        df_ind["target_short"] = (
            df_ind["close"].shift(-n_periodos).pct_change(n_periodos) < umbral_short
        )
        df_ind["target_short"] = df_ind["target_short"].astype(int)

        # Eliminar NaN
        df_ind = df_ind.dropna()

        return df_ind

    def procesar_order_book(self, order_book):
        """Procesa el order book para extraer métricas útiles."""
        if not order_book:
            return {}

        # Extraer asks y bids
        asks = order_book.get("a", [])
        bids = order_book.get("b", [])

        if not asks or not bids:
            return {}

        # Convertir a float
        asks = [[float(price), float(qty)] for price, qty in asks]
        bids = [[float(price), float(qty)] for price, qty in bids]

        # Calcular métricas
        ask_total_qty = sum(qty for _, qty in asks)
        bid_total_qty = sum(qty for _, qty in bids)

        # Calcular precios medios ponderados por volumen
        vwap_ask = (
            sum(price * qty for price, qty in asks) / ask_total_qty
            if ask_total_qty > 0
            else 0
        )
        vwap_bid = (
            sum(price * qty for price, qty in bids) / bid_total_qty
            if bid_total_qty > 0
            else 0
        )

        # Calcular imbalance ratio (>1 significa más presión compradora)
        imbalance = bid_total_qty / ask_total_qty if ask_total_qty > 0 else 1

        # Calcular spread
        best_ask = min(price for price, _ in asks) if asks else 0
        best_bid = max(price for price, _ in bids) if bids else 0
        spread = (best_ask - best_bid) / best_bid * 100 if best_bid > 0 else 0

        # Wall detection (grandes órdenes)
        ask_wall = max(qty for _, qty in asks) if asks else 0
        bid_wall = max(qty for _, qty in bids) if bids else 0

        # Distribución de órdenes (concentración cerca del precio)
        ask_price_levels = [price for price, _ in asks[:5]]  # 5 niveles cercanos al mid
        bid_price_levels = [price for price, _ in bids[:5]]

        # Pendiente de book (qué tan rápido se alejan los precios del mid)
        if len(ask_price_levels) >= 2 and len(bid_price_levels) >= 2:
            ask_slope = (ask_price_levels[-1] - ask_price_levels[0]) / (
                len(ask_price_levels) - 1
            )
            bid_slope = (bid_price_levels[0] - bid_price_levels[-1]) / (
                len(bid_price_levels) - 1
            )
        else:
            ask_slope = bid_slope = 0

        return {
            "ask_total_qty": ask_total_qty,
            "bid_total_qty": bid_total_qty,
            "vwap_ask": vwap_ask,
            "vwap_bid": vwap_bid,
            "imbalance": imbalance,
            "spread": spread,
            "ask_wall": ask_wall,
            "bid_wall": bid_wall,
            "best_ask": best_ask,
            "best_bid": best_bid,
            "ask_slope": ask_slope,
            "bid_slope": bid_slope,
        }

    def procesar_trades(self, trades):
        """Procesa los trades recientes para extraer métricas útiles."""
        if not trades:
            return {}

        # Convertir a DataFrame
        df_trades = pd.DataFrame(trades)

        # Convertir columnas numéricas (pueden venir como strings)
        for col in ["price", "size", "time"]:
            if col in df_trades.columns:
                df_trades[col] = pd.to_numeric(df_trades[col], errors="coerce")

        if df_trades.empty or "side" not in df_trades.columns:
            return {}

        # Separar por side
        buy_trades = df_trades[df_trades["side"] == "Buy"]
        sell_trades = df_trades[df_trades["side"] == "Sell"]

        # Calcular métricas
        buy_volume = buy_trades["size"].sum() if not buy_trades.empty else 0
        sell_volume = sell_trades["size"].sum() if not sell_trades.empty else 0

        # Ratio volumen compra/venta
        buy_sell_ratio = buy_volume / sell_volume if sell_volume > 0 else 1

        # Promedio tamaño de operaciones
        avg_buy_size = buy_trades["size"].mean() if not buy_trades.empty else 0
        avg_sell_size = sell_trades["size"].mean() if not sell_trades.empty else 0

        # Velocidad de trades (trades por minuto)
        if "time" in df_trades.columns and len(df_trades) > 1:
            try:
                df_trades["time"] = pd.to_datetime(
                    df_trades["time"], unit="ms", utc=True
                )
            except (OverflowError, ValueError) as e:
                print(f"Overflow en procesar_trades: {e}")
                df_trades["time"] = pd.to_datetime(
                    df_trades["time"] / 1000, unit="s", utc=True
                )
            time_span = (
                df_trades["time"].max() - df_trades["time"].min()
            ).total_seconds() / 60
            trade_velocity = len(df_trades) / time_span if time_span > 0 else 0
        else:
            trade_velocity = 0

        # Trading activity clusters (patrones de actividad)
        compras_grandes = (
            len(buy_trades[buy_trades["size"] > avg_buy_size * 2])
            if not buy_trades.empty
            else 0
        )
        ventas_grandes = (
            len(sell_trades[sell_trades["size"] > avg_sell_size * 2])
            if not sell_trades.empty
            else 0
        )

        return {
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "buy_sell_ratio": buy_sell_ratio,
            "avg_buy_size": avg_buy_size,
            "avg_sell_size": avg_sell_size,
            "trade_velocity": trade_velocity,
            "large_buys": compras_grandes,
            "large_sells": ventas_grandes,
        }

    def entrenar_modelos(self, df_ind):
        """Entrena modelos para predecir señales de Long y Short."""
        if df_ind is None or df_ind.empty or len(df_ind) < 50:
            return (
                False,
                "Datos insuficientes para entrenar los modelos (mínimo 50 registros)",
            )

        # Features para el modelo
        features = [
            "returns",
            "volatility_14",
            "volatility_7",
            "ma_cross_7_21",
            "ma_cross_21_50",
            "price_to_ma7",
            "price_to_ma21",
            "price_to_ma50",
            "rsi",
            "stoch_k",
            "stoch_d",
            "bb_width",
            "macd",
            "macd_hist",
            "trend",
            "atr_percent",
            "adx",
            "plus_di",
            "minus_di",
            "momentum_percent",
            "range_percent",
            "fisher_rsi",
        ]

        # Preparar datos
        X = df_ind[features].values  # noqa: N806
        y_long = df_ind["target_long"].values
        y_short = df_ind["target_short"].values

        # Verificar que haya al menos 2 clases en cada target
        unique_long = len(np.unique(y_long))
        unique_short = len(np.unique(y_short))

        if unique_long < 2:
            # Ajustar umbral para tener más variación
            print("Ajustando umbral de Long para mayor variación")
            # Usar percentiles en lugar de umbral fijo
            median_long = np.median(y_long)
            y_long = (y_long > median_long).astype(int)
            unique_long = len(np.unique(y_long))

        if unique_short < 2:
            print("Ajustando umbral de Short para mayor variación")
            median_short = np.median(y_short)
            y_short = (y_short > median_short).astype(int)
            unique_short = len(np.unique(y_short))

        # Si aún no hay 2 clases, usar mediana de retornos
        if unique_long < 2 or unique_short < 2:
            # Crear targets basados en la mediana de retornos futuros
            n_periodos = 3
            returns_futuros = df_ind["close"].shift(-n_periodos).pct_change(n_periodos)

            # Usar percentil 60 para Long y 40 para Short
            threshold_long = returns_futuros.quantile(0.5)
            threshold_short = returns_futuros.quantile(0.5)

            y_long = (returns_futuros > threshold_long).astype(int)
            y_short = (returns_futuros < threshold_short).astype(int)

            # Verificar nuevamente
            if len(np.unique(y_long)) < 2:
                y_long = np.random.randint(0, 2, size=len(y_long))
            if len(np.unique(y_short)) < 2:
                y_short = np.random.randint(0, 2, size=len(y_short))

        # Escalar características
        X_scaled = self.scaler.fit_transform(X)  # noqa: N806

        # Dividir en train/test
        X_train, X_test, y_long_train, y_long_test = train_test_split(  # noqa: N806
            X_scaled, y_long, test_size=0.2, random_state=42, shuffle=False
        )
        _, _, y_short_train, y_short_test = train_test_split(
            X_scaled, y_short, test_size=0.2, random_state=42, shuffle=False
        )

        # Entrenar modelo para Long
        self.model_long = GradientBoostingClassifier(
            n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42
        )
        self.model_long.fit(X_train, y_long_train)

        # Entrenar modelo para Short
        self.model_short = GradientBoostingClassifier(
            n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42
        )
        self.model_short.fit(X_train, y_short_train)

        # Evaluar modelos
        y_long_pred = self.model_long.predict(X_test)
        y_short_pred = self.model_short.predict(X_test)

        # Calcular métricas
        long_accuracy = accuracy_score(y_long_test, y_long_pred)
        long_precision = precision_score(y_long_test, y_long_pred, zero_division=0)
        long_recall = recall_score(y_long_test, y_long_pred, zero_division=0)
        long_f1 = f1_score(y_long_test, y_long_pred, zero_division=0)

        short_accuracy = accuracy_score(y_short_test, y_short_pred)
        short_precision = precision_score(y_short_test, y_short_pred, zero_division=0)
        short_recall = recall_score(y_short_test, y_short_pred, zero_division=0)
        short_f1 = f1_score(y_short_test, y_short_pred, zero_division=0)

        # Métricas de importancia de características
        long_feature_importance = dict(
            zip(features, self.model_long.feature_importances_)
        )
        short_feature_importance = dict(
            zip(features, self.model_short.feature_importances_)
        )

        return True, {
            "long_metrics": {
                "accuracy": long_accuracy,
                "precision": long_precision,
                "recall": long_recall,
                "f1": long_f1,
            },
            "short_metrics": {
                "accuracy": short_accuracy,
                "precision": short_precision,
                "recall": short_recall,
                "f1": short_f1,
            },
            "long_feature_importance": long_feature_importance,
            "short_feature_importance": short_feature_importance,
        }

    def generar_predicciones(self, df_ind, order_book_metrics=None, trade_metrics=None):
        """Genera predicciones de Long y Short basadas en datos actuales."""
        if self.model_long is None or self.model_short is None:
            return False, "Los modelos no han sido entrenados"

        if df_ind is None or df_ind.empty:
            return False, "No hay datos disponibles para la predicción"

        # Obtener últimos datos para predicción
        latest_data = df_ind.iloc[-1]

        # Preparar features
        features = [
            "returns",
            "volatility_14",
            "volatility_7",
            "ma_cross_7_21",
            "ma_cross_21_50",
            "price_to_ma7",
            "price_to_ma21",
            "price_to_ma50",
            "rsi",
            "stoch_k",
            "stoch_d",
            "bb_width",
            "macd",
            "macd_hist",
            "trend",
            "atr_percent",
            "adx",
            "plus_di",
            "minus_di",
            "momentum_percent",
            "range_percent",
            "fisher_rsi",
        ]

        # Verificar que todas las features estén disponibles
        for feat in features:
            if feat not in latest_data:
                return False, f"Feature '{feat}' no encontrada en los datos"

        X_pred = latest_data[features].values.reshape(1, -1)  # noqa: N806

        # Escalar
        X_scaled = self.scaler.transform(X_pred)  # noqa: N806

        # Realizar predicciones
        long_prediction = bool(self.model_long.predict(X_scaled)[0])
        short_prediction = bool(self.model_short.predict(X_scaled)[0])

        long_probability = self.model_long.predict_proba(X_scaled)[0][1]
        short_probability = self.model_short.predict_proba(X_scaled)[0][1]

        # Calcular fuerza de señal (combinación de probabilidad y métricas adicionales)
        long_strength = long_probability
        short_strength = short_probability

        # Ajustar fuerza en base a datos de order book
        if order_book_metrics:
            # Si hay más volumen de compra que de venta, reforzar señal Long
            if (
                order_book_metrics.get("imbalance", 1) > 1.2
            ):  # 20% más presión compradora
                long_strength *= 1.2
            elif (
                order_book_metrics.get("imbalance", 1) < 0.8
            ):  # 20% más presión vendedora
                short_strength *= 1.2

        # Ajustar fuerza en base a trades recientes
        if trade_metrics:
            # Si hay más volumen de compra que de venta, reforzar señal Long
            if trade_metrics.get("buy_sell_ratio", 1) > 1.2:
                long_strength *= 1.1
            elif trade_metrics.get("buy_sell_ratio", 1) < 0.8:
                short_strength *= 1.1

            # Grandes operaciones recientes
            if trade_metrics.get("large_buys", 0) > trade_metrics.get("large_sells", 0):
                long_strength *= 1.05
            elif trade_metrics.get("large_sells", 0) > trade_metrics.get(
                "large_buys", 0
            ):
                short_strength *= 1.05
            # Normalizar strengths para que sean entre 0 y 1
        max_strength = max(long_strength, short_strength)
        if max_strength > 1:
            long_strength /= max_strength
            short_strength /= max_strength

        # Preparar resultados
        resultados = {
            "symbol": latest_data.get("symbol", ""),
            "last_price": latest_data["close"],
            "long_signal": long_prediction,
            "short_signal": short_prediction,
            "long_probability": long_probability,
            "short_probability": short_probability,
            "long_strength": long_strength,
            "short_strength": short_strength,
            "decision": "LONG"
            if long_strength > short_strength and long_strength > self.umbral_prob
            else "SHORT"
            if short_strength > long_strength and short_strength > self.umbral_prob
            else "NEUTRAL",
            "indicators": {
                "rsi": latest_data["rsi"],
                "macd": latest_data["macd"],
                "bb_width": latest_data["bb_width"],
                "volatility": latest_data["volatility_14"],
                "trend": latest_data["trend"],
                "adx": latest_data["adx"],
                "stoch_k": latest_data["stoch_k"],
                "stoch_d": latest_data["stoch_d"],
            },
        }

        return True, resultados

    def generar_heatmap_data(self, df_ind):
        """Genera datos para el mapa de calor de correlación entre indicadores."""
        if df_ind is None or df_ind.empty:
            return None

        # Seleccionar columnas para el mapa de calor
        heatmap_cols = [
            "returns",
            "volatility_14",
            "ma_cross_7_21",
            "price_to_ma21",
            "rsi",
            "stoch_k",
            "bb_width",
            "macd",
            "macd_hist",
            "trend",
            "atr_percent",
            "adx",
            "momentum_percent",
            "fisher_rsi",
            "target_long",
            "target_short",
        ]

        # Verificar que todas las columnas estén presentes
        heatmap_cols = [col for col in heatmap_cols if col in df_ind.columns]

        # Calcular matriz de correlación
        corr_matrix = df_ind[heatmap_cols].corr()

        return corr_matrix

    def generar_mapa_calor_señales(self, df_ind):
        """Genera un mapa de calor de las señales en el tiempo."""
        if df_ind is None or df_ind.empty:
            return None

        # Crear DataFrame para el mapa de calor
        heatmap_df = pd.DataFrame(index=df_ind.index)

        # Añadir columnas de indicadores normalizados
        # RSI (0-100)
        heatmap_df["RSI"] = (df_ind["rsi"] - 50) / 50  # Normalizar alrededor de 50

        # Estocástico (0-100)
        heatmap_df["Stoch K"] = (df_ind["stoch_k"] - 50) / 50

        # MACD (normalizar por ATR para escala relativa)
        avg_atr = df_ind["atr"].mean()
        if avg_atr > 0:
            heatmap_df["MACD"] = df_ind["macd"] / (avg_atr * 10)
        else:
            heatmap_df["MACD"] = df_ind["macd"] / (df_ind["close"].mean() * 0.01)

        # ADX (0-100, >25 indica tendencia fuerte)
        heatmap_df["ADX"] = (df_ind["adx"] - 25) / 75

        # Tendencia (-1 a 1)
        heatmap_df["Trend"] = df_ind["trend"]

        # Distancia a medias móviles
        heatmap_df["Price-MA21%"] = df_ind["price_to_ma21"] / 10  # Normalizar

        # Volatilidad
        heatmap_df["Volatility"] = df_ind["volatility_14"] / (
            df_ind["volatility_14"].max() if df_ind["volatility_14"].max() > 0 else 0.01
        )

        # Momentum
        momentum_max = max(
            abs(df_ind["momentum_percent"].max()), abs(df_ind["momentum_percent"].min())
        )
        if momentum_max > 0:
            heatmap_df["Momentum"] = df_ind["momentum_percent"] / momentum_max
        else:
            heatmap_df["Momentum"] = df_ind["momentum_percent"]

        # Señales objetivo
        heatmap_df["Target Long"] = df_ind["target_long"]
        heatmap_df["Target Short"] = (
            df_ind["target_short"] * -1
        )  # Invertir para distinguir visualmente

        return heatmap_df

    def generar_datos_prediccion_futura(self, df, n_futuros=5):
        """Genera datos para la predicción futura del precio."""
        if df is None or df.empty or len(df) < 10:
            return None

        # Obtener último precio
        ultimo_precio = df["close"].iloc[-1]

        # Obtener último timestamp y calcular futuros
        if "datetime" in df.columns:
            ultima_fecha = df["datetime"].iloc[-1]
        else:
            try:
                df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            except (OverflowError, ValueError) as e:
                print(f"Overflow en generar_datos_prediccion_futura: {e}")
                df["datetime"] = pd.to_datetime(
                    df["timestamp"] / 1000, unit="s", utc=True
                )
            ultima_fecha = df["datetime"].iloc[-1]

        # Detectar intervalo
        if len(df) >= 2:
            intervalo = (
                df["datetime"].iloc[-1] - df["datetime"].iloc[-2]
            ).total_seconds() / 60
        else:
            intervalo = 15  # Default 15 minutos

        # Crear fechas futuras
        fechas_futuras = [
            ultima_fecha + timedelta(minutes=int(intervalo) * i)
            for i in range(1, n_futuros + 1)
        ]

        # Calcular indicadores si no están presentes
        if "rsi" not in df.columns and len(df) > 14:
            df_ind = self.calcular_indicadores(df)
        else:
            df_ind = df.copy() if "rsi" in df.columns else None

        # Predecir dirección usando los modelos
        if (
            hasattr(self, "model_long")
            and hasattr(self, "model_short")
            and self.model_long
            and self.model_short
            and df_ind is not None
        ):
            # Preparar features
            features = [
                "returns",
                "volatility_14",
                "volatility_7",
                "ma_cross_7_21",
                "ma_cross_21_50",
                "price_to_ma7",
                "price_to_ma21",
                "price_to_ma50",
                "rsi",
                "stoch_k",
                "stoch_d",
                "bb_width",
                "macd",
                "macd_hist",
                "trend",
                "atr_percent",
                "adx",
                "plus_di",
                "minus_di",
                "momentum_percent",
                "range_percent",
                "fisher_rsi",
            ]

            # Verificar que todas las features estén presentes
            if all(feat in df_ind.columns for feat in features):
                # Obtener últimos datos para predicción
                latest_data = df_ind.iloc[-1]
                X_pred = latest_data[features].values.reshape(1, -1)  # noqa: N806
                X_scaled = self.scaler.transform(X_pred)  # noqa: N806

                # Obtener probabilidades
                long_prob = self.model_long.predict_proba(X_scaled)[0][1]
                short_prob = self.model_short.predict_proba(X_scaled)[0][1]

                # Decidir dirección
                if long_prob > short_prob and long_prob > self.umbral_prob:
                    direccion = 1  # Arriba
                elif short_prob > long_prob and short_prob > self.umbral_prob:
                    direccion = -1  # Abajo
                else:
                    direccion = 0  # Neutral

                # Calcular cambio esperado basado en volatilidad
                volatilidad = (
                    df_ind["volatility_14"].iloc[-1]
                    if "volatility_14" in df_ind
                    else 0.005
                )
                cambio_base = volatilidad * ultimo_precio * 2

                # Ajustar cambio por dirección
                if direccion == 1:
                    cambio_esperado = cambio_base
                elif direccion == -1:
                    cambio_esperado = -cambio_base
                else:
                    cambio_esperado = 0

                # Calcular precios futuros
                precios_futuros = [ultimo_precio]
                for i in range(n_futuros):
                    # Mayor incertidumbre a medida que avanza el tiempo
                    factor_tiempo = (i + 1) * 0.5
                    nuevo_precio = (
                        precios_futuros[-1]
                        + (cambio_esperado / n_futuros) * factor_tiempo
                    )
                    precios_futuros.append(nuevo_precio)

                # Eliminar el primer precio (que es el último conocido)
                precios_futuros = precios_futuros[1:]

                return {
                    "fechas_futuras": fechas_futuras,
                    "precios_futuros": precios_futuros,
                    "direccion": direccion,
                    "long_prob": long_prob,
                    "short_prob": short_prob,
                }

        # Si no hay modelos, usar un enfoque simple basado en tendencia reciente
        ultimos_precios = df["close"].iloc[-5:].values
        tendencia = np.polyfit(range(len(ultimos_precios)), ultimos_precios, 1)[0]

        # Calcular precios futuros
        precios_futuros = [
            ultimo_precio + tendencia * i for i in range(1, n_futuros + 1)
        ]

        return {
            "fechas_futuras": fechas_futuras,
            "precios_futuros": precios_futuros,
            "direccion": 1 if tendencia > 0 else -1 if tendencia < 0 else 0,
            "long_prob": 0.5,
            "short_prob": 0.5,
        }

    def guardar_modelos(self, models_dir: Path) -> bool:
        """Save trained models and scalers to disk using joblib."""
        if self.model_long is None or self.model_short is None:
            return False
        try:
            models_dir.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.model_long, models_dir / "model_long.joblib")
            joblib.dump(self.model_short, models_dir / "model_short.joblib")
            joblib.dump(self.scaler, models_dir / "scaler.joblib")
            joblib.dump(self.mm_scaler, models_dir / "mm_scaler.joblib")
            return True
        except Exception as e:
            print(f"Error saving models: {e}")
            return False

    def cargar_modelos(self, models_dir: Path) -> bool:
        """Load trained models and scalers from disk if they exist."""
        model_long_path = models_dir / "model_long.joblib"
        model_short_path = models_dir / "model_short.joblib"
        scaler_path = models_dir / "scaler.joblib"
        mm_scaler_path = models_dir / "mm_scaler.joblib"

        if not (
            model_long_path.exists()
            and model_short_path.exists()
            and scaler_path.exists()
        ):
            return False
        try:
            self.model_long = joblib.load(model_long_path)
            self.model_short = joblib.load(model_short_path)
            self.scaler = joblib.load(scaler_path)
            if mm_scaler_path.exists():
                self.mm_scaler = joblib.load(mm_scaler_path)
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
