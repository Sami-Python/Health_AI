import { ResponsiveContainer, ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine } from 'recharts';

export default function PerformanceChart({ data }: { data: any[] }) {
    if (!data || data.length === 0) return <div className="text-slate-500 text-sm">No data available</div>;

    return (
        <div className="w-full flex flex-col gap-4">
            <div className="h-80 w-full min-h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                        <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickFormatter={(str) => str.slice(5)} />
                        <YAxis stroke="#94a3b8" fontSize={12} />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                            labelStyle={{ color: '#94a3b8' }}
                        />
                        <Legend verticalAlign="top" height={36} />

                        {/* Zero Line for TSB */}
                        <ReferenceLine y={0} stroke="#475569" />

                        {/* TSB as Bars (Form) */}
                        <Bar dataKey="tsb" name="TSB (Form)" fill="#10b981" barSize={4} />

                        {/* CTL (Fitness) */}
                        <Line type="monotone" dataKey="ctl" stroke="#3b82f6" strokeWidth={2} dot={false} name="CTL (Fitness)" />

                        {/* ATL (Fatigue) */}
                        <Line type="monotone" dataKey="atl" stroke="#ec4899" strokeWidth={2} dot={false} name="ATL (Fatigue)" />

                    </ComposedChart>
                </ResponsiveContainer>
            </div>

            <div className="mt-2 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-400 border-t border-slate-800 pt-4 pb-2">
                <div>
                    <span className="font-bold text-blue-400 block mb-1">CTL (Chronic / Kunto)</span>
                    <p>Training Load (42d avg). Measures long-term fitness.</p>
                </div>
                <div>
                    <span className="font-bold text-pink-400 block mb-1">ATL (Acute / Rasitus)</span>
                    <p>Recent fatigue (7d avg). Measures short-term stress.</p>
                </div>
                <div>
                    <span className="font-bold text-emerald-400 block mb-1">TSB (Form / Vireystila)</span>
                    <p>Readiness balance. Positive = Fresh, Negative = Tired.</p>
                </div>
            </div>
        </div>
    );
}
