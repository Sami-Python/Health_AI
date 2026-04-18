"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { API_BASE_URL, fetchWithRetry } from "@/lib/utils";
import { Brain, Target, Zap, X, ChevronRight, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface OnboardingWizardProps {
  onComplete: () => void;
}

const STEPS = [
  {
    id: "profile",
    icon: Brain,
    title: "Täytä profiilisi",
    description: "Tallennamme perustietosi jotta AI Coach voi räätälöidä suositukset sinulle.",
    color: "blue",
  },
  {
    id: "garmin",
    icon: Zap,
    title: "Yhdistä Garmin",
    description: "Garmin Connect -yhdistyksen avulla saamme päivittäisen palautumisdatasi (Body Battery, uni, stressi).",
    color: "emerald",
  },
  {
    id: "goal",
    icon: Target,
    title: "Aseta ensimmäinen tavoite",
    description: "Tavoitteen avulla AI Coach osaa ohjelmoida treenisi oikein – esim. 50 km/viikko tai kilpailu 6 kk päässä.",
    color: "purple",
  },
];

export default function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const { user } = useAuth();
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [dismissed, setDismissed] = useState(false);

  const handleDismiss = () => {
    localStorage.setItem("onboarding_dismissed", "true");
    setDismissed(true);
    onComplete();
  };

  const handleAction = (stepId: string) => {
    if (stepId === "profile") {
      router.push("/profile");
    } else if (stepId === "garmin") {
      router.push("/settings?tab=garmin");
    } else if (stepId === "goal") {
      // Scroll to AddGoalForm on dashboard
      const el = document.getElementById("add-goal-input");
      if (el) {
        el.focus();
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      handleDismiss();
    }
  };

  const step = STEPS[currentStep];
  const Icon = step.icon;

  const colorMap: Record<string, string> = {
    blue: "from-blue-600 to-cyan-600",
    emerald: "from-emerald-600 to-teal-600",
    purple: "from-purple-600 to-indigo-600",
  };
  const bgMap: Record<string, string> = {
    blue: "bg-blue-500/10 text-blue-400",
    emerald: "bg-emerald-500/10 text-emerald-400",
    purple: "bg-purple-500/10 text-purple-400",
  };

  if (dismissed) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4 animate-in fade-in duration-300">
      <div className="relative w-full max-w-md bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl shadow-black/60 overflow-hidden">
        {/* Top progress bar */}
        <div className="h-1 bg-slate-800 w-full">
          <div
            className="h-1 bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
            style={{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }}
          />
        </div>

        {/* Close button */}
        <button
          onClick={handleDismiss}
          className="absolute top-4 right-4 text-slate-500 hover:text-white transition-colors z-10"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Step indicator dots */}
        <div className="flex items-center justify-center gap-2 pt-5 pb-2">
          {STEPS.map((s, i) => (
            <button
              key={s.id}
              onClick={() => setCurrentStep(i)}
              className={`w-2 h-2 rounded-full transition-all ${
                i === currentStep
                  ? "bg-white w-4"
                  : i < currentStep
                  ? "bg-emerald-500"
                  : "bg-slate-700"
              }`}
            />
          ))}
        </div>

        {/* Content */}
        <div className="px-8 pb-8 pt-4">
          {/* Icon */}
          <div className={`w-16 h-16 rounded-2xl ${bgMap[step.color]} flex items-center justify-center mx-auto mb-6`}>
            <Icon className="h-8 w-8" />
          </div>

          {/* Step number */}
          <p className="text-center text-xs text-slate-500 uppercase tracking-widest mb-2">
            Askel {currentStep + 1} / {STEPS.length}
          </p>

          {/* Title & Description */}
          <h2 className="text-2xl font-bold text-center text-slate-100 mb-3">
            {step.title}
          </h2>
          <p className="text-center text-slate-400 text-sm leading-relaxed mb-8">
            {step.description}
          </p>

          {/* Action buttons */}
          <div className="space-y-3">
            <Button
              onClick={() => handleAction(step.id)}
              className={`w-full bg-gradient-to-r ${colorMap[step.color]} hover:opacity-90 text-white font-semibold shadow-lg h-11`}
            >
              {step.id === "profile" && "Avaa profiiliasetukset"}
              {step.id === "garmin" && "Yhdistä Garmin nyt"}
              {step.id === "goal" && "Aseta tavoite"}
              <ChevronRight className="ml-2 h-4 w-4" />
            </Button>

            {currentStep < STEPS.length - 1 && (
              <Button
                variant="ghost"
                onClick={() => setCurrentStep((s) => s + 1)}
                className="w-full text-slate-500 hover:text-slate-300 font-normal"
              >
                Ohita tällä kertaa →
              </Button>
            )}

            {currentStep === STEPS.length - 1 && (
              <Button
                variant="ghost"
                onClick={handleDismiss}
                className="w-full text-slate-500 hover:text-slate-300 font-normal"
              >
                <CheckCircle2 className="mr-2 h-4 w-4" /> Valmis, sulje
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
