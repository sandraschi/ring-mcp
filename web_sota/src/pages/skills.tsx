import { useQuery } from "@tanstack/react-query";
import { BookOpen } from "lucide-react";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export function Skills() {
  const [selected, setSelected] = useState<string | null>(null);
  const skillsQuery = useQuery({
    queryKey: ["ring-skills"],
    queryFn: () => api.getSkills(),
    staleTime: 60_000,
  });

  const skills = skillsQuery.data?.skills ?? [];
  const active = skills.find((s) => s.name === selected) ?? skills[0] ?? null;

  return (
    <div className="space-y-6" data-testid="skills-page">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Skills</h2>
        <p className="text-slate-300" data-testid="skills-summary">
          {skills.length} skill(s) served as{" "}
          <span className="font-mono">skill://</span> resources
        </p>
      </div>

      {skillsQuery.isLoading ? (
        <p className="text-slate-300">Loading skills…</p>
      ) : skillsQuery.isError ? (
        <p className="text-red-400">
          Could not load skills. Is the API running at {api.getBaseUrl()}?
        </p>
      ) : skills.length === 0 ? (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardContent className="pt-6">
            <p className="text-slate-300">
              No skills found. Add <span className="font-mono">SKILL.md</span>{" "}
              files under <span className="font-mono">skills/</span>.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="space-y-2" data-testid="skills-list">
            {skills.map((s) => (
              <Card
                key={s.name}
                data-testid={`skill-${s.name}`}
                className={`cursor-pointer border-slate-800 bg-slate-950/50 hover:bg-slate-900/50 ${active?.name === s.name ? "border-emerald-700" : ""}`}
                onClick={() => setSelected(s.name)}
              >
                <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
                  <BookOpen className="h-4 w-4 text-emerald-500" />
                  <CardTitle className="font-mono text-sm font-medium text-slate-200">
                    {s.name}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-300">{s.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
          <Card className="border-slate-800 bg-slate-950/50 lg:col-span-2">
            <CardHeader>
              <CardTitle
                className="font-mono text-sm text-white"
                data-testid="skills-render-title"
              >
                {active ? active.name : "Select a skill"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <pre
                data-testid="skills-render"
                className="max-h-[60vh] overflow-y-auto whitespace-pre-wrap break-words rounded-md border border-slate-800 bg-slate-900/40 p-3 font-mono text-xs leading-relaxed text-slate-300"
              >
                {active?.content || "No content."}
              </pre>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
