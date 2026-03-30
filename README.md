# PyPrediccionBybit 🚀

Machine Learning-based market prediction system for Bybit - **Completely Free**

---

## 🎯 Description

PyPrediccionBybit is an algorithmic trading system that combines:

- ✅ **Advanced technical analysis** with custom indicators
- ✅ **Real-time order book analysis**
- ✅ **Anti-spoofing system** to detect manipulation
- ✅ **Machine Learning (Gradient Boosting)** for prediction
- ✅ **Custom TradingView indicator** implemented in Python

**Focus:** Futures trading with entries of **0.30% - 1%** in both LONG and SHORT.

---

## 📋 Requirements

- **Python 3.12+** (required for tkinter compatibility on macOS)
- **Operating System:** Windows, Linux, or macOS
- **Virtual Environment:** Isolated for each installation

---

## 🛠️ Installation

### 🪟 Windows

#### 1. Install Python 3.12

Download from: [python.org/downloads](https://www.python.org/downloads/)

✅ Make sure to check: **"Add Python to PATH"** during installation

#### 2. Create Virtual Environment

```cmd
cd PyPrediccionBybit
python3.12 -m venv .venv
.venv\Scripts\activate
```

#### 3. Verify Installation

```cmd
python -V
# Should show: Python 3.12.x
```

#### 4. Update pip

```cmd
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools
```

#### 5. Install Dependencies

```cmd
pip install -r requirements.txt
```

#### 6. Run Application

```cmd
python app_principal.py
```

---

### 🐧 Linux / 🍎 macOS

#### 1. Install Python 3.12

**macOS:**
```bash
brew install python@3.12
brew install python-tk@3.12
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-tk
```

**Fedora:**
```bash
sudo dnf install python3.12 python3.12-tkinter
```

#### 2. Create Virtual Environment

```bash
cd PyPrediccionBybit
python3.12 -m venv .venv
source .venv/bin/activate
```

#### 3. Verify Installation

```bash
python -V
# Should show: Python 3.12.x
```

#### 4. Update pip

```bash
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools
```

#### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 6. Run Application

```bash
python app_principal.py
```

---

## 📦 Required Libraries

Dependencies are automatically installed with `requirements.txt`:

```bash
pip install -r requirements.txt
```

**Includes:**
- `matplotlib` - Graphs and visualizations
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `seaborn` - Statistical visualizations
- `requests` - Bybit API connection
- `pytz` - Timezone handling
- `scikit-learn` - Machine Learning (Gradient Boosting)

---

## 🚀 Quick Start Guide

### Step 1: Run the Application

```bash
python app_principal.py
```

---

### Step 2: Configure Bybit API

1. **Go to the "Configuración" tab** in the GUI

2. **Add API Key:**
   - Enter your Bybit **API Key**
   - Enter your Bybit **API Secret**

3. **Press "Guardar Configuración"**
   - ✅ Configuration is saved permanently
   - 📁 Location: `~/.pyprediccion/config.json`
   - 🔒 You don't need to re-enter credentials

---

### Step 3: Train Models

1. **Go to the "Trading" tab**

2. **Press "Entrenar Modelos"**
   - ⏱️ Estimated time: 5-10 seconds
   - 📊 System trains Gradient Boosting models
   - ✅ You'll see: "Modelos entrenados. Long acc: XX%, Short acc: XX%"

---

### Step 4: Update Pairs

1. **Press "Actualizar Pares"**
   - 🔄 Loads list of available pairs on Bybit
   - 📈 Shows: "Lista de pares actualizada, XX pares disponibles"

---

### Step 5: Start Monitoring

1. **Press "Iniciar Monitoreo"**
   - ▶️ System starts analyzing market in real-time
   - 📊 Updates data every few seconds
   - 🎯 Shows LONG/SHORT predictions with probabilities
   - 🔔 Alerts when opportunities are detected

---

## 📊 System Features

| Feature | Description |
|---------|-------------|
| **Anti-Spoofing** | Detects and filters order book manipulation |
| **Order Book Analysis** | Processes orderbook in real-time |
| **Custom Indicator** | Python implementation of TradingView indicator |
| **Machine Learning** | Gradient Boosting Classifier for LONG/SHORT prediction |
| **Multi-Timeframe** | Support for multiple intervals (1m, 5m, 15m, 30m, 1h, 4h) |
| **Persistent Configuration** | Saves API keys and preferences automatically |

---

## 🎓 Success Rate

The system is designed for:

- 🎯 **Secured entries:** 0.30% - 1% movement
- 📈 **Directionality:** Works in both uptrend (LONG) and downtrend (SHORT)
- ⚡ **Focus:** Futures trading
- 🤖 **Automation:** Continuous monitoring without manual intervention

---

## 📁 Project Structure

```
PyPrediccionBybit/
├── app_principal.py        # Main application (GUI)
├── bybit_api.py            # Bybit API connection
├── analizador_datos.py     # Data analysis and indicators
├── visualizaciones.py      # Graphs and visualizations
├── test_qa.py              # Automated QA tests
├── requirements.txt        # Python dependencies
├── utils/
│   └── config_manager.py   # Persistent configuration manager
└── local_work/             # Local documentation and work
    ├── plan_config_persistente.md
    └── problemas_encontrados.md
```

---

## ⚙️ Manual Configuration (Optional)

You can manually edit the configuration at:

```bash
# Linux/macOS:
nano ~/.pyprediccion/config.json

# Windows:
notepad %USERPROFILE%\.pyprediccion\config.json
```

### Example config.json:

```json
{
    "SYMBOL": "BTCUSDT,ETHUSDT,DOGEUSDT",
    "INTERVAL": "15",
    "PROBABILITY_THRESHOLD": 0.65,
    "DARK_MODE": true,
    "BYBIT_API_KEY": "YOUR_API_KEY",
    "BYBIT_API_SECRET": "YOUR_API_SECRET"
}
```

---

## 🧪 QA Tests

The project includes automated tests to verify functionality:

```bash
python test_qa.py
```

**Included tests:**
- ✅ Timestamp conversion
- ✅ String to numeric conversion
- ✅ Technical indicator calculation
- ✅ Model training
- ✅ Prediction generation
- ✅ Visualization creation
- ✅ Math operations with strings
- ✅ Timestamp overflow handling

---

## 🔒 Security

- 🔐 **API Keys:** Saved encrypted in `~/.pyprediccion/config.json`
- 🚫 **Not shared:** Credentials only sent to Bybit
- 👁️ **Masked:** API Secret shown as `****` in UI
- 📁 **Permissions:** Recommended `chmod 600` on Linux/macOS

---

## 🛠️ Troubleshooting

### Error: "No module 'matplotlib'"

```bash
pip install matplotlib pandas numpy seaborn
```

### Error: "Invalid API Key"

1. Verify credentials are correct in Bybit
2. Make sure you have **Read** permissions on the API
3. Save configuration again

### Error: "No data available"

1. Check your internet connection
2. Make sure the trading pair exists on Bybit
3. Press "Actualizar Pares" again

### Application closes immediately

1. Open terminal and run: `python app_principal.py`
2. Check error messages in console
3. Review console logs for more details

---

## 🔄 Upcoming Updates

- [ ] **Binance** support
- [ ] More technical indicators
- [ ] Integrated backtesting
- [ ] Export signals to Telegram
- [ ] Historical backtest mode

---

## 📄 License

MIT License - Free to use.

---

## 🙏 Credits and Authorship

### 👨‍💻 Original Author

This project was originally created by **bitcoinalexis**:

- **Original Repository:** [github.com/bitcoinalexis/PyPrediccionBybit](https://github.com/bitcoinalexis/PyPrediccionBybit)
- **Explanatory Video:** [YouTube - Prediction Indicator](https://www.youtube.com/watch?v=163yPGgNvqQ)

### 🔧 Current Maintainer / Fork

This is a fork maintained and improved by **comgunner**:

- **Fork Repository:** [github.com/comgunner/PyPrediccion](https://github.com/comgunner/PyPrediccion)
- **Implemented Improvements:**
  - ✅ Persistent configuration (`~/.pyprediccion/config.json`)
  - ✅ Multi-platform support (Windows, Linux, macOS)
  - ✅ Automated QA tests
  - ✅ Complete documentation
  - ✅ Stability and performance improvements

### 📄 License

MIT License - Free to use.

---

## ⚠️ Disclaimer

**This software is for educational purposes only.** Cryptocurrency trading carries significant risks. Trade responsibly and never risk more than you can afford to lose.

**I am not a financial advisor.** This software does not provide investment advice. All trading decisions are your own responsibility.

---

*Last updated: March 29, 2026*
