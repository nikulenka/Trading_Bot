
"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { ArrowUp, ArrowDown, Minus, Activity, Waves, BarChart3 } from "lucide-react";

interface MarketData {
    timestamp: string;
    close: number;
    unum_score: number | null;
    RSI: number | null;
    MACD: number | null;
    market_state?: string;
}

interface LatestSignal {
    timestamp: string;
    unum_score: number;
    close: number;
    rsi: number;
    macd: number;
    obv_trend: string;
    market_state: string;
}

interface BacktestMetrics {
    total_return_pct: number;
    buy_hold_return_pct: number;
    win_rate_pct: number;
    max_drawdown_pct: number;
    sharpe_ratio: number;
    final_balance: number;
    total_trades: number;
}

export default function Dashboard() {
    const [data, setData] = useState<MarketData[]>([]);
    const [latest, setLatest] = useState<LatestSignal | null>(null);
    const [backtest, setBacktest] = useState<BacktestMetrics | null>(null);
    const [loading, setLoading] = useState(true);
    const [runningBacktest, setRunningBacktest] = useState(false);
    const [timeframe, setTimeframe] = useState("4h");

    // Tuning Parameters
    const [weights, setWeights] = useState({ trend: 0.4, vol: 0.4, mom: 0.2 });
    const [thresholds, setThresholds] = useState({ long: 0.60, short: -0.60 });
    const [risk, setRisk] = useState({ sl: 2.0, tp: 4.0, ts: 1.5, skipWeekends: true });
    const [activeSessions, setActiveSessions] = useState({ asian: true, european: true, american: true });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const resData = await fetch(`http://localhost:8001/api/v1/market-data/${timeframe}`);
                const jsonData = await resData.json();
                setData(jsonData);

                const resSignal = await fetch("http://localhost:8001/api/v1/latest-signal");
                const jsonSignal = await resSignal.json();
                setLatest(jsonSignal);
            } catch (error) {
                console.error("Failed to fetch data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 60000); // Update every minute
        return () => clearInterval(interval);
    }, [timeframe]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const resData = await fetch(`http://localhost:8001/api/v1/market-data/${timeframe}`);
                const jsonData = await resData.json();
                setData(jsonData);

                const resSignal = await fetch("http://localhost:8001/api/v1/latest-signal");
                const jsonSignal = await resSignal.json();
                setLatest(jsonSignal);
            } catch (error) {
                console.error("Failed to fetch data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 60000); // Update every minute
        return () => clearInterval(interval);
    }, [timeframe]);

    // Load state from localStorage on mount
    useEffect(() => {
        const savedWeights = localStorage.getItem("trading_weights");
        const savedThresholds = localStorage.getItem("trading_thresholds");
        const savedRisk = localStorage.getItem("trading_risk");
        const savedSessions = localStorage.getItem("trading_sessions");
        const savedBacktest = localStorage.getItem("trading_backtest_results");

        if (savedWeights) setWeights(JSON.parse(savedWeights));
        if (savedThresholds) setThresholds(JSON.parse(savedThresholds));
        if (savedRisk) setRisk(JSON.parse(savedRisk));
        if (savedSessions) setActiveSessions(JSON.parse(savedSessions));
        if (savedBacktest) setBacktest(JSON.parse(savedBacktest));
    }, []);

    // Save state to localStorage whenever it changes
    useEffect(() => {
        localStorage.setItem("trading_weights", JSON.stringify(weights));
        localStorage.setItem("trading_thresholds", JSON.stringify(thresholds));
        localStorage.setItem("trading_risk", JSON.stringify(risk));
        localStorage.setItem("trading_sessions", JSON.stringify(activeSessions));
    }, [weights, thresholds, risk, activeSessions]);

    useEffect(() => {
        if (backtest) {
            localStorage.setItem("trading_backtest_results", JSON.stringify(backtest));
        }
    }, [backtest]);

    const fetchBacktest = async () => {
        try {
            setRunningBacktest(true);
            const selectedSessions = Object.entries(activeSessions)
                .filter(([_, active]) => active)
                .map(([name]) => name)
                .join(",");

            const params = new URLSearchParams({
                trend_w: weights.trend.toString(),
                vol_w: weights.vol.toString(),
                mom_w: weights.mom.toString(),
                long_t: thresholds.long.toString(),
                short_t: thresholds.short.toString(),
                sl_pct: (risk.sl / 100).toString(),
                tp_pct: (risk.tp / 100).toString(),
                trailing_sl_pct: (risk.ts / 100).toString(),
                skip_weekends: risk.skipWeekends.toString(),
                sessions: selectedSessions
            });
            const res = await fetch(`http://localhost:8001/api/v1/backtest?${params}`);
            const json = await res.json();
            if (json.metrics) {
                setBacktest(json.metrics);
                if (json.chart_data) {
                    setData(json.chart_data);
                }
            }
        } catch (error) {
            console.error("Backtest failed:", error);
        } finally {
            setRunningBacktest(false);
        }
    };

    const runOptimizer = async () => {
        try {
            setRunningBacktest(true);
            const selectedSessions = Object.entries(activeSessions)
                .filter(([_, active]) => active)
                .map(([name]) => name)
                .join(",");

            const params = new URLSearchParams({
                sl_pct: (risk.sl / 100).toString(),
                tp_pct: (risk.tp / 100).toString(),
                trailing_sl_pct: (risk.ts / 100).toString(),
                skip_weekends: risk.skipWeekends.toString(),
                sessions: selectedSessions
            });
            const res = await fetch(`http://localhost:8001/api/v1/optimize?${params}`);
            const json = await res.json();
            if (json.best_weights) {
                const newWeights = {
                    trend: json.best_weights.trend,
                    vol: json.best_weights.volume_levels,
                    mom: json.best_weights.momentum
                };
                setWeights(newWeights);

                // After optimization, run backtest with new weights
                const paramsBt = new URLSearchParams({
                    trend_w: newWeights.trend.toString(),
                    vol_w: newWeights.vol.toString(),
                    mom_w: newWeights.mom.toString(),
                    long_t: thresholds.long.toString(),
                    short_t: thresholds.short.toString(),
                    sl_pct: (risk.sl / 100).toString(),
                    tp_pct: (risk.tp / 100).toString(),
                    trailing_sl_pct: (risk.ts / 100).toString(),
                    skip_weekends: risk.skipWeekends.toString(),
                    sessions: selectedSessions
                });
                const resBt = await fetch(`http://localhost:8001/api/v1/backtest?${paramsBt}`);
                const jsonBt = await resBt.json();
                if (jsonBt.metrics) {
                    setBacktest(jsonBt.metrics);
                }
            }
        } catch (error) {
            console.error("Optimization failed:", error);
        } finally {
            setRunningBacktest(false);
        }
    };


    const getSignalColor = (score: number) => {
        if (score > 0.5) return "text-green-500";
        if (score < -0.5) return "text-red-500";
        return "text-yellow-500";
    };

    const getSignalText = (score: number) => {
        const absScore = Math.abs(score);
        if (score > 0.6) return "STRONG BUY";
        if (score > 0.3) return "BUY";
        if (score < -0.6) return "STRONG SELL";
        if (score < -0.3) return "SELL";
        return "NEUTRAL";
    };

    const getConfidenceText = (score: number) => {
        const absScore = Math.abs(score);
        if (absScore > 0.8) return "High Confidence";
        if (absScore > 0.5) return "Moderate Confidence";
        return "Low Confidence / Noise";
    };

    if (loading && data.length === 0) {
        return <div className="flex h-screen items-center justify-center bg-black text-white">Loading market data...</div>;
    }

    return (
        <div className="min-h-screen bg-black text-white p-8 font-sans">
            <header className="mb-8 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600">
                        TRADING BOT <span className="text-xs align-top bg-zinc-800 px-2 py-1 rounded ml-2 text-zinc-400">UNUM CORE</span>
                    </h1>
                    <p className="text-zinc-500 mt-1">AI-Powered Multi-Timeframe Analysis</p>
                </div>
                <div className="flex gap-2">

                    <button
                        onClick={fetchBacktest}
                        disabled={runningBacktest}
                        className="px-4 py-2 rounded font-medium bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 transition-colors mr-4">
                        {runningBacktest ? "RUNNING..." : "RUN BACKTEST"}
                    </button>
                    <button
                        onClick={() => setTimeframe('1h')}
                        className={`px-4 py-2 rounded font-medium transition-colors ${timeframe === '1h' ? 'bg-blue-600' : 'bg-zinc-900 hover:bg-zinc-800'}`}>
                        1H
                    </button>
                    <button
                        onClick={() => setTimeframe('2h')}
                        className={`px-4 py-2 rounded font-medium transition-colors ${timeframe === '2h' ? 'bg-blue-600' : 'bg-zinc-900 hover:bg-zinc-800'}`}>
                        2H
                    </button>
                    <button
                        onClick={() => setTimeframe('4h')}
                        className={`px-4 py-2 rounded font-medium transition-colors ${timeframe === '4h' ? 'bg-blue-600' : 'bg-zinc-900 hover:bg-zinc-800'}`}>
                        4H
                    </button>
                </div>
            </header>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
                <Card className="bg-zinc-900 border-zinc-800">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-zinc-400">UNUM SCORE</CardTitle>
                        <Activity className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className={`text-2xl font-bold ${latest ? getSignalColor(latest.unum_score) : ''}`}>
                            {latest ? (latest.unum_score * 100).toFixed(0) + "%" : "--"}
                        </div>
                        <p className="text-xs text-zinc-500 mt-1">
                            {latest ? getSignalText(latest.unum_score) : "Analyzing..."}
                        </p>
                    </CardContent>
                </Card>

                <Card className="bg-zinc-900 border-zinc-800">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-zinc-400">MARKET STATE</CardTitle>
                        <Waves className="h-4 w-4 text-cyan-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white uppercase tracking-wider">
                            {latest ? latest.market_state : "--"}
                        </div>
                        <p className="text-xs text-zinc-500 mt-1">
                            {latest ? getConfidenceText(latest.unum_score) : "Detecting cycle..."}
                        </p>
                    </CardContent>
                </Card>

                <Card className="bg-zinc-900 border-zinc-800 lg:col-span-1">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-zinc-400">PRICE (USDT)</CardTitle>
                        <BarChart3 className="h-4 w-4 text-green-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {latest ? "$" + latest.close.toLocaleString() : "--"}
                        </div>
                        <p className="text-xs text-zinc-500 mt-1">Latest Close</p>
                    </CardContent>
                </Card>

                <Card className="bg-zinc-900 border-zinc-800 lg:col-span-1">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-zinc-400">Momentum Indicators</CardTitle>
                        <Waves className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="flex gap-4">
                            <div>
                                <div className="text-lg font-bold text-white">
                                    {latest ? latest.rsi.toFixed(1) : "--"}
                                </div>
                                <p className="text-[10px] text-zinc-500 uppercase">RSI</p>
                            </div>
                            <div className="border-l border-zinc-800 pl-4">
                                <div className="text-lg font-bold text-white">
                                    {latest ? latest.obv_trend : "--"}
                                </div>
                                <p className="text-[10px] text-zinc-500 uppercase">OBV</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-6 md:grid-cols-3 mb-8">
                <Card className="bg-zinc-900 border-zinc-800 md:col-span-2">
                    <CardHeader>
                        <CardTitle className="text-sm font-medium text-zinc-400">Strategy Tuning</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="grid grid-cols-3 gap-8">
                            <div className="space-y-3">
                                <div className="flex justify-between text-xs text-zinc-400">
                                    <span>Trend Weight</span>
                                    <span className="text-blue-400">{(weights.trend * 100).toFixed(0)}%</span>
                                </div>
                                <input
                                    type="range" min="0" max="1" step="0.05"
                                    value={weights.trend}
                                    onChange={(e) => setWeights({ ...weights, trend: parseFloat(e.target.value) })}
                                    className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                                />
                            </div>
                            <div className="space-y-3">
                                <div className="flex justify-between text-xs text-zinc-400">
                                    <span>Volume Weight</span>
                                    <span className="text-cyan-400">{(weights.vol * 100).toFixed(0)}%</span>
                                </div>
                                <input
                                    type="range" min="0" max="1" step="0.05"
                                    value={weights.vol}
                                    onChange={(e) => setWeights({ ...weights, vol: parseFloat(e.target.value) })}
                                    className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                                />
                            </div>
                            <div className="space-y-3">
                                <div className="flex justify-between text-xs text-zinc-400">
                                    <span>Momentum Weight</span>
                                    <span className="text-purple-400">{(weights.mom * 100).toFixed(0)}%</span>
                                </div>
                                <input
                                    type="range" min="0" max="1" step="0.05"
                                    value={weights.mom}
                                    onChange={(e) => setWeights({ ...weights, mom: parseFloat(e.target.value) })}
                                    className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-8 pt-4 border-t border-zinc-800">
                            <div className="space-y-3">
                                <div className="flex justify-between text-xs text-zinc-400">
                                    <span>Buy Threshold</span>
                                    <span className="text-green-500">{thresholds.long.toFixed(2)}</span>
                                </div>
                                <input
                                    type="range" min="0" max="1" step="0.05"
                                    value={thresholds.long}
                                    onChange={(e) => setThresholds({ ...thresholds, long: parseFloat(e.target.value) })}
                                    className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-green-500"
                                />
                            </div>
                            <div className="space-y-3">
                                <div className="flex justify-between text-xs text-zinc-400">
                                    <span>Sell Threshold</span>
                                    <span className="text-red-500">{thresholds.short.toFixed(2)}</span>
                                </div>
                                <input
                                    type="range" min="-1" max="0" step="0.05"
                                    value={thresholds.short}
                                    onChange={(e) => setThresholds({ ...thresholds, short: parseFloat(e.target.value) })}
                                    className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-red-500"
                                />
                            </div>
                        </div>

                        <div className="space-y-4 pt-6 border-t border-zinc-800">
                            <h3 className="text-sm font-semibold text-zinc-300">Risk Management</h3>
                            <div className="grid grid-cols-2 gap-8">
                                <div className="space-y-3">
                                    <div className="flex justify-between text-xs text-zinc-400">
                                        <span>Stop Loss (%)</span>
                                        <span className="text-red-400">{risk.sl}%</span>
                                    </div>
                                    <input
                                        type="range" min="0.5" max="10" step="0.5"
                                        value={risk.sl}
                                        onChange={(e) => setRisk({ ...risk, sl: parseFloat(e.target.value) })}
                                        className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-red-500"
                                    />
                                </div>
                                <div className="space-y-3">
                                    <div className="flex justify-between text-xs text-zinc-400">
                                        <span>Take Profit (%)</span>
                                        <span className="text-green-400">{risk.tp}%</span>
                                    </div>
                                    <input
                                        type="range" min="1" max="20" step="0.5"
                                        value={risk.tp}
                                        onChange={(e) => setRisk({ ...risk, tp: parseFloat(e.target.value) })}
                                        className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-green-500"
                                    />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-8 items-end">
                                <div className="space-y-3">
                                    <div className="flex justify-between text-xs text-zinc-400">
                                        <span>Trailing Stop (%)</span>
                                        <span className="text-blue-400">{risk.ts}%</span>
                                    </div>
                                    <input
                                        type="range" min="0.5" max="5" step="0.1"
                                        value={risk.ts}
                                        onChange={(e) => setRisk({ ...risk, ts: parseFloat(e.target.value) })}
                                        className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                                    />
                                </div>
                                <div className="flex items-center justify-between pb-1">
                                    <span className="text-xs text-zinc-400">Exclude Weekends</span>
                                    <input
                                        type="checkbox"
                                        checked={risk.skipWeekends}
                                        onChange={(e) => setRisk({ ...risk, skipWeekends: e.target.checked })}
                                        className="w-4 h-4 rounded border-zinc-700 bg-zinc-800 accent-blue-500"
                                    />
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-zinc-900 border-zinc-800 flex flex-col justify-center items-center p-6 text-center">
                    <h3 className="text-zinc-400 text-sm mb-4">Auto-Optimize</h3>
                    <p className="text-xs text-zinc-600 mb-6 px-4">Find mathematically best weights for current market</p>
                    <button
                        onClick={runOptimizer}
                        disabled={runningBacktest}
                        className="w-full py-4 mb-4 rounded-xl font-bold bg-purple-600 hover:bg-purple-500 disabled:opacity-50 transition-all border border-purple-400/20">
                        {runningBacktest ? "OPTIMIZING..." : "AUTO-OPTIMIZE"}
                    </button>
                    <button
                        onClick={fetchBacktest}
                        disabled={runningBacktest}
                        className="w-full py-4 rounded-xl font-bold bg-blue-600 hover:bg-blue-500 disabled:opacity-50 transition-all">
                        {runningBacktest ? "CALCULATING..." : "APPLY & RE-TEST"}
                    </button>
                </Card>
            </div>

            {backtest && (
                <div className="mt-8">
                    <h2 className="text-xl font-bold text-zinc-200 mb-4">Historical Performance (BTCUSDT 4H)</h2>
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        <Card className="bg-zinc-900 border-zinc-800">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-zinc-400">Total ROI</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className={`text-2xl font-bold ${backtest.total_return_pct > 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {backtest.total_return_pct > 0 ? '+' : ''}{backtest.total_return_pct}%
                                </div>
                                <p className="text-xs text-zinc-500 mt-1">vs Buy & Hold: {backtest.buy_hold_return_pct}%</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-zinc-900 border-zinc-800">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-zinc-400">Win Rate</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-white">{backtest.win_rate_pct}%</div>
                                <p className="text-xs text-zinc-500 mt-1">Total Trades: {backtest.total_trades}</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-zinc-900 border-zinc-800">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-zinc-400">Max Drawdown</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold text-red-400">{backtest.max_drawdown_pct}%</div>
                                <p className="text-xs text-zinc-500 mt-1">Sharpe: {backtest.sharpe_ratio}</p>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            )}

            <div className="grid gap-6 md:grid-cols-3 mt-8">
                <Card className="bg-zinc-900 border-zinc-800 md:col-span-1">
                    <CardHeader>
                        <CardTitle className="text-sm font-medium text-zinc-400">Session Filters</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-xs text-zinc-400">Asian (00:00 - 09:00 UTC)</span>
                            <input
                                type="checkbox"
                                checked={activeSessions.asian}
                                onChange={(e) => setActiveSessions({ ...activeSessions, asian: e.target.checked })}
                                className="w-4 h-4 rounded border-zinc-700 bg-zinc-800 accent-blue-500"
                            />
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-xs text-zinc-400">European (07:00 - 16:00 UTC)</span>
                            <input
                                type="checkbox"
                                checked={activeSessions.european}
                                onChange={(e) => setActiveSessions({ ...activeSessions, european: e.target.checked })}
                                className="w-4 h-4 rounded border-zinc-700 bg-zinc-800 accent-blue-500"
                            />
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-xs text-zinc-400">American (13:00 - 22:00 UTC)</span>
                            <input
                                type="checkbox"
                                checked={activeSessions.american}
                                onChange={(e) => setActiveSessions({ ...activeSessions, american: e.target.checked })}
                                className="w-4 h-4 rounded border-zinc-700 bg-zinc-800 accent-blue-500"
                            />
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-zinc-900 border-zinc-800 md:col-span-2">
                    <CardHeader>
                        <CardTitle className="text-zinc-200">Price & Signal History ({timeframe})</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[400px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                <XAxis
                                    dataKey="timestamp"
                                    hide
                                />
                                <YAxis yAxisId="left" stroke="#888" domain={['auto', 'auto']} />
                                <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" domain={[-1.2, 1.2]} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#111', border: '1px solid #333' }}
                                    itemStyle={{ color: '#ccc' }}
                                    labelFormatter={(label) => new Date(label).toLocaleString()}
                                />
                                <ReferenceLine yAxisId="right" y={0} stroke="#666" strokeDasharray="3 3" />
                                <Line yAxisId="left" type="monotone" dataKey="close" stroke="#3b82f6" dot={false} strokeWidth={2} name="Price" />
                                <Line yAxisId="right" type="step" dataKey="unum_score" stroke="#10b981" dot={false} strokeWidth={2} name="Unum Score" />
                            </LineChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
