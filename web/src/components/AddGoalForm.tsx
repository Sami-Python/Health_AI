"use client";

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';

interface AddGoalFormProps {
    onSuccess?: () => void;
}

export default function AddGoalForm({ onSuccess }: AddGoalFormProps) {
    const { user } = useAuth();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        activity_type: 'Running',
        target_value: '',
        target_unit: 'km',
        period_type: 'weekly', // weekly, monthly, target_date
        frequency: 'Weekly', // Keep for recurring logic
        target_date: '',
        description: ''
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        if (!user) return;

        try {
            const token = await user.getIdToken();
            const res = await fetch('http://localhost:8000/goals', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    activity_type: formData.activity_type,
                    target_value: parseFloat(formData.target_value),
                    target_unit: formData.target_unit,
                    period_type: formData.period_type,
                    frequency: formData.period_type === 'target_date' ? null : formData.frequency,
                    target_date: formData.period_type === 'target_date' ? formData.target_date : null,
                    description: formData.description
                })
            });

            if (!res.ok) throw new Error('Failed to create goal');

            // Reset form
            setFormData({
                activity_type: 'Running',
                target_value: '',
                target_unit: 'km',
                period_type: 'weekly',
                frequency: 'Weekly',
                target_date: '',
                description: ''
            });

            if (onSuccess) onSuccess();

        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const inputClass = "w-full rounded bg-slate-800 p-2 text-white border border-slate-700 focus:border-blue-500 focus:outline-none placeholder-slate-500";
    const labelClass = "block text-xs uppercase tracking-wide font-bold text-slate-500 mb-1";

    return (
        <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm backdrop-blur-sm">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">Create New Goal</h2>
            </div>

            {error && <div className="rounded bg-red-900/50 p-3 text-sm text-red-200 border border-red-800">{error}</div>}

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className={labelClass}>Activity</label>
                    <div className="relative">
                        <select
                            className={inputClass + " appearance-none"}
                            value={formData.activity_type}
                            onChange={(e) => setFormData({ ...formData, activity_type: e.target.value })}
                        >
                            <option>Running</option>
                            <option>Cycling</option>
                            <option>Swimming</option>
                            <option>Gym</option>
                            <option>Skiing</option>
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-400">
                            <svg className="h-4 w-4 fill-current" viewBox="0 0 20 20"><path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" fillRule="evenodd"></path></svg>
                        </div>
                    </div>
                </div>

                {/* Goal Type Selection */}
                <div>
                    <label className={labelClass}>Goal Type</label>
                    <div className="flex gap-2 rounded bg-slate-800 p-1">
                        <button
                            type="button"
                            className={`flex-1 rounded py-1 text-xs font-medium transition-colors ${formData.period_type !== 'target_date' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
                            onClick={() => setFormData({ ...formData, period_type: 'weekly' })}
                        >
                            Recurring
                        </button>
                        <button
                            type="button"
                            className={`flex-1 rounded py-1 text-xs font-medium transition-colors ${formData.period_type === 'target_date' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
                            onClick={() => setFormData({ ...formData, period_type: 'target_date' })}
                        >
                            Target Date
                        </button>
                    </div>
                </div>
            </div>

            {/* Dynamic Middle Section */}
            <div className="grid grid-cols-2 gap-4">
                {formData.period_type === 'target_date' ? (
                    <div className="col-span-2">
                        <label className={labelClass}>Target Date</label>
                        <input
                            type="date"
                            className={inputClass}
                            value={formData.target_date}
                            onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
                            required={formData.period_type === 'target_date'}
                        />
                    </div>
                ) : (
                    <div className="col-span-2">
                        <label className={labelClass}>Frequency</label>
                        <div className="relative">
                            <select
                                className={inputClass + " appearance-none"}
                                value={formData.frequency}
                                onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                            >
                                <option value="Weekly">Weekly (Every Week)</option>
                                <option value="Monthly">Monthly (Every Month)</option>
                            </select>
                            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-400">
                                <svg className="h-4 w-4 fill-current" viewBox="0 0 20 20"><path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" fillRule="evenodd"></path></svg>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className={labelClass}>Target Value</label>
                    <input
                        type="number"
                        step="0.1"
                        className={inputClass}
                        placeholder="e.g. 30"
                        value={formData.target_value}
                        onChange={(e) => setFormData({ ...formData, target_value: e.target.value })}
                        required
                    />
                </div>
                <div>
                    <label className={labelClass}>Unit</label>
                    <div className="relative">
                        <select
                            className={inputClass + " appearance-none"}
                            value={formData.target_unit}
                            onChange={(e) => setFormData({ ...formData, target_unit: e.target.value })}
                        >
                            <option value="km">km (Distance)</option>
                            <option value="min">min (Duration)</option>
                            <option value="hours">hours (Duration)</option>
                            <option value="times">times (Count)</option>
                            <option value="kcal">kcal (Energy)</option>
                            <option value="kg">kg (Weight)</option>
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-400">
                            <svg className="h-4 w-4 fill-current" viewBox="0 0 20 20"><path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" fillRule="evenodd"></path></svg>
                        </div>
                    </div>
                </div>
            </div>

            <div>
                <label className={labelClass}>Description (Optional)</label>
                <input
                    type="text"
                    className={inputClass}
                    placeholder="e.g. Prepare for marathon"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
            </div>

            <div className="pt-2">
                <Button type="submit" disabled={loading} className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2">
                    {loading ? 'Saving...' : 'Create Goal'}
                </Button>
            </div>
        </form>
    );
}
