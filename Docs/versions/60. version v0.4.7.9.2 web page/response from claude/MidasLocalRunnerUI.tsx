import React, { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Copy, Play, RefreshCcw, Calendar, Lock, AlertCircle } from "lucide-react";

// ----------
// Midas_V2 – Local Runner Web UI (Phase 1, STANDARD range runner)
// Purpose: a thin, optional launcher that ONLY builds the exact CLI command
// you already run manually. No strategy/backtester changes. Most features
// are visible but disabled for now so we can wire them in later.
// ----------

export default function MidasLocalRunnerUI() {
  // Core controls
  const [startDate, setStartDate] = useState(""); // YYYY-MM-DD
  const [endDate, setEndDate] = useState("");
  const [scenario, setScenario] = useState("B");
  const [copySuccess, setCopySuccess] = useState(false);

  // (Preview-only; disabled for Phase 1)
  const [newsMinScore] = useState<number>(3);
  const [topN] = useState<number>(3);
  const [bandMin] = useState<number>(10);
  const [bandMax] = useState<number>(40);
  const [minRvolOpen] = useState<number>(2.0);
  const [gateMinutes] = useState<number>(15);

  // Helpers
  const isValidDate = (s: string) => /^\d{4}-\d{2}-\d{2}$/.test(s);
  const datesValid = isValidDate(startDate) && isValidDate(endDate);

  const command = useMemo(() => {
    if (!datesValid) return "";

    // Phase 1: STANDARD range runner (non-catalyst) to sanity-check features over wide ranges
    const parts: string[] = [
      "python",
      "scripts\\run_range_and_summarize.py",
      "--start", startDate,
      "--end", endDate,
      "--scenario", scenario,
    ];

    return parts.join(" ");
  }, [startDate, endDate, scenario, datesValid]);

  const handleCopy = async () => {
    if (!command) return;
    try {
      await navigator.clipboard.writeText(command);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (e) {
      console.warn("Failed to copy:", e);
      alert("Failed to copy to clipboard. Please copy manually.");
    }
  };

  const preset = (label: "Yesterday" | "Aug2025-Sample") => {
    if (label === "Yesterday") {
      const d = new Date();
      d.setDate(d.getDate() - 1);
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, "0");
      const dd = String(d.getDate()).padStart(2, "0");
      const y = `${yyyy}-${mm}-${dd}`;
      setStartDate(y);
      setEndDate(y);
    } else if (label === "Aug2025-Sample") {
      setStartDate("2025-08-05");
      setEndDate("2025-08-31");
    }
  };

  const resetAll = () => {
    setStartDate("");
    setEndDate("");
    setScenario("B");
    setCopySuccess(false);
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-neutral-50 to-neutral-100 p-6">
      <div className="mx-auto max-w-5xl grid gap-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-neutral-900">
              Midas_V2 – Local Runner UI
            </h1>
            <p className="mt-2 text-sm text-neutral-600 max-w-2xl">
              <span className="font-semibold">Phase 1:</span> Uses the STANDARD range runner (non-catalyst). 
              Only builds the exact CLI command you already use. No strategy/backtester changes. 
              Features below are placeholders and mostly disabled.
            </p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg">
            <AlertCircle className="h-4 w-4 text-blue-600" />
            <span className="text-xs font-medium text-blue-700">Phase 1 - Preview Only</span>
          </div>
        </div>

        {/* Date + Scenario Card */}
        <Card className="shadow-md border-neutral-200">
          <CardHeader className="bg-neutral-50/50">
            <CardTitle className="text-lg font-semibold">Range Controls</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 pt-6">
            <div className="grid gap-4 md:grid-cols-4">
              <div className="grid gap-2">
                <Label className="flex items-center gap-2 text-sm font-medium">
                  <Calendar className="h-4 w-4 text-neutral-500"/>
                  Start Date
                </Label>
                <Input 
                  type="date" 
                  value={startDate} 
                  onChange={(e) => setStartDate(e.target.value)}
                  className="font-mono"
                />
              </div>
              <div className="grid gap-2">
                <Label className="flex items-center gap-2 text-sm font-medium">
                  <Calendar className="h-4 w-4 text-neutral-500"/>
                  End Date
                </Label>
                <Input 
                  type="date" 
                  value={endDate} 
                  onChange={(e) => setEndDate(e.target.value)}
                  className="font-mono"
                />
              </div>
              <div className="grid gap-2">
                <Label className="text-sm font-medium">Scenario</Label>
                <Select value={scenario} onValueChange={setScenario}>
                  <SelectTrigger>
                    <SelectValue placeholder="Pick scenario" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="A">A</SelectItem>
                    <SelectItem value="B">B (baseline)</SelectItem>
                    <SelectItem value="C">C</SelectItem>
                    <SelectItem value="D">D_strict</SelectItem>
                    <SelectItem value="E">E_dip</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label className="text-sm font-medium">Quick Presets</Label>
                <div className="grid grid-cols-2 gap-2">
                  <Button 
                    variant="secondary" 
                    size="sm"
                    onClick={() => preset("Yesterday")}
                    className="text-xs"
                  >
                    Yesterday
                  </Button>
                  <Button 
                    variant="secondary" 
                    size="sm"
                    onClick={() => preset("Aug2025-Sample")}
                    className="text-xs"
                  >
                    Aug 2025
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Feature Placeholders (disabled) */}
        <Card className="shadow-md border-neutral-200">
          <CardHeader className="bg-neutral-50/50">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              Feature Placeholders
              <span className="text-xs font-normal text-neutral-500">(disabled in Phase 1)</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3 pt-6">
            <DisabledField label="Catalyst Options" value="Inactive (using standard runner)" />
            <DisabledField label="News Min Score" value="N/A in standard runner" />
            <DisabledField label="Top-N by Gap" value="N/A in standard runner" />
            <DisabledField label="Band Enforce" value="N/A in standard runner" />
            <DisabledField label="Opening RVOL" value="N/A in standard runner" />
            <DisabledField label="Gate Minutes" value="N/A in standard runner" />
            <DisabledField label="Catalyst Deny/Exclude" value="N/A in standard runner" />
            <DisabledField label="Support/Resistance (S/R Lite)" value="Off (coming soon)" />
            <DisabledField label="Adaptive Sizing A/B" value="Off (coming soon)" />
            <DisabledField label="Candle Snapshots" value="Off (coming soon)" />
            <DisabledField label="Analyzer Panel" value="Read-only (future)" />
            <DisabledField label="Router D→E" value="Off (future)" />
          </CardContent>
        </Card>

        {/* Command Preview */}
        <Card className="shadow-md border-neutral-200">
          <CardHeader className="bg-neutral-50/50">
            <CardTitle className="text-lg font-semibold">Command Preview</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 pt-6">
            <div className="relative">
              <Textarea 
                readOnly 
                value={command || "← Fill Start/End dates above to preview the exact command."} 
                className="font-mono text-sm min-h-[120px] bg-neutral-900 text-green-400 border-neutral-700 resize-none"
                placeholder="Command will appear here..."
              />
              {!command && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="text-neutral-400 text-sm flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    <span>Enter dates to generate command</span>
                  </div>
                </div>
              )}
            </div>
            
            <div className="flex gap-2 flex-wrap">
              <Button 
                disabled={!command} 
                onClick={handleCopy} 
                className="flex items-center gap-2"
                variant={copySuccess ? "default" : "default"}
              >
                <Copy className="h-4 w-4"/>
                {copySuccess ? "Copied!" : "Copy"}
              </Button>
              <Button 
                disabled 
                className="flex items-center gap-2 opacity-50" 
                title="Execution is deliberately disabled in Phase 1."
              >
                <Play className="h-4 w-4"/>
                Run (disabled)
              </Button>
              <Button 
                variant="secondary" 
                onClick={resetAll} 
                className="flex items-center gap-2"
              >
                <RefreshCcw className="h-4 w-4"/>
                Reset
              </Button>
            </div>
            
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="text-xs text-amber-800 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>
                  <strong>Phase 1 rule:</strong> This UI never executes commands—only builds the exact 
                  one-liner you can paste into PowerShell. Future phases may enable local execution once validated.
                </span>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Footer Note */}
        <div className="text-center text-xs text-neutral-500 pb-4">
          Midas_V2 Local Runner UI • Phase 1 Foundation • Non-Executing Preview Only
        </div>
      </div>
    </div>
  );
}

function DisabledField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-neutral-200 p-3 bg-gradient-to-br from-neutral-50 to-neutral-100/50 hover:border-neutral-300 transition-colors">
      <div className="flex items-start gap-2">
        <Lock className="h-3.5 w-3.5 text-neutral-400 mt-0.5 flex-shrink-0" />
        <div>
          <div className="text-sm font-medium text-neutral-700">{label}</div>
          <div className="text-xs text-neutral-500 mt-0.5">{value}</div>
        </div>
      </div>
    </div>
  );
}
