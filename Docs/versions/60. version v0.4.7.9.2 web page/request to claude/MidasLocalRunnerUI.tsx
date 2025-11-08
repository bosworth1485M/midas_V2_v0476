import React, { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Copy, Play, RefreshCcw, Calendar, Lock } from "lucide-react";

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
      alert("Copied the run command to clipboard.");
    } catch (e) {
      console.warn(e);
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
  };

  return (
    <div className="min-h-screen w-full bg-neutral-50 p-6">
      <div className="mx-auto max-w-5xl grid gap-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Midas_V2 – Local Runner UI (skeleton)</h1>
            <p className="text-sm text-neutral-600">
              Phase 1: Uses the STANDARD range runner (non-catalyst). Only builds the exact CLI command you already use.
              No strategy/backtester changes. Features below are placeholders and mostly disabled.
            </p>
          </div>
        </div>

        {/* Date + Scenario Card */}
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Range Controls</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-4">
            <div className="grid gap-2">
              <Label className="flex items-center gap-2"><Calendar className="h-4 w-4"/>Start</Label>
              <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div className="grid gap-2">
              <Label className="flex items-center gap-2"><Calendar className="h-4 w-4"/>End</Label>
              <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>
            <div className="grid gap-2">
              <Label>Scenario</Label>
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
            <div className="grid grid-cols-2 gap-2 items-end">
              <Button variant="secondary" onClick={() => preset("Yesterday")}>Yesterday</Button>
              <Button variant="secondary" onClick={() => preset("Aug2025-Sample")}>Aug 2025</Button>
            </div>
          </CardContent>
        </Card>

        {/* Placeholders (disabled) */}
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Feature Placeholders (disabled in Phase 1)</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3">
            <DisabledField label="Catalyst options" value="Inactive (using standard runner)" />
            <DisabledField label="News min score" value="N/A in standard runner" />
            <DisabledField label="Top-N by gap" value="N/A in standard runner" />
            <DisabledField label="Band enforce" value="N/A in standard runner" />
            <DisabledField label="Opening RVOL" value="N/A in standard runner" />
            <DisabledField label="Gate minutes" value="N/A in standard runner" />
            <DisabledField label="Catalyst deny/exclude filters" value="N/A in standard runner" />
            <DisabledField label="Support/Resistance (S/R Lite)" value="Off (coming soon)" />
            <DisabledField label="Adaptive Sizing A/B" value="Off (coming soon)" />
            <DisabledField label="Candle Snapshots (sidecar)" value="Off (coming soon)" />
            <DisabledField label="Analyzer Panel" value="Read-only (future)" />
            <DisabledField label="Router D>E" value="Off (future)" />
          </CardContent>
        </Card>

        {/* Command Preview */}
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Preview Command</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            <Textarea readOnly value={command || "Fill Start/End to preview the exact command."} className="font-mono text-sm min-h-[120px]" />
            <div className="flex gap-2">
              <Button disabled={!command} onClick={handleCopy} className="flex items-center gap-2"><Copy className="h-4 w-4"/>Copy</Button>
              <Button disabled className="flex items-center gap-2" title="Execution is deliberately disabled in Phase 1."><Play className="h-4 w-4"/>Run (disabled)</Button>
              <Button variant="secondary" onClick={resetAll} className="flex items-center gap-2"><RefreshCcw className="h-4 w-4"/>Reset</Button>
            </div>
            <p className="text-xs text-neutral-500">
              Phase 1 rule: this UI never executes commands—only builds the exact one-liner you can paste into PowerShell.
              Future phases may enable local execution once validated.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function DisabledField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border p-3 bg-neutral-50">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-medium flex items-center gap-2"><Lock className="h-3.5 w-3.5" />{label}</div>
          <div className="text-xs text-neutral-500">{value}</div>
        </div>
      </div>
    </div>
  );
}