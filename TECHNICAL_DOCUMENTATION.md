# Техническая Документация: Торговый Бот BTC/USDT

## Оглавление
1. [Общая Архитектура](#общая-архитектура)
2. [Источники Данных](#источники-данных)
3. [Технические Индикаторы](#технические-индикаторы)
4. [Система UNUM Score](#система-unum-score)
5. [Бэктестинг и Управление Рисками](#бэктестинг-и-управление-рисками)
6. [Анализ Торговых Сессий](#анализ-торговых-сессий)
7. [API и Веб-Интерфейс](#api-и-веб-интерфейс)

---

## Общая Архитектура

Торговый бот представляет собой полнофункциональную систему технического анализа и бэктестинга для пары BTC/USDT. Система состоит из трех основных компонентов:

### Backend (Python + FastAPI)
- **Indicators** (`backend/src/core/indicators.py`) - расчет технических индикаторов
- **SignalAggregator** (`backend/src/core/strategy.py`) - агрегация сигналов и расчет UNUM Score
- **Backtester** (`backend/src/core/backtest.py`) - симуляция торговли с управлением рисками
- **API** (`backend/src/api/market.py`) - REST API endpoints

### Frontend (Next.js + React)
- Интерактивный дашборд с графиками и метриками
- Настройка параметров стратегии в реальном времени
- Визуализация результатов бэктестинга

### Data Layer
- Исторические данные с Binance (CSV формат)
- Таймфреймы: 1h, 2h, 4h
- Период: 4-8 лет исторических данных

---

## Источники Данных

### Формат Данных
Данные хранятся в CSV файлах в директории `backend/data/`:
- `BTCUSDT_1h.csv` - часовые свечи
- `BTCUSDT_2h.csv` - двухчасовые свечи
- `BTCUSDT_4h.csv` - четырехчасовые свечи (основной таймфрейм)

### Структура CSV
```
timestamp,open,high,low,close,volume
2017-08-17 04:00:00,4261.48,4485.39,4200.74,4285.08,795.150377
```

### Загрузка Данных
Данные загружаются через скрипт `backend/fetch_data.py` с использованием библиотеки `ccxt`:
```python
exchange = ccxt.binance()
ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='4h', since=start_timestamp)
```

---

## Технические Индикаторы

Система рассчитывает **17 различных индикаторов**, разделенных на категории:

### 1. Трендовые Индикаторы

#### Moving Averages (SMA/EMA)
- **Периоды**: 20, 50, 200
- **Библиотека**: `ta` (Technical Analysis Library)
- **Назначение**: Определение направления тренда

```python
self.df[f'SMA_{p}'] = ta_lib.trend.SMAIndicator(close=self.df['close'], window=p).sma_indicator()
self.df[f'EMA_{p}'] = ta_lib.trend.EMAIndicator(close=self.df['close'], window=p).ema_indicator()
```

#### MACD (Moving Average Convergence Divergence)
- **Параметры**: fast=12, slow=26, signal=9
- **Компоненты**: MACD Line, Signal Line, Histogram
- **Сигнал**: Пересечение MACD и сигнальной линии

```python
macd = ta_lib.trend.MACD(close=self.df['close'], window_slow=26, window_fast=12, window_sign=9)
self.df['MACD'] = macd.macd()
self.df['MACD_Signal'] = macd.macd_signal()
self.df['MACD_Hist'] = macd.macd_diff()
```

#### Aroon Indicator
- **Период**: 25
- **Компоненты**: Aroon Up, Aroon Down, Aroon Indicator
- **Сигнал**: Aroon Up > 70 → бычий тренд, Aroon Down > 70 → медвежий тренд

#### ADX (Average Directional Index)
- **Период**: 14
- **Назначение**: Измерение силы тренда
- **Интерпретация**: ADX > 25 → сильный тренд, ADX < 20 → слабый тренд/флэт

### 2. Индикаторы Импульса (Momentum)

#### RSI (Relative Strength Index)
- **Период**: 14
- **Диапазон**: 0-100
- **Сигналы**: 
  - RSI > 70 → перекупленность
  - RSI < 30 → перепроданность
  - RSI 40-60 → нейтральная зона

#### Stochastic Oscillator
- **Параметры**: K=14, D=3
- **Диапазон**: 0-100
- **Сигнал**: Пересечение %K и %D в зонах перекупленности/перепроданности

#### CCI (Commodity Channel Index)
- **Период**: 20
- **Диапазон**: обычно от -100 до +100
- **Сигналы**: CCI > +100 → сильный бычий импульс, CCI < -100 → сильный медвежий импульс

### 3. Индикаторы Волатильности

#### ATR (Average True Range)
- **Период**: 14
- **Назначение**: Измерение волатильности рынка
- **Использование**: Нормализация сигналов и определение размеров стоп-лоссов

#### Bollinger Bands
- **Параметры**: period=20, std_dev=2
- **Компоненты**: Upper Band, Middle Band (SMA), Lower Band
- **Сигнал**: Цена у границ полос → возможный разворот

#### Keltner Channels
- **Параметры**: period=20, atr_period=10
- **Назначение**: Альтернатива Bollinger Bands на основе ATR

### 4. Объемные Индикаторы

#### OBV (On-Balance Volume)
- **Расчет**: Кумулятивный объем с учетом направления цены
- **Сигнал**: Дивергенция между OBV и ценой → возможный разворот

```python
self.df['OBV'] = ta_lib.volume.OnBalanceVolumeIndicator(
    close=self.df['close'], 
    volume=self.df['volume']
).on_balance_volume()
```

#### Volume SMA
- **Период**: 20
- **Назначение**: Определение среднего объема для выявления всплесков активности

### 5. Уровни Поддержки/Сопротивления

#### Fibonacci Levels
- **Период анализа**: 100 свечей (rolling window)
- **Уровни**: 0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%
- **Расчет**: На основе максимума и минимума за период

```python
diff = self.df['Roll_Max'] - self.df['Roll_Min']
self.df['Fib_382'] = self.df['Roll_Min'] + diff * 0.382
self.df['Fib_618'] = self.df['Roll_Min'] + diff * 0.618
```

---

## Система UNUM Score

**UNUM Score** - это интегральный показатель от -1.0 до +1.0, который агрегирует сигналы всех индикаторов с учетом их весов и рыночных условий.

### Архитектура UNUM

#### 1. Категории Сигналов

Все индикаторы разделены на **3 основные категории**:

**A. Trend (Тренд)** - вес по умолчанию: 0.4
- MA Alignment (выравнивание скользящих средних)
- MACD (дивергенция/конвергенция)
- Aroon (сила тренда)

**B. Volume/Levels (Объем/Уровни)** - вес по умолчанию: 0.4
- Fibonacci Interaction (взаимодействие с уровнями Фибо)
- OBV Trend (тренд объема)
- ATR Volatility (волатильность)

**C. Momentum (Импульс)** - вес по умолчанию: 0.2
- RSI (индекс относительной силы)
- Stochastic (стохастический осциллятор)
- CCI (индекс товарного канала)

#### 2. Расчет Индивидуальных Сигналов

Каждый индикатор генерирует сигнал в диапазоне **-1.0 (сильный SHORT) до +1.0 (сильный LONG)**:

**Пример: MA Alignment**
```python
def _calc_ma_signal(self):
    # Сравнение EMA20 и EMA50
    self.df['sig_ma'] = np.where(
        self.df['EMA_20'] > self.df['EMA_50'], 1, -1
    )
```

**Пример: RSI Signal**
```python
def _calc_rsi_signal(self):
    rsi = self.df['RSI']
    self.df['sig_rsi'] = np.where(
        rsi < 30, 1,          # Перепроданность → LONG
        np.where(rsi > 70, -1, 0)  # Перекупленность → SHORT
    )
```

**Пример: Fibonacci Interaction**
```python
def _calc_fib_signal(self):
    close = self.df['close']
    tolerance = 0.02  # 2% допуск
    
    # Проверка близости к ключевым уровням
    near_382 = (close - self.df['Fib_382']).abs() / close < tolerance
    near_618 = (close - self.df['Fib_618']).abs() / close < tolerance
    
    # Сигнал зависит от направления подхода к уровню
    self.df['sig_fib'] = np.where(near_618 & (close > self.df['Fib_618']), 1, 
                         np.where(near_382 & (close < self.df['Fib_382']), -1, 0))
```

#### 3. Взвешенная Агрегация

Сигналы каждой категории суммируются с учетом **внутренних весов** (sub_weights):

```python
# Trend Score
trend_score = (
    self.df['sig_ma'] * 0.5 +      # MA Alignment: 50%
    self.df['sig_macd'] * 0.3 +    # MACD: 30%
    self.df['sig_aroon'] * 0.2     # Aroon: 20%
)

# Volume/Levels Score
vol_score = (
    self.df['sig_fib'] * 0.4 +     # Fibonacci: 40%
    self.df['sig_obv'] * 0.3 +     # OBV: 30%
    self.df['sig_atr'] * 0.3       # ATR: 30%
)

# Momentum Score
mom_score = (
    self.df['sig_rsi'] * 0.4 +     # RSI: 40%
    self.df['sig_stoch'] * 0.3 +   # Stochastic: 30%
    self.df['sig_cci'] * 0.3       # CCI: 30%
)
```

Затем категории объединяются с учетом **основных весов**:

```python
raw_score = (
    trend_score * 0.4 +      # Trend: 40%
    vol_score * 0.4 +        # Volume/Levels: 40%
    mom_score * 0.2          # Momentum: 20%
)
```

#### 4. Фильтры Шума (Noise Reduction)

Для повышения качества сигналов применяются **4 фильтра**:

**A. ADX Filter (Сила Тренда)**
```python
adx_filter = np.where(self.df['ADX'] > 22, 1.0, 0.2)
# Если ADX < 22 → слабый тренд → сигнал ослабляется в 5 раз
```

**B. Volume Spike Confirmation (Подтверждение Объемом)**
```python
vol_spike = np.where(
    self.df['volume'] > self.df['VOL_SMA'] * 1.2,  # Объем на 20% выше среднего
    1.0,   # Полная сила сигнала
    0.5    # Половинная сила
)
```

**C. Volatility Dampener (Нормализация Волатильности)**
```python
vol_dampener = self.df['sig_atr']  # Значение от 0.3 до 1.0
# Низкая волатильность → сигнал ослабляется
```

**D. Signal Persistence (Устойчивость Сигнала)**
```python
prev_score = score_series.shift(1).fillna(0)
persistence = np.where(
    np.sign(score_series) == np.sign(prev_score),  # Сигнал не изменил направление
    1.0,   # Полная сила
    0.5    # Половинная сила (только что развернулся)
)
```

**Итоговая формула:**
```python
filtered_score = raw_score * adx_filter * vol_spike * vol_dampener * persistence
```

#### 5. Multi-Timeframe Confirmation (MTC)

Финальный этап - подтверждение сигнала на других таймфреймах:

```python
def confirm_signal_mtf(self, score_series):
    if '1h' in self.other_dfs:
        # Проверяем тренд на 1h
        df_1h = self.other_dfs['1h']
        latest_1h_trend = df_1h['EMA_20'].iloc[-1] > df_1h['EMA_50'].iloc[-1]
        
        # Усиливаем сигнал при совпадении направления
        mtf_boost = np.where(
            (score_series > 0) & latest_1h_trend, 1.2,  # LONG + бычий 1h
            np.where((score_series < 0) & ~latest_1h_trend, 1.2,  # SHORT + медвежий 1h
            1.0)  # Нет подтверждения
        )
        return score_series * mtf_boost
    return score_series
```

#### 6. Адаптация к Рыночным Условиям

Система автоматически определяет **Market State** и корректирует веса:

```python
def detect_market_state(self):
    adx = self.df['ADX'].iloc[-1]
    ma_slope = (self.df['EMA_50'].iloc[-1] - self.df['EMA_50'].iloc[-20]) / 20
    
    if adx > 25 and abs(ma_slope) > 10:
        self.state = MarketState.TRENDING
        # В тренде: увеличиваем вес трендовых индикаторов
        self.weights['trend'] = 0.5
        self.weights['momentum'] = 0.3
        self.weights['volume_levels'] = 0.2
    else:
        self.state = MarketState.RANGING
        # Во флэте: увеличиваем вес осцилляторов
        self.weights['trend'] = 0.2
        self.weights['momentum'] = 0.4
        self.weights['volume_levels'] = 0.4
```

### Итоговый UNUM Score

**Диапазон**: -1.0 (максимальный SHORT) до +1.0 (максимальный LONG)

**Интерпретация**:
- `UNUM > 0.6` → Сильный сигнал на LONG (вход в длинную позицию)
- `UNUM < -0.6` → Сильный сигнал на SHORT (вход в короткую позицию)
- `-0.6 < UNUM < 0.6` → Нейтральная зона (не торгуем)

**Пороги по умолчанию**:
- `long_threshold = 0.6`
- `short_threshold = -0.6`

---

## Бэктестинг и Управление Рисками

### Архитектура Backtester

Класс `Backtester` реализует **итеративную симуляцию** торговли (не векторизованную), что позволяет корректно обрабатывать path-dependent условия (SL/TP/Trailing Stop).

### Параметры Риск-Менеджмента

#### 1. Stop Loss (SL)
- **Параметр**: `sl_pct` (по умолчанию: 2.0%)
- **Логика**: Автоматический выход при убытке
- **LONG**: Выход, если `price <= entry_price * (1 - sl_pct)`
- **SHORT**: Выход, если `price >= entry_price * (1 + sl_pct)`

#### 2. Take Profit (TP)
- **Параметр**: `tp_pct` (по умолчанию: 4.0%)
- **Логика**: Автоматический выход при достижении цели прибыли
- **LONG**: Выход, если `price >= entry_price * (1 + tp_pct)`
- **SHORT**: Выход, если `price <= entry_price * (1 - tp_pct)`

#### 3. Trailing Stop (TS)
- **Параметр**: `trailing_sl_pct` (по умолчанию: 1.5%)
- **Логика**: Динамический стоп, следующий за ценой
- **LONG**: 
  - Отслеживаем `peak_price = max(peak_price, current_price)`
  - Выход, если `price <= peak_price * (1 - trailing_sl_pct)`
- **SHORT**: 
  - Отслеживаем `peak_price = min(peak_price, current_price)`
  - Выход, если `price >= peak_price * (1 + trailing_sl_pct)`

### Логика Входа и Выхода

```python
for i in range(1, len(df)):
    # 1. ВЫХОД (приоритет выше входа)
    if position != 0:
        if position == 1:  # LONG
            peak_price = max(peak_price, prices[i])
            if (prices[i] <= entry_price * (1 - sl_pct)) or \
               (prices[i] >= entry_price * (1 + tp_pct)) or \
               (prices[i] <= peak_price * (1 - trailing_sl_pct)):
                exit_triggered = True
        
        if exit_triggered:
            balance = curr_equity * (1 - fee)
            position = 0
            trades_count += 1
    
    # 2. ВХОД (только если нет позиции)
    if position == 0 and not weekends[i] and in_sessions[i]:
        if scores[i] > long_threshold:
            position = 1  # LONG
            entry_price = prices[i]
            peak_price = prices[i]
            balance = balance * (1 - fee)
            trades_count += 1
        elif scores[i] < short_threshold:
            position = -1  # SHORT
            entry_price = prices[i]
            peak_price = prices[i]
            balance = balance * (1 - fee)
            trades_count += 1
```

### Комиссии
- **Параметр**: `fee = 0.001` (0.1% на сделку)
- **Применение**: Вычитается при входе и выходе из позиции

### Метрики Производительности

После завершения бэктеста рассчитываются следующие метрики:

```python
def calculate_metrics(self, df, trades_count):
    # 1. Total Return (ROI стратегии)
    total_return = ((df['equity_curve'].iloc[-1] / self.initial_balance) - 1) * 100
    
    # 2. Buy & Hold Return (ROI пассивной стратегии)
    buy_hold_return = ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
    
    # 3. Win Rate (процент прибыльных сделок)
    profitable_trades = (df['strategy_returns'] > 0).sum()
    win_rate = (profitable_trades / trades_count * 100) if trades_count > 0 else 0
    
    # 4. Maximum Drawdown (максимальная просадка)
    cummax = df['equity_curve'].cummax()
    drawdown = (df['equity_curve'] - cummax) / cummax * 100
    max_drawdown = drawdown.min()
    
    # 5. Sharpe Ratio (риск-скорректированная доходность)
    returns = df['strategy_returns']
    sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
    
    return {
        "total_return_pct": round(total_return, 2),
        "buy_hold_return_pct": round(buy_hold_return, 2),
        "win_rate_pct": round(win_rate, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "sharpe_ratio": round(sharpe, 2),
        "final_balance": round(df['equity_curve'].iloc[-1], 2),
        "total_trades": int(trades_count)
    }
```

---

## Анализ Торговых Сессий

Система поддерживает фильтрацию сделок по **торговым сессиям** (UTC):

### Определение Сессий

```python
df['hour'] = df.index.hour
df['is_asian'] = (df['hour'] >= 0) & (df['hour'] < 9)      # 00:00 - 09:00 UTC
df['is_european'] = (df['hour'] >= 7) & (df['hour'] < 16)  # 07:00 - 16:00 UTC
df['is_american'] = (df['hour'] >= 13) & (df['hour'] < 22) # 13:00 - 22:00 UTC
```

### Фильтрация Входов

```python
if allowed_sessions:
    session_mask = pd.Series(False, index=df.index)
    if 'asian' in allowed_sessions: session_mask |= df['is_asian']
    if 'european' in allowed_sessions: session_mask |= df['is_european']
    if 'american' in allowed_sessions: session_mask |= df['is_american']
    df['in_session'] = session_mask
else:
    df['in_session'] = True  # Все сессии активны

# Вход только в разрешенные сессии
if position == 0 and not weekends[i] and in_sessions[i]:
    # ... логика входа
```

### Пример Использования

```python
# Торговать только в европейскую и американскую сессии
backtester.run_backtest(allowed_sessions=['european', 'american'])

# Торговать только в азиатскую сессию
backtester.run_backtest(allowed_sessions=['asian'])

# Торговать во все сессии
backtester.run_backtest(allowed_sessions=None)
```

---

## API и Веб-Интерфейс

### REST API Endpoints

#### 1. GET `/api/v1/market-data/{timeframe}`
Возвращает исторические данные с индикаторами и UNUM Score.

**Параметры**:
- `timeframe`: '1h', '2h', '4h'

**Ответ**:
```json
[
  {
    "timestamp": "2024-01-01T00:00:00",
    "close": 42000.5,
    "RSI": 55.3,
    "MACD": 120.5,
    "unum_score": 0.65,
    "market_state": "trending"
  }
]
```

#### 2. GET `/api/v1/backtest`
Запускает бэктест с кастомными параметрами.

**Параметры**:
- `trend_w`: вес категории Trend (default: 0.4)
- `vol_w`: вес категории Volume/Levels (default: 0.4)
- `mom_w`: вес категории Momentum (default: 0.2)
- `long_t`: порог для LONG (default: 0.6)
- `short_t`: порог для SHORT (default: -0.6)
- `sl_pct`: Stop Loss % (default: 0.015)
- `tp_pct`: Take Profit % (default: 0.03)
- `trailing_sl_pct`: Trailing Stop % (default: 0.015)
- `skip_weekends`: пропускать выходные (default: true)
- `sessions`: активные сессии, через запятую (example: "asian,european")

**Ответ**:
```json
{
  "metrics": {
    "total_return_pct": 35.69,
    "buy_hold_return_pct": 61.61,
    "win_rate_pct": 48.56,
    "max_drawdown_pct": -28.45,
    "sharpe_ratio": 0.82,
    "final_balance": 13569.23,
    "total_trades": 696
  },
  "chart_data": [...]
}
```

#### 3. GET `/api/v1/optimize`
Автоматическая оптимизация весов для максимизации ROI.

**Параметры**:
- `sl_pct`, `tp_pct`, `trailing_sl_pct`, `skip_weekends`, `sessions`

**Ответ**:
```json
{
  "best_weights": {
    "trend": 0.5,
    "volume_levels": 0.3,
    "momentum": 0.2
  },
  "best_roi": 42.15
}
```

### Веб-Интерфейс

Frontend предоставляет:
- **Интерактивные графики** (Recharts): цена, UNUM Score, equity curve
- **Настройка параметров**: слайдеры для весов, порогов, риск-параметров
- **Session Filters**: чекбоксы для выбора торговых сессий
- **Метрики в реальном времени**: ROI, Win Rate, Drawdown, Sharpe Ratio
- **Автооптимизация**: кнопка "AUTO-OPTIMIZE" для поиска лучших весов
- **Persistence**: все настройки сохраняются в localStorage

---

## Заключение

Торговый бот представляет собой комплексную систему технического анализа, которая:

1. **Агрегирует 17 индикаторов** в единый UNUM Score
2. **Адаптируется к рыночным условиям** (тренд/флэт)
3. **Фильтрует шум** через ADX, объем, волатильность и устойчивость сигнала
4. **Управляет рисками** через SL/TP/Trailing Stop
5. **Оптимизирует торговлю** по времени (сессии, выходные)
6. **Предоставляет полный бэктестинг** с детальными метриками

Система достигла **+35.69% ROI** на исторических данных с оптимизированными параметрами риск-менеджмента.
