"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL, fetchWithRetry } from "@/lib/utils";
import { Sparkles, RefreshCw, Calendar } from "lucide-react";
import Skeleton from "@/components/ui/Skeleton";

interface WeeklySummaryData {
  summary: string;
  week_start: string;
  cached: boolean;
}

export default function WeeklySummaryCard() {
  const { user } = useAuth();
  const [data, setData] = useState<WeeklySummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchSummary = useCallback(
    async (forceRefresh = false) => {
      if (!user) return;
      if (forceRefresh) setRefreshing(true);
      else setLoading(true);

      try {
        const token = await user.getIdToken();
        const res = await fetchWithRetry(
          `${API_BASE_URL}/ai/weekly-summary${forceRefresh ? "?refresh=1" : ""}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (res.ok) {
          setData(await res.json());
          setError(false);
        } else {
          setError(true);
        }
      } catch {
        setError(true);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [user]
  );

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  // Determine week label
  const weekLabel = data?.week_start
    ? (() => {
        const d = new Date(data.week_start);
        return d.toLocaleDateString("fi-FI", {
          day: "numeric",
          month: "long",
        });
      })()
    : null;

  return (
    <div className="relative rounded-2xl border border-violet-800/40 bg-gradient-to-br from-violet-950/60 via-slate-900/80 to-indigo-950/50 p-6 backdrop-blur-md overflow-hidden group transition-all hover:border-violet-700/60 shadow-lg shadow-violet-900/20">
      {/* Background glow */}
      <div className="absolute top-0 right-0 w-40 h-40 bg-violet-500/10 rounded-full blur-3xl -z-10 group-hover:bg-violet-500/15 transition-colors" />
      <div className="absolute bottom-0 left-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-3xl -z-10" />

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-violet-500/20 text-violet-400">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">
              Viikon yhteenveto
            </h2>
            {weekLabel && (
              <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                <Calendar className="h-3 w-3" />
                {weekLabel} alkaen
              </p>
            )}
          </div>
        </div>
        <button
          onClick={() => fetchSummary(true)}
          disabled={refreshing || loading}
          title="Päivitä yhteenveto"
          className="p-2 rounded-lg text-slate-500 hover:text-violet-400 hover:bg-violet-500/10 transition-all disabled:opacity-40"
        >
          <RefreshCw
            className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
          />
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-4 w-full rounded" />
          <Skeleton className="h-4 w-5/6 rounded" />
          <Skeleton className="h-4 w-4/6 rounded" />
        </div>
      ) : error ? (
        <p className="text-slate-500 text-sm italic">
          Viikkoyhteenveto ei juuri nyt saatavilla.
        </p>
      ) : data?.summary ? (
        <div className="space-y-2">
          <p className="text-slate-200 text-sm leading-relaxed">
            {data.summary}
          </p>
          {data.cached && (
            <p className="text-[11px] text-slate-600 mt-1">
              ✓ Välimuistista (tämän viikon)
            </p>
          )}
        </div>
      ) : (
        <p className="text-slate-500 text-sm italic">
          Ei tarpeeksi dataa yhteenvetoon. Synkronoi Garmin-data ensin.
        </p>
      )}
    </div>
  );
}
