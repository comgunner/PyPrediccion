"""Aplicación principal para el sistema de predicción y análisis de trading.

Interfaz gráfica que integra API, análisis de datos y visualizaciones.
"""

import threading
import time
import tkinter as tk
import traceback
from datetime import datetime
from tkinter import messagebox, scrolledtext, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from analizador_datos import AnalizadorDatos

# Importar módulos personalizados
from bybit_api import BybitAPI, SymbolInvalidError
from utils.config_manager import ConfigManager
from visualizaciones import COLORES, Visualizador


class AplicacionPredictor:
    """Aplicación para predicción de mercado de Bybit con mapas de calor."""

    def __init__(self, root):
        """Inicializa la aplicación y configura la interfaz gráfica principal."""
        self.root = root
        self.root.title("Heat Predictor - Trading Prediction System")
        self.root.geometry("1200x800")
        self.root.configure(bg="#F0F0F0")  # Color de fondo
        self.root.resizable(True, True)

        # Modo oscuro por defecto
        self.modo_oscuro = tk.BooleanVar(value=True)

        # Variables de control de UI (deben existir antes de cargar configuración)
        self.api_key_var = tk.StringVar()
        self.api_secret_var = tk.StringVar()
        self.symbol_var = tk.StringVar(value="BTCUSDT")
        self.intervalo_var = tk.StringVar(value="15")
        self.umbral_prob_var = tk.DoubleVar(value=0.65)

        # Cargar configuración persistente
        self.config_manager = ConfigManager()
        self._cargar_configuracion_guardada()

        # Crear instancias con credenciales desde configuración
        self.api = BybitAPI(
            api_key=self.config_manager.get("BYBIT_API_KEY"),
            api_secret=self.config_manager.get("BYBIT_API_SECRET"),
        )
        self.analizador = AnalizadorDatos()

        # Cargar modelos previamente entrenados si existen
        if self.analizador.cargar_modelos(self.config_manager.models_dir):
            print(f"Models loaded from: {self.config_manager.models_dir}")

        self.visualizador = Visualizador(modo_oscuro=self.modo_oscuro.get())

        # Variables de control
        self.monitoreo_activo = False
        self.thread_monitoreo = None

        # Datos para visualizaciones
        self.df_actual = None
        self.df_indicadores = None
        self.prediccion_actual = None
        self.order_book_actual = None
        self.trades_actuales = None

        # Configurar tema antes de crear las figuras
        self.configurar_tema()

        # Figuras para gráficos - configurar con fondo apropiado
        figure_kwargs = {"facecolor": self.bg_color, "edgecolor": self.bg_color}
        self.fig_precios = plt.figure(figsize=(10, 6), **figure_kwargs)
        self.fig_mapa_calor = plt.figure(figsize=(8, 6), **figure_kwargs)
        self.fig_indicadores = plt.figure(figsize=(6, 4), **figure_kwargs)
        self.fig_decision = plt.figure(figsize=(4, 3), **figure_kwargs)

        # Configurar la interfaz
        self.setup_ui()

    def configurar_tema(self):
        """Configura el tema claro u oscuro."""
        if self.modo_oscuro.get():
            # Tema oscuro
            self.bg_color = "#121212"
            self.fg_color = "white"
            self.accent_color = "#1976D2"
            self.widget_bg = "#1E1E1E"
            self.entry_bg = "#333333"
        else:
            # Tema claro
            self.bg_color = "#F0F0F0"
            self.fg_color = "black"
            self.accent_color = "#2196F3"
            self.widget_bg = "white"
            self.entry_bg = "#EEEEEE"

        # Aplicar tema a la ventana principal
        self.root.configure(bg=self.bg_color)

        # Configurar estilo de ttk
        style = ttk.Style()
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.fg_color)
        style.configure("TButton", background=self.accent_color)
        style.configure("TEntry", fieldbackground=self.entry_bg)
        style.configure("TNotebook", background=self.bg_color)
        style.configure(
            "TNotebook.Tab", background=self.widget_bg, foreground=self.fg_color
        )

        # Actualizar visualizador
        if hasattr(self, "visualizador"):
            self.visualizador = Visualizador(modo_oscuro=self.modo_oscuro.get())

    def _cargar_configuracion_guardada(self):
        """Populate UI variables from persisted configuration."""
        self.api_key_var.set(self.config_manager.get("BYBIT_API_KEY", ""))
        self.api_secret_var.set(self.config_manager.get("BYBIT_API_SECRET", ""))
        symbols = self.config_manager.get_symbols_list()
        self.symbol_var.set(symbols[0] if symbols else "BTCUSDT")
        self.intervalo_var.set(self.config_manager.get("INTERVAL", "15"))
        self.umbral_prob_var.set(self.config_manager.get("PROBABILITY_THRESHOLD", 0.65))
        self.modo_oscuro.set(self.config_manager.get("DARK_MODE", True))
        print(f"Config loaded from: {self.config_manager.config_path}")
        print(
            f"API configured: {'yes' if self.config_manager.is_configured() else 'no'}"
        )

    def setup_ui(self):
        """Configuración de la interfaz gráfica."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10", style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Crear notebook (pestañas)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Pestaña de Trading
        trading_tab = ttk.Frame(notebook)
        notebook.add(trading_tab, text="Trading")

        # Pestaña de configuración
        config_tab = ttk.Frame(notebook)
        notebook.add(config_tab, text="Configuración")

        # Pestaña de gráficos avanzados
        chart_tab = ttk.Frame(notebook)
        notebook.add(chart_tab, text="Gráficos")

        # Pestaña de mapas de calor
        heatmap_tab = ttk.Frame(notebook)
        notebook.add(heatmap_tab, text="Mapas de Calor")

        # Pestaña de logs
        log_tab = ttk.Frame(notebook)
        notebook.add(log_tab, text="Logs")

        # Configurar contenido de las pestañas
        self.setup_trading_tab(trading_tab)
        self.setup_config_tab(config_tab)
        self.setup_chart_tab(chart_tab)
        self.setup_heatmap_tab(heatmap_tab)
        self.setup_log_tab(log_tab)

        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Listo. Configure su API y par de trading.")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)

        # Obtener y mostrar la hora actual
        self.update_hora_actual()

    def setup_trading_tab(self, parent):
        """Configuración de la pestaña principal de trading."""
        # Panel principal dividido en izquierda y derecha
        panel = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Panel izquierdo para gráfico de precios
        left_frame = ttk.Frame(panel)
        panel.add(left_frame, weight=2)

        # Panel derecho para indicadores y decisión
        right_frame = ttk.Frame(panel)
        panel.add(right_frame, weight=1)

        # Frame superior para controles en panel izquierdo
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Dropdown para selección de símbolo
        ttk.Label(control_frame, text="Símbolo:").pack(side=tk.LEFT, padx=5)
        symbol_combo = ttk.Combobox(
            control_frame, textvariable=self.symbol_var, width=10
        )
        symbol_combo["values"] = self.config_manager.get_symbols_list() or (
            "BTCUSDT",
            "ETHUSDT",
            "SOLUSDT",
            "ADAUSDT",
            "BNBUSDT",
            "XRPUSDT",
        )
        symbol_combo.pack(side=tk.LEFT, padx=5)

        # Dropdown para selección de intervalo
        ttk.Label(control_frame, text="Intervalo:").pack(side=tk.LEFT, padx=5)
        interval_combo = ttk.Combobox(
            control_frame, textvariable=self.intervalo_var, width=5
        )
        interval_combo["values"] = ("1", "5", "15", "30", "60", "240", "D")
        interval_combo.pack(side=tk.LEFT, padx=5)

        # Botones de acción
        ttk.Button(
            control_frame, text="Actualizar", command=self.actualizar_datos
        ).pack(side=tk.LEFT, padx=5)

        # Monitoreo
        self.monitoreo_btn = ttk.Button(
            control_frame, text="Iniciar Monitoreo", command=self.toggle_monitoreo
        )
        self.monitoreo_btn.pack(side=tk.LEFT, padx=5)

        # Hora actual
        self.hora_label = ttk.Label(control_frame, text="--:--:--")
        self.hora_label.pack(side=tk.RIGHT, padx=10)
        ttk.Label(control_frame, text="Hora (GMT-6):").pack(side=tk.RIGHT)

        # Gráfico de precios
        chart_frame = ttk.Frame(left_frame)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        canvas = FigureCanvasTkAgg(self.fig_precios, master=chart_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas_precios = canvas

        # Frame para indicadores en panel derecho
        indicators_frame = ttk.Frame(right_frame)
        indicators_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Panel dividido vertical para indicadores y decisión
        panel_right = ttk.PanedWindow(indicators_frame, orient=tk.VERTICAL)
        panel_right.pack(fill=tk.BOTH, expand=True)

        # Panel superior para indicadores
        indicators_top = ttk.Frame(panel_right)
        panel_right.add(indicators_top, weight=2)

        # Panel inferior para decisión
        decision_bottom = ttk.Frame(panel_right)
        panel_right.add(decision_bottom, weight=1)

        # Canvas para indicadores
        canvas_ind = FigureCanvasTkAgg(self.fig_indicadores, master=indicators_top)
        canvas_ind.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas_indicadores = canvas_ind

        # Canvas para decisión
        canvas_dec = FigureCanvasTkAgg(self.fig_decision, master=decision_bottom)
        canvas_dec.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas_decision = canvas_dec

    def setup_config_tab(self, parent):
        """Configuración de la pestaña de configuración."""
        # Frame para API
        api_frame = ttk.LabelFrame(parent, text="Configuración de API", padding="10")
        api_frame.pack(fill=tk.X, padx=5, pady=5)

        # API Key
        ttk.Label(api_frame, text="API Key:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        ttk.Entry(api_frame, textvariable=self.api_key_var, width=50).grid(
            row=0, column=1, padx=5, pady=5
        )

        # API Secret
        ttk.Label(api_frame, text="API Secret:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        secret_entry = ttk.Entry(
            api_frame, textvariable=self.api_secret_var, width=50, show="*"
        )
        secret_entry.grid(row=1, column=1, padx=5, pady=5)

        # Frame para configuración de modelo
        model_frame = ttk.LabelFrame(
            parent, text="Configuración del Modelo", padding="10"
        )
        model_frame.pack(fill=tk.X, padx=5, pady=5)

        # Umbral de probabilidad
        ttk.Label(model_frame, text="Umbral de Probabilidad:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        threshold_scale = ttk.Scale(
            model_frame,
            from_=0.5,
            to=0.95,
            orient=tk.HORIZONTAL,
            variable=self.umbral_prob_var,
            length=200,
        )
        threshold_scale.grid(row=0, column=1, padx=5, pady=5)
        threshold_value = ttk.Label(model_frame, text="0.65")
        threshold_value.grid(row=0, column=2, padx=5, pady=5)

        # Actualizar etiqueta cuando cambia el umbral
        def update_threshold_label(*args):
            threshold_value.config(text=f"{self.umbral_prob_var.get():.2f}")
            self.analizador.umbral_prob = self.umbral_prob_var.get()

        # Python 3.12+: usar trace_add en lugar de trace
        if hasattr(self.umbral_prob_var, "trace_add"):
            self.umbral_prob_var.trace_add("write", update_threshold_label)
        else:
            self.umbral_prob_var.trace("w", update_threshold_label)

        # Frame para apariencia
        appearance_frame = ttk.LabelFrame(parent, text="Apariencia", padding="10")
        appearance_frame.pack(fill=tk.X, padx=5, pady=5)

        # Modo oscuro toggle
        dark_check = ttk.Checkbutton(
            appearance_frame,
            text="Modo Oscuro",
            variable=self.modo_oscuro,
            command=self.cambiar_tema,
        )
        dark_check.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        # Frame para botones
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=10)

        # Botón para guardar configuración
        ttk.Button(
            button_frame,
            text="Guardar Configuración",
            command=self.guardar_configuracion,
        ).pack(side=tk.LEFT, padx=5)

        # Botón para abrir archivo de configuración
        ttk.Button(
            button_frame,
            text="Abrir Config",
            command=self.abrir_archivo_config,
        ).pack(side=tk.LEFT, padx=5)

        # Botón para probar conexión
        ttk.Button(
            button_frame, text="Probar Conexión", command=self.probar_conexion
        ).pack(side=tk.LEFT, padx=5)

        # Botón para entrenar modelo
        ttk.Button(
            button_frame, text="Entrenar Modelos", command=self.entrenar_modelos
        ).pack(side=tk.LEFT, padx=5)

        # Botón para actualizar lista de pares
        ttk.Button(
            button_frame, text="Actualizar Pares", command=self.actualizar_lista_pares
        ).pack(side=tk.LEFT, padx=5)

    def setup_chart_tab(self, parent):
        """Configuración de la pestaña de gráficos avanzados."""
        # Panel de control
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Opciones de visualización
        ttk.Label(control_frame, text="Opciones de Visualización:").pack(
            side=tk.LEFT, padx=5
        )

        # Checkbuttons para diferentes indicadores
        self.show_ma = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            control_frame, text="Medias Móviles", variable=self.show_ma
        ).pack(side=tk.LEFT, padx=5)

        self.show_bb = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            control_frame, text="Bandas Bollinger", variable=self.show_bb
        ).pack(side=tk.LEFT, padx=5)

        self.show_signals = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Señales", variable=self.show_signals).pack(
            side=tk.LEFT, padx=5
        )

        # Botón para actualizar
        ttk.Button(
            control_frame,
            text="Actualizar Gráfico",
            command=self.actualizar_grafico_avanzado,
        ).pack(side=tk.RIGHT, padx=5)

        # Frame para el gráfico
        chart_frame = ttk.Frame(parent)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Canvas grande para gráfico avanzado
        self.fig_avanzado = plt.figure(figsize=(10, 8))
        canvas_adv = FigureCanvasTkAgg(self.fig_avanzado, master=chart_frame)
        canvas_adv.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas_avanzado = canvas_adv

    def setup_heatmap_tab(self, parent):
        """Configuración de la pestaña de mapas de calor."""
        # Panel dividido horizontalmente
        panel = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Panel izquierdo para mapa de calor de correlación
        left_frame = ttk.Frame(panel)
        panel.add(left_frame, weight=1)

        # Panel derecho para mapa de calor dinámico
        right_frame = ttk.Frame(panel)
        panel.add(right_frame, weight=1)

        # Panel de control izquierdo
        control_left = ttk.Frame(left_frame)
        control_left.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(control_left, text="Mapa de Correlación:").pack(side=tk.LEFT, padx=5)
        ttk.Button(
            control_left, text="Actualizar", command=self.actualizar_mapa_correlacion
        ).pack(side=tk.RIGHT, padx=5)

        # Canvas para mapa de correlación
        corr_frame = ttk.Frame(left_frame)
        corr_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        canvas_corr = FigureCanvasTkAgg(self.fig_mapa_calor, master=corr_frame)
        canvas_corr.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas_mapa_calor = canvas_corr

        # Panel de control derecho
        control_right = ttk.Frame(right_frame)
        control_right.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(control_right, text="Mapa de Calor Dinámico:").pack(
            side=tk.LEFT, padx=5
        )

        ttk.Label(control_right, text="Períodos:").pack(side=tk.LEFT, padx=5)
        self.periodos_var = tk.StringVar(value="20")
        periodos_combo = ttk.Combobox(
            control_right, textvariable=self.periodos_var, width=5
        )
        periodos_combo["values"] = ("10", "20", "50", "100")
        periodos_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_right, text="Actualizar", command=self.actualizar_mapa_dinamico
        ).pack(side=tk.RIGHT, padx=5)

        # Canvas para mapa dinámico
        dyn_frame = ttk.Frame(right_frame)
        dyn_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.fig_mapa_dinamico = plt.figure(figsize=(8, 6))
        canvas_dyn = FigureCanvasTkAgg(self.fig_mapa_dinamico, master=dyn_frame)
        canvas_dyn.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas_mapa_dinamico = canvas_dyn

    def setup_log_tab(self, parent):
        """Configuración de la pestaña de logs."""
        # Panel de control
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(control_frame, text="Registro de Actividad:").pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(control_frame, text="Limpiar Log", command=self.limpiar_log).pack(
            side=tk.RIGHT, padx=5
        )

        # Área de log
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        # Configurar colores para el área de log
        self.log_text.tag_configure("info", foreground="white")
        self.log_text.tag_configure("warning", foreground="orange")
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("success", foreground="green")

        # Log inicial
        self.log("Sistema iniciado. Configure la API y el par de trading.", "info")

        # Registrar handler de cierre limpio
        self._after_hora_id = None
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)

    def cerrar_aplicacion(self):
        """Shut down background threads and scheduled callbacks before destroying the window."""
        # Detener loop de monitoreo
        self.monitoreo_activo = False

        # Cancelar callback periódico de hora
        if self._after_hora_id is not None:
            self.root.after_cancel(self._after_hora_id)
            self._after_hora_id = None

        # Cerrar figuras de matplotlib para liberar memoria
        plt.close("all")

        self.root.quit()
        self.root.destroy()

    def update_hora_actual(self):
        """Actualiza la hora actual en la interfaz."""
        hora_actual = self.api.obtener_hora_gmt6()
        hora_str = hora_actual.strftime("%Y-%m-%d %H:%M:%S")
        self.hora_label.config(text=hora_str)

        # Programar próxima actualización y guardar ID para poder cancelarla
        self._after_hora_id = self.root.after(1000, self.update_hora_actual)

    def guardar_configuracion(self):
        """Save API credentials and model settings to persistent configuration."""
        api_key = self.api_key_var.get().strip()
        api_secret = self.api_secret_var.get().strip()

        self.config_manager.set("BYBIT_API_KEY", api_key)
        self.config_manager.set("BYBIT_API_SECRET", api_secret)
        self.config_manager.set("SYMBOL", self.symbol_var.get())
        self.config_manager.set("INTERVAL", self.intervalo_var.get())
        self.config_manager.set("PROBABILITY_THRESHOLD", self.umbral_prob_var.get())
        self.config_manager.set("DARK_MODE", self.modo_oscuro.get())

        if self.config_manager.save():
            self.api.api_key = api_key
            self.api.api_secret = api_secret
            self.analizador.umbral_prob = self.umbral_prob_var.get()
            messagebox.showinfo(
                "Configuración",
                f"Configuración guardada correctamente\n\nRuta: {self.config_manager.config_path}",
            )
            self.status_var.set(
                f"Config guardada. Par: {self.symbol_var.get()}, Intervalo: {self.intervalo_var.get()}"
            )
            self.log("Configuración guardada correctamente", "success")
            self.log(f"Ruta: {self.config_manager.config_path}", "info")
        else:
            messagebox.showerror("Error", "No se pudo guardar la configuración")
            self.log("Error al guardar configuración", "error")

    def abrir_archivo_config(self):
        """Open the configuration file using the system default editor."""
        self.config_manager.open_config_file()
        self.log(
            f"Abriendo archivo de configuración: {self.config_manager.config_path}",
            "info",
        )

    def _eliminar_simbolo_invalido(self, symbol: str) -> None:
        """Remove an invalid symbol from config and switch to the next available one."""
        self.log(
            f"Símbolo no disponible en Bybit: {symbol} — eliminado del config",
            "warning",
        )

        symbols = self.config_manager.get_symbols_list()
        symbols = [s for s in symbols if s != symbol]

        if symbols:
            self.config_manager.set("SYMBOL", ",".join(symbols))
            self.config_manager.save()

            # Actualizar dropdown con la lista limpia
            next_symbol = symbols[0]
            self.symbol_var.set(next_symbol)

            # Actualizar valores del combobox
            for widget in self.root.winfo_children():
                self._update_symbol_combo(widget, symbols)

            self.status_var.set(f"'{symbol}' eliminado. Usando: {next_symbol}")
            self.log(f"Cambiando a {next_symbol}", "info")
        else:
            self.config_manager.set("SYMBOL", "BTCUSDT")
            self.config_manager.save()
            self.symbol_var.set("BTCUSDT")
            self.status_var.set(
                f"'{symbol}' eliminado. Sin símbolos válidos, usando BTCUSDT"
            )
            self.log(
                "No quedan símbolos válidos en config, usando BTCUSDT por defecto",
                "warning",
            )

    def _update_symbol_combo(self, widget, symbols: list) -> None:
        """Recursively update symbol Combobox values in widget tree."""
        from tkinter import ttk as _ttk

        if isinstance(widget, _ttk.Combobox) and "BTCUSDT" in str(
            widget.cget("values")
        ):
            widget["values"] = symbols
        for child in widget.winfo_children():
            self._update_symbol_combo(child, symbols)

    def probar_conexion(self):
        """Prueba la conexión a la API de Bybit."""
        self.status_var.set("Probando conexión...")
        self.root.update_idletasks()

        try:
            # Intentar obtener datos para probar la conexión
            symbol = self.symbol_var.get()
            result = self.api.obtener_datos_mercado(
                symbol, intervalo=self.intervalo_var.get(), limit=10
            )

            if result:
                messagebox.showinfo("Conexión", "Conexión establecida correctamente")
                self.status_var.set("Conexión establecida correctamente")
                self.log(f"Conexión establecida correctamente para {symbol}", "success")
                return True
            else:
                messagebox.showerror(
                    "Error", "No se pudo establecer conexión con la API"
                )
                self.status_var.set("Error de conexión")
                self.log("Error al conectar con la API", "error")
                return False
        except Exception as e:
            messagebox.showerror("Error", f"Error al conectar: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
            self.log(f"Error de conexión: {str(e)}", "error")
            return False

    def entrenar_modelos(self):
        """Entrena los modelos de predicción."""
        self.status_var.set("Entrenando modelos...")
        self.root.update_idletasks()

        # Verificar si ya hay datos cargados
        if self.df_indicadores is None:
            self.actualizar_datos()
            if self.df_indicadores is None:
                return

        try:
            # Entrenar modelos
            success, result = self.analizador.entrenar_modelos(self.df_indicadores)

            if success:
                long_acc = result["long_metrics"]["accuracy"]
                short_acc = result["short_metrics"]["accuracy"]

                mensaje = (
                    f"Modelos entrenados correctamente\n"
                    f"Precisión Long: {long_acc:.2f}\n"
                    f"Precisión Short: {short_acc:.2f}"
                )

                messagebox.showinfo("Entrenamiento", mensaje)
                self.status_var.set(
                    f"Modelos entrenados - Long: {long_acc:.2f}, Short: {short_acc:.2f}"
                )
                self.log(
                    f"Modelos entrenados. Long acc: {long_acc:.2f}, Short acc: {short_acc:.2f}",
                    "success",
                )

                # Logging de features más importantes
                self.log("Top 5 features para Long:", "info")
                long_importance = sorted(
                    result["long_feature_importance"].items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5]
                for feature, importance in long_importance:
                    self.log(f"  {feature}: {importance:.4f}", "info")

                self.log("Top 5 features para Short:", "info")
                short_importance = sorted(
                    result["short_feature_importance"].items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5]
                for feature, importance in short_importance:
                    self.log(f"  {feature}: {importance:.4f}", "info")

                # Guardar modelos para futuros inicios
                if self.analizador.guardar_modelos(self.config_manager.models_dir):
                    self.log(
                        f"Modelos guardados en {self.config_manager.models_dir}", "info"
                    )
            else:
                messagebox.showerror("Error", f"Error al entrenar modelos: {result}")
                self.status_var.set(f"Error: {result}")
                self.log(f"Error al entrenar modelos: {result}", "error")
        except Exception as e:
            messagebox.showerror("Error", f"Error durante el entrenamiento: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
            self.log(f"Error durante entrenamiento: {str(e)}", "error")

    def actualizar_datos(self):
        """Obtiene y procesa datos actualizados del mercado."""
        self.status_var.set("Actualizando datos...")
        self.root.update_idletasks()

        try:
            # Obtener datos del mercado
            symbol = self.symbol_var.get()
            intervalo = self.intervalo_var.get()

            # Klines
            kline_data = self.api.obtener_datos_mercado(
                symbol, intervalo=intervalo, limit=200
            )
            if not kline_data:
                messagebox.showerror(
                    "Error", "No se pudieron obtener datos del mercado"
                )
                self.status_var.set("Error al obtener datos")
                self.log(f"Error al obtener datos de {symbol}", "error")
                return

            self.log(f"Datos crudos obtenidos: {len(kline_data)} velas", "info")

            # Procesar klines
            try:
                self.df_actual = self.analizador.procesar_klines(kline_data)
                self.log(f"Klines procesados: {len(self.df_actual)} registros", "info")
            except Exception as e:
                tb = traceback.format_exc()
                self.log(f"Error en procesar_klines: {str(e)}", "error")
                self.log(f"Traceback completo: {tb}", "error")
                raise

            # Calcular indicadores
            try:
                self.df_indicadores = self.analizador.calcular_indicadores(
                    self.df_actual
                )
                self.log("Indicadores calculados", "info")
            except Exception as e:
                tb = traceback.format_exc()
                self.log(f"Error en calcular_indicadores: {str(e)}", "error")
                self.log(f"Traceback completo: {tb}", "error")
                raise

            # Order book
            self.order_book_actual = self.api.obtener_book_orders(symbol)
            order_book_metrics = self.analizador.procesar_order_book(
                self.order_book_actual
            )

            # Trades recientes
            trades_data = self.api.obtener_trades_recientes(symbol)
            self.trades_actuales = self.analizador.procesar_trades(trades_data)

            # Generar predicción si hay modelos entrenados
            if (
                hasattr(self.analizador, "model_long")
                and self.analizador.model_long is not None
            ):
                success, self.prediccion_actual = self.analizador.generar_predicciones(
                    self.df_indicadores, order_book_metrics, self.trades_actuales
                )

                if success:
                    decision = self.prediccion_actual.get("decision", "NEUTRAL")
                    long_prob = self.prediccion_actual.get("long_probability", 0)
                    short_prob = self.prediccion_actual.get("short_probability", 0)

                    self.log(
                        f"Predicción para {symbol}: {decision}",
                        "success" if decision != "NEUTRAL" else "info",
                    )
                    self.log(
                        f"  Long prob: {long_prob:.2f}, Short prob: {short_prob:.2f}",
                        "info",
                    )

                    # Mostrar información en la barra de estado
                    self.status_var.set(
                        f"{symbol}: {decision} (Long: {long_prob:.2f}, Short: {short_prob:.2f})"
                    )
                else:
                    self.prediccion_actual = None
                    self.status_var.set("Datos actualizados. Sin predicción")
                    self.log(
                        f"No se pudo generar predicción: {self.prediccion_actual}",
                        "warning",
                    )
            else:
                self.prediccion_actual = None
                self.status_var.set("Datos actualizados. Entrene los modelos primero")
                self.log(
                    "Datos obtenidos. Los modelos necesitan ser entrenados", "info"
                )

            # Actualizar visualizaciones
            self.actualizar_visualizaciones()

            # Log de información relevante
            self.log(
                f"Actualizados {len(self.df_actual)} registros para {symbol} ({intervalo}min)",
                "info",
            )
            ultimo_precio = (
                self.df_actual["close"].iloc[-1] if self.df_actual is not None else None
            )
            if ultimo_precio:
                self.log(f"Último precio: {ultimo_precio:.4f}", "info")

            return True
        except SymbolInvalidError as e:
            self._eliminar_simbolo_invalido(str(e).split(":")[0])
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar datos: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
            self.log(f"Error al actualizar datos: {str(e)}", "error")
            return False

    def actualizar_visualizaciones(self):
        """Actualiza todas las visualizaciones con los datos actuales."""
        if self.df_actual is None:
            return

        try:
            # Generar datos de predicción futura para el gráfico
            prediccion_futura = self.analizador.generar_datos_prediccion_futura(
                self.df_actual
            )

            # Actualizar gráfico de precios
            self.fig_precios = self.visualizador.crear_grafico_precios(
                self.fig_precios,
                self.df_actual,
                prediccion_futura,
                self.order_book_actual,
                f"{self.symbol_var.get()} ({self.intervalo_var.get()}min)",
            )
            self.canvas_precios.draw()
            self.canvas_precios.flush_events()

            # Actualizar panel de indicadores
            if self.prediccion_actual is not None:
                self.fig_indicadores = self.visualizador.crear_panel_indicadores(
                    self.fig_indicadores, self.prediccion_actual
                )
                self.canvas_indicadores.draw()
                self.canvas_indicadores.flush_events()

                # Actualizar panel de decisión
                self.fig_decision = self.visualizador.crear_panel_decision(
                    self.fig_decision, self.prediccion_actual
                )
                self.canvas_decision.draw()
                self.canvas_decision.flush_events()
        except Exception as e:
            tb = traceback.format_exc()
            self.log(f"Error al actualizar visualizaciones: {str(e)}", "error")
            self.log(f"Traceback completo: {tb}", "error")

    def cambiar_tema(self):
        """Cambia entre tema claro y oscuro."""
        # Configurar colores según el tema
        self.configurar_tema()

        # Actualizar fondo de las figuras
        for fig in [
            self.fig_precios,
            self.fig_mapa_calor,
            self.fig_indicadores,
            self.fig_decision,
        ]:
            if fig is not None:
                fig.set_facecolor(self.bg_color)
                fig.set_edgecolor(self.bg_color)

        # Actualizar visualizador
        self.visualizador = Visualizador(modo_oscuro=self.modo_oscuro.get())

        # Re-aplicar tema a elementos
        if self.modo_oscuro.get():
            self.log_text.config(bg="#1E1E1E", fg="white")
        else:
            self.log_text.config(bg="white", fg="black")

        # Actualizar visualizaciones
        if self.df_actual is not None:
            self.actualizar_visualizaciones()

        # Log del cambio
        theme_name = "oscuro" if self.modo_oscuro.get() else "claro"
        self.log(f"Tema cambiado a {theme_name}", "info")

    def actualizar_lista_pares(self):
        """Actualiza la lista de pares disponibles desde la API."""
        self.status_var.set("Actualizando lista de pares...")
        self.root.update_idletasks()

        try:
            # Obtener datos de tickers
            tickers = self.api.obtener_tickers()
            if not tickers:
                messagebox.showwarning(
                    "Advertencia", "No se pudieron obtener los pares disponibles"
                )
                return

            # Filtrar los pares con USDT
            usdt_pairs = [
                ticker.get("symbol")
                for ticker in tickers
                if ticker.get("symbol", "").endswith("USDT")
            ]

            # Seleccionar los más populares o de mayor volumen
            popular_pairs = usdt_pairs[:20] if len(usdt_pairs) > 20 else usdt_pairs

            # Actualizar comboboxes
            for combo in self.root.winfo_children():
                if (
                    isinstance(combo, ttk.Combobox)
                    and combo.cget("values")
                    and "BTCUSDT" in combo.cget("values")
                ):
                    combo["values"] = popular_pairs

            # Log de la actualización
            self.log(
                f"Lista de pares actualizada, {len(popular_pairs)} pares disponibles",
                "info",
            )
        except Exception as e:
            self.log(f"Error al actualizar lista de pares: {str(e)}", "error")

    def toggle_monitoreo(self):
        """Inicia o detiene el monitoreo continuo."""
        if self.monitoreo_activo:
            # Detener monitoreo
            self.monitoreo_activo = False
            self.monitoreo_btn.config(text="Iniciar Monitoreo")
            self.status_var.set("Monitoreo detenido")
            self.log("Monitoreo detenido", "info")
        else:
            # Verificar si hay modelos entrenados
            if (
                not hasattr(self.analizador, "model_long")
                or self.analizador.model_long is None
            ):
                # Intentar obtener datos y entrenar automáticamente
                self.log("Modelos no entrenados. Intentando entrenar...", "info")
                self.status_var.set("Obteniendo datos y entrenando modelos...")
                self.root.update_idletasks()

                # Primero obtener datos
                if not self.actualizar_datos():
                    messagebox.showerror(
                        "Error",
                        "No se pudieron obtener datos del mercado.\n"
                        "Verifique su conexión a internet y configuración de API.",
                    )
                    return

                # Entrenar modelos
                success, result = self.analizador.entrenar_modelos(self.df_indicadores)

                if not success:
                    messagebox.showerror(
                        "Error",
                        f"No se pudieron entrenar los modelos:\n{result}",
                    )
                    return

                # Mostrar resultados del entrenamiento
                long_acc = result["long_metrics"]["accuracy"]
                short_acc = result["short_metrics"]["accuracy"]

                self.log(
                    f"Modelos entrenados automáticamente - Long: {long_acc:.2f}, Short: {short_acc:.2f}",
                    "success",
                )

                messagebox.showinfo(
                    "Modelos Entrenados",
                    f"Modelos entrenados exitosamente:\n"
                    f"Precisión Long: {long_acc:.2f}\n"
                    f"Precisión Short: {short_acc:.2f}\n\n"
                    f"El monitoreo se iniciará automáticamente.",
                )

            # Iniciar monitoreo
            self.monitoreo_activo = True
            self.monitoreo_btn.config(text="Detener Monitoreo")
            self.status_var.set("Monitoreo activo")
            self.log("Monitoreo iniciado", "info")

            # Iniciar thread de monitoreo
            self.thread_monitoreo = threading.Thread(target=self.monitoreo_loop)
            self.thread_monitoreo.daemon = True
            self.thread_monitoreo.start()

    def monitoreo_loop(self):
        """Loop de monitoreo continuo en segundo plano."""
        while self.monitoreo_activo:
            try:
                # Actualizar datos y realizar predicción
                self.actualizar_datos()

                # Verificar si hay señal fuerte
                if self.prediccion_actual:
                    decision = self.prediccion_actual.get("decision")
                    if decision in ["LONG", "SHORT"]:
                        # Notificar de señal fuerte
                        self.root.bell()  # Hacer sonido

                        # Para evitar múltiples notificaciones de la misma señal
                        time.sleep(5)

                # Esperar para la próxima actualización (basado en el intervalo)
                intervalo_min = (
                    int(self.intervalo_var.get())
                    if self.intervalo_var.get().isdigit()
                    else 15
                )
                # Esperar 1/3 del intervalo (mínimo 10 segundos)
                wait_seconds = max(intervalo_min * 20, 10)

                for _ in range(wait_seconds):
                    if not self.monitoreo_activo:
                        break
                    time.sleep(1)
            except Exception as e:
                self.log(f"Error en loop de monitoreo: {str(e)}", "error")
                time.sleep(30)  # Esperar antes de reintentar en caso de error

    def actualizar_grafico_avanzado(self):
        """Actualiza el gráfico avanzado con más indicadores."""
        if self.df_actual is None or self.df_indicadores is None:
            messagebox.showwarning("Advertencia", "No hay datos para mostrar")
            return

        try:
            # Limpiar figura
            self.fig_avanzado.clear()

            # Crear subplot principal para precios
            gs = self.fig_avanzado.add_gridspec(3, 1, height_ratios=[3, 1, 1])
            ax_precios = self.fig_avanzado.add_subplot(gs[0])
            ax_vol = self.fig_avanzado.add_subplot(gs[1], sharex=ax_precios)
            ax_ind = self.fig_avanzado.add_subplot(gs[2], sharex=ax_precios)

            # Dibujar velas
            for i in range(len(self.df_actual)):
                # Color verde si cierre > apertura, rojo si cierre < apertura
                if self.df_actual.iloc[i]["close"] >= self.df_actual.iloc[i]["open"]:
                    color = COLORES["verde"]
                else:
                    color = COLORES["rojo"]

                # Línea de máximo a mínimo
                ax_precios.plot(
                    [
                        self.df_actual.iloc[i]["datetime"],
                        self.df_actual.iloc[i]["datetime"],
                    ],
                    [self.df_actual.iloc[i]["low"], self.df_actual.iloc[i]["high"]],
                    color=color,
                    linewidth=1,
                )

                # Rectángulo de apertura a cierre
                ax_precios.plot(
                    [
                        self.df_actual.iloc[i]["datetime"],
                        self.df_actual.iloc[i]["datetime"],
                    ],
                    [self.df_actual.iloc[i]["open"], self.df_actual.iloc[i]["close"]],
                    color=color,
                    linewidth=5,
                )

            # Añadir medias móviles si la opción está activada
            if self.show_ma.get():
                if "ma7" in self.df_indicadores.columns:
                    ax_precios.plot(
                        self.df_indicadores["datetime"],
                        self.df_indicadores["ma7"],
                        color=COLORES["verde"],
                        linewidth=1,
                        alpha=0.8,
                        label="MA7",
                    )
                if "ma21" in self.df_indicadores.columns:
                    ax_precios.plot(
                        self.df_indicadores["datetime"],
                        self.df_indicadores["ma21"],
                        color=COLORES["rojo"],
                        linewidth=1,
                        alpha=0.8,
                        label="MA21",
                    )
                if "ma50" in self.df_indicadores.columns:
                    ax_precios.plot(
                        self.df_indicadores["datetime"],
                        self.df_indicadores["ma50"],
                        color=COLORES["azul"],
                        linewidth=1,
                        alpha=0.5,
                        label="MA50",
                    )

            # Añadir bandas de Bollinger si la opción está activada
            if self.show_bb.get() and all(
                col in self.df_indicadores.columns for col in ["bb_upper", "bb_lower"]
            ):
                ax_precios.plot(
                    self.df_indicadores["datetime"],
                    self.df_indicadores["bb_upper"],
                    color=COLORES["gris"],
                    linestyle="--",
                    linewidth=1,
                    alpha=0.6,
                )
                ax_precios.plot(
                    self.df_indicadores["datetime"],
                    self.df_indicadores["bb_lower"],
                    color=COLORES["gris"],
                    linestyle="--",
                    linewidth=1,
                    alpha=0.6,
                )

            # Añadir señales si la opción está activada
            if self.show_signals.get():
                if "target_long" in self.df_indicadores.columns:
                    # Señales de compra (long)
                    indices_compra = self.df_indicadores.index[
                        self.df_indicadores["target_long"] == 1
                    ]
                    if len(indices_compra) > 0:
                        fechas_compra = self.df_indicadores.loc[
                            indices_compra, "datetime"
                        ]
                        precios_compra = (
                            self.df_indicadores.loc[indices_compra, "low"] * 0.998
                        )
                        ax_precios.scatter(
                            fechas_compra,
                            precios_compra,
                            marker="^",
                            s=60,
                            color=COLORES["verde"],
                            alpha=0.7,
                            label="Long Signal",
                        )

                if "target_short" in self.df_indicadores.columns:
                    # Señales de venta (short)
                    indices_venta = self.df_indicadores.index[
                        self.df_indicadores["target_short"] == 1
                    ]
                    if len(indices_venta) > 0:
                        fechas_venta = self.df_indicadores.loc[
                            indices_venta, "datetime"
                        ]
                        precios_venta = (
                            self.df_indicadores.loc[indices_venta, "high"] * 1.002
                        )
                        ax_precios.scatter(
                            fechas_venta,
                            precios_venta,
                            marker="v",
                            s=60,
                            color=COLORES["rojo"],
                            alpha=0.7,
                            label="Short Signal",
                        )

            # Añadir predicción futura
            prediccion_futura = self.analizador.generar_datos_prediccion_futura(
                self.df_actual
            )
            if prediccion_futura:
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

            # Dibujar volumen
            for i in range(len(self.df_actual)):
                if self.df_actual.iloc[i]["close"] >= self.df_actual.iloc[i]["open"]:
                    color = COLORES["verde_claro"]
                else:
                    color = COLORES["rojo_claro"]
                ax_vol.bar(
                    self.df_actual.iloc[i]["datetime"],
                    self.df_actual.iloc[i]["volume"],
                    color=color,
                    alpha=0.7,
                    width=0.7,
                )

            # Dibujar indicadores en el panel inferior
            if "rsi" in self.df_indicadores.columns:
                ax_ind.plot(
                    self.df_indicadores["datetime"],
                    self.df_indicadores["rsi"],
                    color=COLORES["morado"],
                    label="RSI",
                )
                # Líneas de sobrecompra/sobreventa
                ax_ind.axhline(y=70, color=COLORES["rojo"], linestyle="--", alpha=0.5)
                ax_ind.axhline(y=30, color=COLORES["verde"], linestyle="--", alpha=0.5)
                ax_ind.set_ylim(0, 100)

            # Configuración de gráficos
            ax_precios.set_title(f"{self.symbol_var.get()} - Análisis Técnico")
            ax_precios.grid(True, alpha=0.3)
            ax_precios.legend(loc="upper left")

            ax_vol.set_ylabel("Volumen")
            ax_vol.grid(True, alpha=0.3)

            ax_ind.set_ylabel("RSI")
            ax_ind.grid(True, alpha=0.3)
            ax_ind.set_xlabel("Fecha")

            # Formatear eje x para fechas
            import matplotlib.dates as mdates

            ax_precios.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m %H:%M"))
            plt.setp(ax_ind.get_xticklabels(), rotation=45, ha="right")

            self.fig_avanzado.tight_layout()
            self.canvas_avanzado.draw()

        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al actualizar gráfico avanzado: {str(e)}"
            )
            self.log(f"Error en gráfico avanzado: {str(e)}", "error")

    def actualizar_mapa_correlacion(self):
        """Actualiza el mapa de calor de correlación."""
        if self.df_indicadores is None:
            messagebox.showwarning("Advertencia", "No hay datos para mostrar")
            return

        try:
            # Generar matriz de correlación
            corr_matrix = self.analizador.generar_heatmap_data(self.df_indicadores)

            if corr_matrix is not None:
                # Actualizar visualización
                self.fig_mapa_calor = self.visualizador.crear_mapa_calor(
                    self.fig_mapa_calor, corr_matrix
                )
                self.canvas_mapa_calor.draw()

                self.log("Mapa de correlación actualizado", "info")
            else:
                self.log("No se pudo generar matriz de correlación", "warning")
        except Exception as e:
            self.log(f"Error al actualizar mapa de correlación: {str(e)}", "error")

    def actualizar_mapa_dinamico(self):
        """Actualiza el mapa de calor dinámico."""
        if self.df_indicadores is None:
            messagebox.showwarning("Advertencia", "No hay datos para mostrar")
            return

        try:
            # Generar datos para mapa de calor dinámico
            heatmap_df = self.analizador.generar_mapa_calor_señales(self.df_indicadores)

            if heatmap_df is not None:
                # Número de periodos a mostrar
                periodos = int(self.periodos_var.get())

                # Actualizar visualización
                self.fig_mapa_dinamico = self.visualizador.crear_mapa_calor_dinamico(
                    self.fig_mapa_dinamico, heatmap_df, periodos
                )
                self.canvas_mapa_dinamico.draw()

                self.log(
                    f"Mapa de calor dinámico actualizado ({periodos} periodos)", "info"
                )
            else:
                self.log("No se pudo generar datos para mapa de calor", "warning")
        except Exception as e:
            self.log(f"Error al actualizar mapa de calor dinámico: {str(e)}", "error")

    def log(self, mensaje, tipo="info"):
        """Añade un mensaje al área de log."""
        # Obtener hora actual
        hora = datetime.now().strftime("%H:%M:%S")
        mensaje_log = f"[{hora}] {mensaje}\n"

        # Habilitar edición del área de log
        self.log_text.config(state=tk.NORMAL)

        # Insertar mensaje con el tipo/color adecuado
        self.log_text.insert(tk.END, mensaje_log, tipo)

        # Auto-scroll al final
        self.log_text.see(tk.END)

        # Deshabilitar edición del área de log
        self.log_text.config(state=tk.DISABLED)

    def limpiar_log(self):
        """Limpia el área de log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log("Log limpiado", "info")


# Función principal
def main():
    """Punto de entrada principal de la aplicación."""
    root = tk.Tk()
    app = AplicacionPredictor(root)  # noqa: F841
    root.mainloop()


if __name__ == "__main__":
    main()
