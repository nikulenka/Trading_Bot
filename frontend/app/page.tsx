
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
}

interface LatestSignal {
    timestamp: string;
    unum_score: number;
    close: number;
    rsi: number;
    macd: number;
    obv_trend: string;
}

export default function Dashboard() {
    const [data, setData] = useState<MarketData[]>([]);
    const [latest, setLatest] = useState<LatestSignal | null>(null);
    const [loading, setLoading] = useState(true);
    const [timeframe, setTimeframe] = useState("4h");

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


    const getSignalColor = (score: number) => {
        if (score > 0.5) return "text-green-500";
        if (score < -0.5) return "text-red-500";
        return "text-yellow-500";
    };

    const getSignalText = (score: number) => {
        if (score > 0.5) return "STRONG BUY";
        if (score > 0.2) return "BUY";
        if (score < -0.5) return "STRONG SELL";
        if (score < -0.2) return "SELL";
        return "NEUTRAL";
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

                <Card className="bg-zinc-900 border-zinc-800">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-zinc-400">RSI (14)</CardTitle>
                        <Waves className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {latest ? latest.rsi.toFixed(2) : "--"}
                        </div>
                        <p className="text-xs text-zinc-500 mt-1">Momentum</p>
                    </CardContent>
                </Card>

                <Card className="bg-zinc-900 border-zinc-800">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-zinc-400">OBV TREND</CardTitle>
                        <Activity className="h-4 w-4 text-yellow-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">
                            {latest ? latest.obv_trend : "--"}
                        </div>
                        <p className="text-xs text-zinc-500 mt-1">Volume Flow</p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-6 md:grid-cols-1">
                <Card className="bg-zinc-900 border-zinc-800 col-span-1">
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
