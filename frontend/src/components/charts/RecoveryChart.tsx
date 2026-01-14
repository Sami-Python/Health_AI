import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from 'recharts';

export default function RecoveryChart({ data }: { data: any[] }) {
    if (!data || data.length === 0) return <div className="text-slate-500 text-sm">No data available</div>;

    return (
        <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                        <linearGradient id="colorReadiness" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorSleep" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickFormatter={(str) => str.slice(5)} />
                    <YAxis stroke="#94a3b8" fontSize={12} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                        itemStyle={{ color: '#f8fafc' }}
                    />
                    <Area type="monotone" dataKey="readiness" stroke="#10b981" fillOpacity={1} fill="url(#colorReadiness)" name="Body Battery" />
                    <Area type="monotone" dataKey="sleep_min" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorSleep)" name="Sleep (min)" />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
