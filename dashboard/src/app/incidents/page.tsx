import { listRecentExecutions } from "@/lib/db";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { AlertTriangle, CheckCircle2, Clock, XCircle } from "lucide-react";

const STATUS_LABEL: Record<string, string> = {
  pending: "Pendiente",
  running: "En proceso",
  succeeded: "Completado",
  failed: "Fallido",
  cancelled: "Cancelado",
};

const STATUS_VARIANT: Record<string, "secondary" | "success" | "destructive" | "outline"> = {
  pending: "secondary",
  running: "secondary",
  succeeded: "success",
  failed: "destructive",
  cancelled: "outline",
};

const SEVERITY_BORDER: Record<string, string> = {
  critical: "border-l-red-500",
  high: "border-l-orange-400",
  medium: "border-l-amber-400",
  low: "border-l-emerald-400",
};

const SEVERITY_DOT: Record<string, string> = {
  critical: "bg-red-500",
  high: "bg-orange-400",
  medium: "bg-amber-400",
  low: "bg-emerald-400",
};

function StatusIcon({ status }: { status: string }) {
  if (status === "succeeded") return <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />;
  if (status === "failed") return <XCircle className="h-3.5 w-3.5 text-red-500" />;
  return <Clock className="h-3.5 w-3.5 text-muted-foreground" />;
}

export default async function IncidentsPage() {
  let executions = null;
  let error = false;

  try {
    executions = await listRecentExecutions(20);
  } catch {
    error = true;
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-8">
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Incidencias recientes</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Últimas 20 ejecuciones del agente</p>
      </div>

      {error ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground text-sm">
            <XCircle className="h-8 w-8 mx-auto mb-3 text-red-400 opacity-60" />
            No se pudo conectar a la base de datos. Asegúrate de que Docker Compose está en
            ejecución (<code className="font-mono text-xs bg-muted px-1 rounded">make up</code>).
          </CardContent>
        </Card>
      ) : !executions || executions.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground text-sm">
            <Clock className="h-8 w-8 mx-auto mb-3 opacity-40" />
            No hay incidencias todavía.{" "}
            <a href="/chat" className="underline underline-offset-4 hover:text-foreground">
              Envía la primera desde el chat.
            </a>
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-2">
          {executions.map((ex) => {
            const cls = ex.classification as { type?: string; severity?: string } | null;
            const severity = cls?.severity?.toLowerCase() ?? "";
            const borderClass = SEVERITY_BORDER[severity] ?? "border-l-border";
            const dotClass = SEVERITY_DOT[severity] ?? "bg-muted-foreground";
            const statusVariant = STATUS_VARIANT[ex.status] ?? "secondary";

            return (
              <Card
                key={ex.id}
                className={`border-l-4 ${borderClass} transition-shadow hover:shadow-md`}
              >
                <CardContent className="px-5 py-3.5">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1.5">
                        <StatusIcon status={ex.status} />
                        <p className="text-sm font-medium truncate">
                          {ex.message ?? (
                            <span className="text-muted-foreground italic font-normal">
                              Sin mensaje
                            </span>
                          )}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        <Badge variant={statusVariant}>
                          {STATUS_LABEL[ex.status] ?? ex.status}
                        </Badge>
                        {cls?.type && (
                          <Badge variant="outline" className="capitalize">
                            {cls.type}
                          </Badge>
                        )}
                        {cls?.severity && (
                          <Badge variant="outline" className="capitalize flex items-center gap-1">
                            <span className={`h-1.5 w-1.5 rounded-full ${dotClass}`} />
                            {cls.severity}
                          </Badge>
                        )}
                        {ex.auto_resolved !== null && ex.auto_resolved !== undefined && (
                          <Badge variant={ex.auto_resolved ? "success" : "warning"}>
                            {ex.auto_resolved ? (
                              <span className="flex items-center gap-1">
                                <CheckCircle2 className="h-3 w-3" /> Auto-resuelto
                              </span>
                            ) : (
                              <span className="flex items-center gap-1">
                                <AlertTriangle className="h-3 w-3" /> Escalado
                              </span>
                            )}
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="text-right text-xs text-muted-foreground whitespace-nowrap shrink-0">
                      <p className="font-medium text-foreground/70">{ex.customer_name ?? "—"}</p>
                      <p className="mt-0.5 tabular-nums">
                        {new Date(ex.created_at).toLocaleString("es-ES", {
                          day: "2-digit",
                          month: "2-digit",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </main>
  );
}
