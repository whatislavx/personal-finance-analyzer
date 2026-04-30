import { ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip, Line } from 'recharts';

export interface TrendPoint {
    key: string;
    label: string;
    income: number;
    expense: number;
    net: number;
}

export function LineChartAnalysis({ data }: { data: TrendPoint[] }) {
    const formatAxisMoney = (value: number) => {
        const absoluteValue = Math.abs(value);
        if (absoluteValue >= 1000) {
            return `$${(value / 1000).toFixed(1)}k`;
        }
        return `$${value.toFixed(0)}`;
    };

    return (
        <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data} margin={{ top: 6, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="label" stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis
                    stroke="#64748b"
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={formatAxisMoney}
                />
                <Tooltip
                    contentStyle={{
                        backgroundColor: '#0f172a',
                        border: '1px solid #334155',
                        borderRadius: '0.75rem',
                        color: '#e2e8f0',
                    }}
                    formatter={(value: number, name: string) => [
                        `$${Number(value).toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
                        name === 'income' ? 'Income' : name === 'expense' ? 'Expense' : 'Net',
                    ]}
                />
                <Line type="monotone" dataKey="income" stroke="#10b981" strokeWidth={3} dot={{ r: 3 }} activeDot={{ r: 5 }} />
                <Line type="monotone" dataKey="expense" stroke="#ef4444" strokeWidth={3} dot={{ r: 3 }} activeDot={{ r: 5 }} />
                <Line type="monotone" dataKey="net" stroke="#6366f1" strokeWidth={3} strokeDasharray="6 4" dot={{ r: 3 }} activeDot={{ r: 5 }} />
            </LineChart>
        </ResponsiveContainer>
    );
}
