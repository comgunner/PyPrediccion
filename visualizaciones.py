"""Módulo para crear visualizaciones de datos de trading.

Incluye gráficos de precios, mapas de calor y paneles de indicadores.
"""

import matplotlib

# Usar backend compatible con Tkinter
matplotlib.use("TkAgg", force=True)

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Configuración de estilos y colores
COLORES = {
    "verde": "#4CAF50",  # Verde para señales Long
    "rojo": "#F44336",  # Rojo para señales Short
    "azul": "#2196F3",  # Azul para líneas predictivas
    "naranja": "#FF9800",  # Naranja para alertas
    "morado": "#9C27B0",  # Morado para métricas alternativas
    "gris": "#9E9E9E",  # Gris para neutral
    "verde_claro": "#A5D6A7",
    "rojo_claro": "#EF9A9A",
    "fondo": "#121212",  # Fondo oscuro
    "texto": "#FFFFFF",  # Texto claro
}


class Visualizador:
    """Clase para crear visualizaciones de datos de trading."""

    def __init__(self, modo_oscuro=True):
        """Inicializa el visualizador.

        Args:
            modo_oscuro: Si True, usa un tema oscuro para los gráficos

        """
        self.modo_oscuro = modo_oscuro
        if modo_oscuro:
            plt.style.use("dark_background")
            self.color_texto = "white"
            self.color_fondo = "#1e1e1e"
            self.color_grid = "#333333"
        else:
            plt.style.use("ggplot")
            self.color_texto = "black"
            self.color_fondo = "white"
            self.color_grid = "#cccccc"

        # Configuración de tamaño de texto
        plt.rcParams.update(
            {"font.size": 9, "axes.titlesize": 12, "axes.labelsize": 10}
        )

        # Configurar colores por defecto para figuras y ejes
        matplotlib.rcParams["figure.facecolor"] = self.color_fondo
        matplotlib.rcParams["axes.facecolor"] = self.color_fondo
        matplotlib.rcParams["axes.labelcolor"] = self.color_texto
        matplotlib.rcParams["xtick.color"] = self.color_texto
        matplotlib.rcParams["ytick.color"] = self.color_texto
        matplotlib.rcParams["axes.edgecolor"] = self.color_grid

    def crear_grafico_precios(
        self, fig, df, prediccion_futura=None, order_book=None, titulo=None
    ):
        """Crea un gráfico de precios con velas y predicción futura.

        Args:
            fig: Figura de matplotlib donde se dibujará
            df: DataFrame con los datos de precios (OHLCV)
            prediccion_futura: Dict con datos de predicción
            order_book: Dict con datos del order book
            titulo: Título del gráfico

        Returns:
            Figura actualizada

        """
        if df is None or df.empty:
            return fig

        # Asegurarse de tener columna datetime
        if "datetime" not in df.columns:
            try:
                df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            except (OverflowError, ValueError) as e:
                print(f"Overflow en crear_grafico_precios: {e}")
                df["datetime"] = pd.to_datetime(
                    df["timestamp"] / 1000, unit="s", utc=True
                )

        # Limpiar figura anterior
        fig.clear()

        # Configurar subplot principal para precios y subplot para volumen
        gs = fig.add_gridspec(2, 1, height_ratios=[3, 1])
        ax_precios = fig.add_subplot(gs[0])
        ax_volumen = fig.add_subplot(gs[1], sharex=ax_precios)

        # Configurar colores de los ejes
        for ax in [ax_precios, ax_volumen]:
            ax.set_facecolor(self.color_fondo)
            ax.tick_params(colors=self.color_texto)
            ax.spines["bottom"].set_color(self.color_grid)
            ax.spines["top"].set_color(self.color_grid)
            ax.spines["left"].set_color(self.color_grid)
            ax.spines["right"].set_color(self.color_grid)
            ax.xaxis.label.set_color(self.color_texto)
            ax.yaxis.label.set_color(self.color_texto)
            ax.title.set_color(self.color_texto)

        # Dibujar velas simplificadas
        for i in range(len(df)):
            # Color verde si cierre > apertura, rojo si cierre < apertura
            if df.iloc[i]["close"] >= df.iloc[i]["open"]:
                color = COLORES["verde"]
            else:
                color = COLORES["rojo"]

            # Línea de máximo a mínimo
            ax_precios.plot(
                [df.iloc[i]["datetime"], df.iloc[i]["datetime"]],
                [df.iloc[i]["low"], df.iloc[i]["high"]],
                color=color,
                linewidth=1,
            )

            # Rectángulo de apertura a cierre
            ax_precios.plot(
                [df.iloc[i]["datetime"], df.iloc[i]["datetime"]],
                [df.iloc[i]["open"], df.iloc[i]["close"]],
                color=color,
                linewidth=5,
            )

        # Añadir medias móviles si existen
        if "ma7" in df.columns:
            ax_precios.plot(
                df["datetime"],
                df["ma7"],
                color=COLORES["verde"],
                linewidth=1,
                alpha=0.8,
                label="MA7",
            )
        if "ma21" in df.columns:
            ax_precios.plot(
                df["datetime"],
                df["ma21"],
                color=COLORES["rojo"],
                linewidth=1,
                alpha=0.8,
                label="MA21",
            )
        if "ma50" in df.columns:
            ax_precios.plot(
                df["datetime"],
                df["ma50"],
                color=COLORES["azul"],
                linewidth=1,
                alpha=0.6,
                label="MA50",
            )

        # Añadir bandas de Bollinger si existen
        if all(col in df.columns for col in ["bb_upper", "bb_lower"]):
            ax_precios.plot(
                df["datetime"],
                df["bb_upper"],
                color=COLORES["gris"],
                linestyle="--",
                linewidth=1,
                alpha=0.6,
            )
            ax_precios.plot(
                df["datetime"],
                df["bb_lower"],
                color=COLORES["gris"],
                linestyle="--",
                linewidth=1,
                alpha=0.6,
            )

        # Añadir predicción futura si existe
        if prediccion_futura is not None:
            fechas_futuras = prediccion_futura.get("fechas_futuras")
            precios_futuros = prediccion_futura.get("precios_futuros")
            direccion = prediccion_futura.get("direccion", 0)

            if fechas_futuras and precios_futuros:
                # Color según dirección
                if direccion > 0:
                    color_prediccion = COLORES["verde"]
                elif direccion < 0:
                    color_prediccion = COLORES["rojo"]
                else:
                    color_prediccion = COLORES["azul"]

                # Dibujar línea de predicción futura
                ax_precios.plot(
                    fechas_futuras,
                    precios_futuros,
                    color=color_prediccion,
                    linestyle="--",
                    linewidth=2,
                    label="Predicción",
                )

                # Añadir área sombreada para mostrar incertidumbre
                std_estimado = (
                    df["close"].std() * 0.1
                )  # 10% de desviación estándar histórica
                precios_sup = [
                    p + std_estimado * (i + 1) for i, p in enumerate(precios_futuros)
                ]
                precios_inf = [
                    p - std_estimado * (i + 1) for i, p in enumerate(precios_futuros)
                ]

                ax_precios.fill_between(
                    fechas_futuras,
                    precios_inf,
                    precios_sup,
                    color=color_prediccion,
                    alpha=0.2,
                )

                # Añadir flechas direccionales en la última vela
                ultimo_precio = df["close"].iloc[-1]
                ultima_fecha = df["datetime"].iloc[-1]

                if direccion > 0:  # Tendencia alcista
                    ax_precios.scatter(
                        ultima_fecha,
                        ultimo_precio * 1.005,
                        marker="^",
                        s=80,
                        color=COLORES["verde"],
                    )
                elif direccion < 0:  # Tendencia bajista
                    ax_precios.scatter(
                        ultima_fecha,
                        ultimo_precio * 0.995,
                        marker="v",
                        s=80,
                        color=COLORES["rojo"],
                    )

                # Conectar último precio conocido con predicción
                ax_precios.plot(
                    [ultima_fecha, fechas_futuras[0]],
                    [ultimo_precio, precios_futuros[0]],
                    color=color_prediccion,
                    alpha=0.5,
                    linewidth=1,
                )

        # Añadir señales de compra/venta si están disponibles
        if "target_long" in df.columns and "target_short" in df.columns:
            # Señales de compra (long)
            indices_compra = df.index[df["target_long"] == 1]
            if len(indices_compra) > 0:
                fechas_compra = df.loc[indices_compra, "datetime"]
                precios_compra = (
                    df.loc[indices_compra, "low"] * 0.998
                )  # Ligeramente debajo
                ax_precios.scatter(
                    fechas_compra,
                    precios_compra,
                    marker="^",
                    s=60,
                    color=COLORES["verde"],
                    alpha=0.7,
                )

            # Señales de venta (short)
            indices_venta = df.index[df["target_short"] == 1]
            if len(indices_venta) > 0:
                fechas_venta = df.loc[indices_venta, "datetime"]
                precios_venta = (
                    df.loc[indices_venta, "high"] * 1.002
                )  # Ligeramente arriba
                ax_precios.scatter(
                    fechas_venta,
                    precios_venta,
                    marker="v",
                    s=60,
                    color=COLORES["rojo"],
                    alpha=0.7,
                )

        # Mostrar datos de book si están disponibles
        if order_book and "best_bid" in order_book and "best_ask" in order_book:
            ultima_fecha = df["datetime"].iloc[-1]
            bid = order_book["best_bid"]
            ask = order_book["best_ask"]

            # Dibujar líneas horizontales para bid y ask
            ax_precios.axhline(y=bid, color=COLORES["verde"], linestyle=":", alpha=0.6)
            ax_precios.axhline(y=ask, color=COLORES["rojo"], linestyle=":", alpha=0.6)

            # Añadir etiquetas
            ax_precios.text(
                ultima_fecha,
                bid * 0.9998,
                f"Bid: {bid:.2f}",
                color=COLORES["verde"],
                ha="right",
                fontsize=8,
            )
            ax_precios.text(
                ultima_fecha,
                ask * 1.0002,
                f"Ask: {ask:.2f}",
                color=COLORES["rojo"],
                ha="right",
                fontsize=8,
            )

        # Dibujar volumen
        if "volume" in df.columns:
            for i in range(len(df)):
                if df.iloc[i]["close"] >= df.iloc[i]["open"]:
                    color = COLORES["verde_claro"]
                else:
                    color = COLORES["rojo_claro"]
                ax_volumen.bar(
                    df.iloc[i]["datetime"],
                    df.iloc[i]["volume"],
                    color=color,
                    alpha=0.7,
                    width=0.7,
                )

            ax_volumen.set_ylabel("Volumen")

        # Configurar formato de ejes
        ax_precios.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m %H:%M"))
        ax_precios.set_ylabel("Precio")
        ax_precios.set_title(titulo or "Gráfico de Precios y Predicciones")
        ax_precios.grid(True, alpha=0.3)
        ax_precios.legend(loc="upper left")

        # Rotar etiquetas fecha para mejor visualización
        plt.setp(ax_volumen.get_xticklabels(), rotation=45, ha="right")

        fig.tight_layout()
        return fig

    def crear_mapa_calor(self, fig, corr_matrix):
        """Crea un mapa de calor de correlación entre indicadores.

        Args:
            fig: Figura de matplotlib donde se dibujará
            corr_matrix: Matriz de correlación

        Returns:
            Figura actualizada

        """
        if corr_matrix is None:
            return fig

        # Limpiar figura
        fig.clear()
        ax = fig.add_subplot(111)

        # Configurar colores del eje
        ax.set_facecolor(self.color_fondo)
        ax.tick_params(colors=self.color_texto)
        ax.spines["bottom"].set_color(self.color_grid)
        ax.spines["top"].set_color(self.color_grid)
        ax.spines["left"].set_color(self.color_grid)
        ax.spines["right"].set_color(self.color_grid)
        ax.xaxis.label.set_color(self.color_texto)
        ax.yaxis.label.set_color(self.color_texto)
        ax.title.set_color(self.color_texto)

        # Máscara para el triángulo superior
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

        # Crear mapa de calor
        cmap = sns.diverging_palette(230, 20, as_cmap=True)

        sns.heatmap(
            corr_matrix,
            mask=mask,
            annot=True,
            fmt=".2f",
            linewidths=0.5,
            cmap=cmap,
            center=0,
            ax=ax,
            annot_kws={"size": 8},
        )

        # Ajustar tamaño de etiquetas
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
        ax.set_yticklabels(ax.get_yticklabels(), fontsize=8)

        ax.set_title("Correlación entre Indicadores y Señales")

        fig.tight_layout()
        return fig

    def crear_mapa_calor_dinamico(self, fig, heatmap_df, ultimas_filas=20):
        """Crea un mapa de calor dinámico de la evolución de los indicadores.

        Args:
            fig: Figura de matplotlib donde se dibujará
            heatmap_df: DataFrame con los datos de indicadores normalizados
            ultimas_filas: Número de filas (periodos) a mostrar

        Returns:
            Figura actualizada

        """
        if heatmap_df is None or heatmap_df.empty:
            return fig

        # Tomar solo las últimas filas
        if len(heatmap_df) > ultimas_filas:
            heatmap_df = heatmap_df.iloc[-ultimas_filas:]

        # Limpiar figura
        fig.clear()
        ax = fig.add_subplot(111)

        # Configurar colores del eje
        ax.set_facecolor(self.color_fondo)
        ax.tick_params(colors=self.color_texto)
        ax.spines["bottom"].set_color(self.color_grid)
        ax.spines["top"].set_color(self.color_grid)
        ax.spines["left"].set_color(self.color_grid)
        ax.spines["right"].set_color(self.color_grid)
        ax.xaxis.label.set_color(self.color_texto)
        ax.yaxis.label.set_color(self.color_texto)
        ax.title.set_color(self.color_texto)

        # Crear mapa de calor
        cmap = sns.diverging_palette(10, 220, sep=80, n=7, as_cmap=True)

        # Convertir el índice a fechas formateadas
        heatmap_df = heatmap_df.copy()
        if isinstance(heatmap_df.index[0], pd.Timestamp):
            heatmap_df.index = [idx.strftime("%d-%m %H:%M") for idx in heatmap_df.index]

        # Crear el heatmap
        sns.heatmap(
            heatmap_df.T,
            cmap=cmap,
            center=0,
            linewidths=0.5,
            ax=ax,
            vmin=-1,
            vmax=1,
            cbar_kws={"shrink": 0.8},
        )

        # Ajustar etiquetas
        plt.yticks(rotation=0)
        plt.xticks(rotation=45, ha="right")

        ax.set_title("Evolución de Indicadores (Normalizado)")

        fig.tight_layout()
        return fig

    def crear_panel_indicadores(self, fig, resultado_prediccion):
        """Crea un panel visual con los principales indicadores y su estado.

        Args:
            fig: Figura de matplotlib donde se dibujará
            resultado_prediccion: Dict con el resultado de la predicción

        Returns:
            Figura actualizada

        """
        if resultado_prediccion is None:
            return fig

        # Limpiar figura
        fig.clear()

        # Configurar grid para paneles
        gs = fig.add_gridspec(2, 2)

        # Panel 1: Señales de trading
        ax_signals = fig.add_subplot(gs[0, 0])

        # Obtener datos
        long_prob = resultado_prediccion.get("long_probability", 0)
        short_prob = resultado_prediccion.get("short_probability", 0)
        long_strength = resultado_prediccion.get("long_strength", 0)
        short_strength = resultado_prediccion.get("short_strength", 0)
        decision = resultado_prediccion.get("decision", "NEUTRAL")

        # Gráfico de Gauge para la decisión
        if decision == "LONG":
            color_decision = COLORES["verde"]
            valor_gauge = 0.75  # Posición hacia Long (derecha)
        elif decision == "SHORT":
            color_decision = COLORES["rojo"]
            valor_gauge = 0.25  # Posición hacia Short (izquierda)
        else:
            color_decision = COLORES["gris"]
            valor_gauge = 0.5  # Neutral (centro)

        # Crear semicírculo de gauge (como un tacómetro)
        theta = np.linspace(0, np.pi, 100)
        r = 0.8
        x = r * np.cos(theta)
        y = r * np.sin(theta)

        # Pintar el fondo del gauge
        ax_signals.plot(x, y, color=self.color_grid, linewidth=15, alpha=0.3)

        # Marcar posición actual
        pos = np.pi * (1 - valor_gauge)
        x_pos = r * np.cos(pos)
        y_pos = r * np.sin(pos)
        ax_signals.scatter(x_pos, y_pos, s=300, color=color_decision, zorder=5)

        # Añadir etiquetas
        ax_signals.text(
            -0.7, 0.2, "SHORT", color=COLORES["rojo"], fontsize=10, ha="center"
        )
        ax_signals.text(
            0.7, 0.2, "LONG", color=COLORES["verde"], fontsize=10, ha="center"
        )
        ax_signals.text(
            0,
            -0.3,
            decision,
            color=color_decision,
            fontsize=14,
            weight="bold",
            ha="center",
        )

        # Eliminar ejes
        ax_signals.axis("off")
        ax_signals.set_xlim(-1, 1)
        ax_signals.set_ylim(-0.5, 1)

        # Panel 2: Indicadores técnicos
        ax_tech = fig.add_subplot(gs[0, 1])

        indicators = resultado_prediccion.get("indicators", {})
        if indicators:
            nombres = []
            valores = []
            colores = []

            # RSI
            rsi = indicators.get("rsi", 50)
            nombres.append("RSI")
            valores.append(rsi / 100)  # Normalizado a 0-1
            if rsi > 70:
                colores.append(COLORES["rojo"])  # Sobrecomprado
            elif rsi < 30:
                colores.append(COLORES["verde"])  # Sobrevendido
            else:
                colores.append(COLORES["gris"])

            # MACD
            macd = indicators.get("macd", 0)
            macd_norm = (macd + 1) / 2  # Normalizar de -1,1 a 0,1
            nombres.append("MACD")
            valores.append(min(max(macd_norm, 0), 1))
            if macd > 0:
                colores.append(COLORES["verde"])
            else:
                colores.append(COLORES["rojo"])

            # Estocástico
            stoch_k = indicators.get("stoch_k", 50)
            nombres.append("Stoch K")
            valores.append(stoch_k / 100)
            if stoch_k > 80:
                colores.append(COLORES["rojo"])
            elif stoch_k < 20:
                colores.append(COLORES["verde"])
            else:
                colores.append(COLORES["azul"])

            # ADX
            adx = indicators.get("adx", 15)
            nombres.append("ADX")
            valores.append(min(adx / 100, 1))
            if adx > 25:
                colores.append(COLORES["naranja"])
            else:
                colores.append(COLORES["gris"])

            # Volatilidad
            volatility = indicators.get("volatility", 0.01)
            nombres.append("Volatilidad")
            valores.append(min(volatility * 100, 1))
            colores.append(COLORES["morado"])

            # Crear barras horizontales para indicadores
            y_pos = range(len(nombres))
            bars = ax_tech.barh(y_pos, valores, color=colores, alpha=0.7)

            # Añadir etiquetas con valores reales
            for i, bar in enumerate(bars):
                width = bar.get_width()
                if nombres[i] == "RSI":
                    ax_tech.text(
                        width + 0.05,
                        bar.get_y() + bar.get_height() / 2,
                        f"{rsi:.1f}",
                        va="center",
                    )
                elif nombres[i] == "MACD":
                    ax_tech.text(
                        width + 0.05,
                        bar.get_y() + bar.get_height() / 2,
                        f"{macd:.4f}",
                        va="center",
                    )
                elif nombres[i] == "Stoch K":
                    ax_tech.text(
                        width + 0.05,
                        bar.get_y() + bar.get_height() / 2,
                        f"{stoch_k:.1f}",
                        va="center",
                    )
                elif nombres[i] == "ADX":
                    ax_tech.text(
                        width + 0.05,
                        bar.get_y() + bar.get_height() / 2,
                        f"{adx:.1f}",
                        va="center",
                    )
                elif nombres[i] == "Volatilidad":
                    ax_tech.text(
                        width + 0.05,
                        bar.get_y() + bar.get_height() / 2,
                        f"{volatility * 100:.2f}%",
                        va="center",
                    )

            ax_tech.set_xlim(0, 1.5)
            ax_tech.set_yticks(y_pos)
            ax_tech.set_yticklabels(nombres)
            ax_tech.set_title("Indicadores Técnicos")

        # Panel 3: Probabilidades
        ax_probs = fig.add_subplot(gs[1, 0])

        # Gráfico de barras para probabilidades
        names = ["Long", "Short"]
        probs = [long_prob, short_prob]
        strengths = [long_strength, short_strength]
        colors = [COLORES["verde"], COLORES["rojo"]]

        # Dibujar barras de probabilidad
        ax_probs.bar(
            names, probs, width=0.4, color=colors, alpha=0.5, label="Probabilidad"
        )

        # Dibujar barras de fuerza
        ax_probs.bar(
            [n + 0.4 for n in range(len(names))],
            strengths,
            width=0.4,
            color=colors,
            alpha=0.8,
            label="Fuerza",
        )

        # Etiquetas y formato
        ax_probs.set_ylim(0, 1)
        ax_probs.set_ylabel("Probabilidad")
        ax_probs.set_title("Probabilidades y Fuerza de Señal")
        ax_probs.yaxis.grid(True, alpha=0.3)
        ax_probs.legend()

        # Añadir threshold
        umbral = resultado_prediccion.get("umbral_prob", 0.65)
        ax_probs.axhline(y=umbral, color=self.color_texto, linestyle="--", alpha=0.5)
        ax_probs.text(0, umbral + 0.02, f"Umbral: {umbral}", fontsize=8)

        # Panel 4: Información adicional
        ax_info = fig.add_subplot(gs[1, 1])
        ax_info.axis("off")

        # Mostrar información del símbolo y precio
        symbol = resultado_prediccion.get("symbol", "")
        precio = resultado_prediccion.get("last_price", 0)

        info_text = (
            f"Símbolo: {symbol}\n"
            f"Precio: {precio:.4f}\n\n"
            f"Tendencia: {'Alcista' if indicators.get('trend', 0) > 0 else 'Bajista' if indicators.get('trend', 0) < 0 else 'Neutral'}\n"
            f"BB Width: {indicators.get('bb_width', 0):.4f}\n"
        )

        # Añadir texto informativo
        ax_info.text(0.1, 0.5, info_text, verticalalignment="center")

        fig.tight_layout()
        return fig

    def crear_panel_decision(self, fig, resultado_prediccion):
        """Crea un panel simplificado que muestra la decisión de trading recomendada.

        Args:
            fig: Figura de matplotlib donde se dibujará
            resultado_prediccion: Dict con el resultado de la predicción

        Returns:
            Figura actualizada

        """
        if resultado_prediccion is None:
            return fig

        # Limpiar figura
        fig.clear()
        ax = fig.add_subplot(111)

        # Determinar acción recomendada
        decision = resultado_prediccion.get("decision", "NEUTRAL")
        long_prob = resultado_prediccion.get("long_probability", 0)
        short_prob = resultado_prediccion.get("short_probability", 0)
        long_strength = resultado_prediccion.get("long_strength", 0)
        short_strength = resultado_prediccion.get("short_strength", 0)

        # Color según la decisión
        if decision == "LONG":
            color = COLORES["verde"]
            fuerza = long_strength
            emoji = "↗️"  # Emoji de flecha hacia arriba
        elif decision == "SHORT":
            color = COLORES["rojo"]
            fuerza = short_strength
            emoji = "↘️"  # Emoji de flecha hacia abajo
        else:
            color = COLORES["gris"]
            fuerza = max(long_strength, short_strength)
            emoji = "↔️"  # Emoji de flecha lateral

        # Mostrar símbolo y último precio
        symbol = resultado_prediccion.get("symbol", "")
        precio = resultado_prediccion.get("last_price", 0)

        # Crear un texto informativo
        info_text = f"Símbolo: {symbol}\nPrecio: {precio:.4f}"

        # Ocultar ejes
        ax.axis("off")

        # Mostrar decisión con emoji
        ax.text(
            0.5,
            0.7,
            f"{emoji} {decision} {emoji}",
            fontsize=32,
            weight="bold",
            ha="center",
            color=color,
        )

        # Mostrar fuerza de la señal como indicador visual
        ax.text(0.5, 0.5, f"Fuerza de señal: {fuerza:.2f}", fontsize=16, ha="center")

        # Barra de fuerza
        rect = plt.Rectangle((0.3, 0.45), 0.4 * fuerza, 0.03, color=color, alpha=0.8)
        ax.add_patch(rect)

        # Mostrar info adicional
        ax.text(0.5, 0.3, info_text, fontsize=12, ha="center")

        # Añadir probabilidades
        prob_text = f"Prob. LONG: {long_prob:.2f} | Prob. SHORT: {short_prob:.2f}"
        ax.text(0.5, 0.15, prob_text, fontsize=12, ha="center")

        fig.tight_layout()
        return fig

    def crear_grafico_avanzado(
        self,
        fig,
        df,
        df_indicadores,
        prediccion_futura=None,
        mostrar_ma=True,
        mostrar_bb=True,
        mostrar_signals=True,
    ):
        """Crea un gráfico avanzado con múltiples indicadores.

        Args:
            fig: Figura de matplotlib donde se dibujará
            df: DataFrame con datos de precios
            df_indicadores: DataFrame con indicadores calculados
            prediccion_futura: Dict con datos de predicción futura
            mostrar_ma: Si True, muestra medias móviles
            mostrar_bb: Si True, muestra bandas de Bollinger
            mostrar_signals: Si True, muestra señales de trading

        Returns:
            Figura actualizada

        """
        if df is None or df.empty:
            return fig

        # Asegurarse de tener columna datetime
        if "datetime" not in df.columns and "timestamp" in df.columns:
            try:
                df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            except (OverflowError, ValueError) as e:
                print(f"Overflow en crear_grafico_avanzado: {e}")
                df["datetime"] = pd.to_datetime(
                    df["timestamp"] / 1000, unit="s", utc=True
                )

        # Limpiar figura
        fig.clear()

        # Crear subplot principal para precios y subplots para indicadores
        gs = fig.add_gridspec(3, 1, height_ratios=[3, 1, 1])
        ax_precios = fig.add_subplot(gs[0])
        ax_vol = fig.add_subplot(gs[1], sharex=ax_precios)
        ax_ind = fig.add_subplot(gs[2], sharex=ax_precios)

        # Configurar colores de los ejes
        for ax in [ax_precios, ax_vol, ax_ind]:
            ax.set_facecolor(self.color_fondo)
            ax.tick_params(colors=self.color_texto)
            ax.spines["bottom"].set_color(self.color_grid)
            ax.spines["top"].set_color(self.color_grid)
            ax.spines["left"].set_color(self.color_grid)
            ax.spines["right"].set_color(self.color_grid)
            ax.xaxis.label.set_color(self.color_texto)
            ax.yaxis.label.set_color(self.color_texto)
            ax.title.set_color(self.color_texto)

        # Dibujar velas
        for i in range(len(df)):
            # Color verde si cierre > apertura, rojo si cierre < apertura
            if df.iloc[i]["close"] >= df.iloc[i]["open"]:
                color = COLORES["verde"]
            else:
                color = COLORES["rojo"]

            # Línea de máximo a mínimo
            ax_precios.plot(
                [df.iloc[i]["datetime"], df.iloc[i]["datetime"]],
                [df.iloc[i]["low"], df.iloc[i]["high"]],
                color=color,
                linewidth=1,
            )

            # Rectángulo de apertura a cierre
            ax_precios.plot(
                [df.iloc[i]["datetime"], df.iloc[i]["datetime"]],
                [df.iloc[i]["open"], df.iloc[i]["close"]],
                color=color,
                linewidth=5,
            )

        # Dibujar medias móviles si está habilitado
        if mostrar_ma and df_indicadores is not None:
            if "ma7" in df_indicadores.columns:
                ax_precios.plot(
                    df_indicadores["datetime"],
                    df_indicadores["ma7"],
                    color=COLORES["verde"],
                    linewidth=1,
                    alpha=0.8,
                    label="MA7",
                )
            if "ma21" in df_indicadores.columns:
                ax_precios.plot(
                    df_indicadores["datetime"],
                    df_indicadores["ma21"],
                    color=COLORES["rojo"],
                    linewidth=1,
                    alpha=0.8,
                    label="MA21",
                )
            if "ma50" in df_indicadores.columns:
                ax_precios.plot(
                    df_indicadores["datetime"],
                    df_indicadores["ma50"],
                    color=COLORES["azul"],
                    linewidth=1,
                    alpha=0.6,
                    label="MA50",
                )

        # Dibujar bandas de Bollinger si está habilitado
        if (
            mostrar_bb
            and df_indicadores is not None
            and all(col in df_indicadores.columns for col in ["bb_upper", "bb_lower"])
        ):
            ax_precios.plot(
                df_indicadores["datetime"],
                df_indicadores["bb_upper"],
                color=COLORES["gris"],
                linestyle="--",
                linewidth=1,
                alpha=0.6,
            )
            ax_precios.plot(
                df_indicadores["datetime"],
                df_indicadores["bb_lower"],
                color=COLORES["gris"],
                linestyle="--",
                linewidth=1,
                alpha=0.6,
            )

        # Dibujar señales si está habilitado
        if mostrar_signals and df_indicadores is not None:
            if "target_long" in df_indicadores.columns:
                # Señales de compra (long)
                indices_compra = df_indicadores.index[
                    df_indicadores["target_long"] == 1
                ]
                if len(indices_compra) > 0:
                    fechas_compra = df_indicadores.loc[indices_compra, "datetime"]
                    precios_compra = df_indicadores.loc[indices_compra, "low"] * 0.998
                    ax_precios.scatter(
                        fechas_compra,
                        precios_compra,
                        marker="^",
                        s=80,
                        color=COLORES["verde"],
                        alpha=0.7,
                        label="Long Signal",
                    )

            if "target_short" in df_indicadores.columns:
                # Señales de venta (short)
                indices_venta = df_indicadores.index[
                    df_indicadores["target_short"] == 1
                ]
                if len(indices_venta) > 0:
                    fechas_venta = df_indicadores.loc[indices_venta, "datetime"]
                    precios_venta = df_indicadores.loc[indices_venta, "high"] * 1.002
                    ax_precios.scatter(
                        fechas_venta,
                        precios_venta,
                        marker="v",
                        s=80,
                        color=COLORES["rojo"],
                        alpha=0.7,
                        label="Short Signal",
                    )

        # Dibujar predicción futura
        if prediccion_futura is not None:
            fechas_futuras = prediccion_futura.get("fechas_futuras")
            precios_futuros = prediccion_futura.get("precios_futuros")
            direccion = prediccion_futura.get("direccion", 0)

            if fechas_futuras and precios_futuros:
                if direccion > 0:
                    color_pred = COLORES["verde"]
                elif direccion < 0:
                    color_pred = COLORES["rojo"]
                else:
                    color_pred = COLORES["azul"]

                ax_precios.plot(
                    fechas_futuras,
                    precios_futuros,
                    color=color_pred,
                    linestyle="--",
                    linewidth=2,
                    label="Predicción",
                )

                # Área sombreada para incertidumbre
                std_estimado = df["close"].std() * 0.1
                precios_sup = [
                    p + std_estimado * (i + 1) for i, p in enumerate(precios_futuros)
                ]
                precios_inf = [
                    p - std_estimado * (i + 1) for i, p in enumerate(precios_futuros)
                ]

                ax_precios.fill_between(
                    fechas_futuras,
                    precios_inf,
                    precios_sup,
                    color=color_pred,
                    alpha=0.2,
                )

        # Dibujar volumen
        for i in range(len(df)):
            if df.iloc[i]["close"] >= df.iloc[i]["open"]:
                color = COLORES["verde_claro"]
            else:
                color = COLORES["rojo_claro"]
            ax_vol.bar(
                df.iloc[i]["datetime"],
                df.iloc[i]["volume"],
                color=color,
                alpha=0.7,
                width=0.7,
            )

        # Dibujar indicadores en el panel inferior
        if df_indicadores is not None and "rsi" in df_indicadores.columns:
            ax_ind.plot(
                df_indicadores["datetime"],
                df_indicadores["rsi"],
                color=COLORES["morado"],
                label="RSI",
            )

            # Líneas de sobrecompra/sobreventa
            ax_ind.axhline(y=70, color=COLORES["rojo"], linestyle="--", alpha=0.5)
            ax_ind.axhline(y=30, color=COLORES["verde"], linestyle="--", alpha=0.5)
            ax_ind.set_ylim(0, 100)

        # Configuración de gráficos
        symbol = (
            df_indicadores["symbol"].iloc[0]
            if df_indicadores is not None and "symbol" in df_indicadores.columns
            else ""
        )
        ax_precios.set_title(f"{symbol} - Análisis Técnico Avanzado")
        ax_precios.grid(True, alpha=0.3)
        ax_precios.legend(loc="upper left")

        ax_vol.set_ylabel("Volumen")
        ax_vol.grid(True, alpha=0.3)

        ax_ind.set_ylabel("RSI")
        ax_ind.grid(True, alpha=0.3)
        ax_ind.set_xlabel("Fecha")

        # Formatear eje x para fechas
        ax_precios.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m %H:%M"))
        plt.setp(ax_ind.get_xticklabels(), rotation=45, ha="right")

        fig.tight_layout()
        return fig

    def crear_grafico_multiplot(self, fig, df, indicadores_mostrar=None):
        """Crea un gráfico con múltiples subplots para diferentes indicadores.

        Args:
            fig: Figura de matplotlib donde se dibujará
            df: DataFrame con datos e indicadores
            indicadores_mostrar: Lista de indicadores a mostrar

        Returns:
            Figura actualizada

        """
        if df is None or df.empty:
            return fig

        if indicadores_mostrar is None:
            indicadores_mostrar = ["rsi", "macd", "stoch_k"]

        # Verificar qué indicadores están disponibles
        indicadores_disponibles = [
            ind for ind in indicadores_mostrar if ind in df.columns
        ]

        if len(indicadores_disponibles) == 0:
            return fig

        # Limpiar figura
        fig.clear()

        # Calcular número de subplots
        n_plots = len(indicadores_disponibles) + 1  # +1 para el gráfico de precios

        # Crear subplots
        gs = fig.add_gridspec(n_plots, 1, height_ratios=[3] + [1] * (n_plots - 1))

        # Gráfico de precios
        ax_precios = fig.add_subplot(gs[0])

        # Dibujar velas
        for i in range(len(df)):
            if df.iloc[i]["close"] >= df.iloc[i]["open"]:
                color = COLORES["verde"]
            else:
                color = COLORES["rojo"]

            ax_precios.plot(
                [df.iloc[i]["datetime"], df.iloc[i]["datetime"]],
                [df.iloc[i]["low"], df.iloc[i]["high"]],
                color=color,
                linewidth=1,
            )

            ax_precios.plot(
                [df.iloc[i]["datetime"], df.iloc[i]["datetime"]],
                [df.iloc[i]["open"], df.iloc[i]["close"]],
                color=color,
                linewidth=4,
            )

        # Añadir título y configuración
        symbol = df["symbol"].iloc[0] if "symbol" in df.columns else ""
        ax_precios.set_title(f"{symbol} - Análisis de Indicadores")
        ax_precios.grid(True, alpha=0.3)
        ax_precios.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m %H:%M"))

        # Crear gráficos para cada indicador
        for i, indicador in enumerate(indicadores_disponibles, 1):
            ax_ind = fig.add_subplot(gs[i], sharex=ax_precios)

            # Configuración específica por tipo de indicador
            if indicador == "rsi":
                ax_ind.plot(df["datetime"], df[indicador], color=COLORES["morado"])
                ax_ind.axhline(y=70, color=COLORES["rojo"], linestyle="--", alpha=0.5)
                ax_ind.axhline(y=30, color=COLORES["verde"], linestyle="--", alpha=0.5)
                ax_ind.set_ylim(0, 100)

            elif indicador == "macd":
                ax_ind.plot(
                    df["datetime"], df[indicador], color=COLORES["azul"], label="MACD"
                )
                if "macd_signal" in df.columns:
                    ax_ind.plot(
                        df["datetime"],
                        df["macd_signal"],
                        color=COLORES["naranja"],
                        label="Signal",
                    )
                if "macd_hist" in df.columns:
                    # Histograma con colores según signo
                    for j in range(len(df)):
                        if df.iloc[j]["macd_hist"] > 0:
                            color = COLORES["verde_claro"]
                        else:
                            color = COLORES["rojo_claro"]
                        ax_ind.bar(
                            df.iloc[j]["datetime"],
                            df.iloc[j]["macd_hist"],
                            color=color,
                            alpha=0.7,
                            width=0.7,
                        )
                ax_ind.axhline(y=0, color=self.color_texto, linestyle="-", alpha=0.2)
                ax_ind.legend(loc="upper left")

            elif indicador in ["stoch_k", "stoch_d"]:
                ax_ind.plot(
                    df["datetime"],
                    df[indicador],
                    color=COLORES["azul"]
                    if indicador == "stoch_k"
                    else COLORES["verde"],
                )
                if "stoch_d" in df.columns and indicador == "stoch_k":
                    ax_ind.plot(
                        df["datetime"],
                        df["stoch_d"],
                        color=COLORES["verde"],
                        label="Stoch D",
                    )
                ax_ind.axhline(y=80, color=COLORES["rojo"], linestyle="--", alpha=0.5)
                ax_ind.axhline(y=20, color=COLORES["verde"], linestyle="--", alpha=0.5)
                ax_ind.set_ylim(0, 100)

            elif indicador == "bb_width":
                ax_ind.plot(df["datetime"], df[indicador], color=COLORES["naranja"])
                # Añadir línea de promedio
                media_bb_width = df[indicador].mean()
                ax_ind.axhline(
                    y=media_bb_width, color=self.color_texto, linestyle="--", alpha=0.5
                )

            elif indicador == "adx":
                ax_ind.plot(
                    df["datetime"], df[indicador], color=COLORES["morado"], label="ADX"
                )
                if "plus_di" in df.columns and "minus_di" in df.columns:
                    ax_ind.plot(
                        df["datetime"],
                        df["plus_di"],
                        color=COLORES["verde"],
                        label="+DI",
                    )
                    ax_ind.plot(
                        df["datetime"],
                        df["minus_di"],
                        color=COLORES["rojo"],
                        label="-DI",
                    )
                ax_ind.axhline(y=25, color=self.color_texto, linestyle="--", alpha=0.5)
                ax_ind.legend(loc="upper left")

            else:
                # Configuración genérica para otros indicadores
                ax_ind.plot(df["datetime"], df[indicador], color=COLORES["azul"])

            # Configuración común
            ax_ind.set_ylabel(indicador.upper())
            ax_ind.grid(True, alpha=0.3)

            # Ocultar etiquetas del eje x excepto en el último subplot
            if i < len(indicadores_disponibles):
                plt.setp(ax_ind.get_xticklabels(), visible=False)
            else:
                plt.setp(ax_ind.get_xticklabels(), rotation=45, ha="right")

        fig.tight_layout()
        return fig
