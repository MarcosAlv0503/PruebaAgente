import { ArrowRight, MessageSquare, LayoutList, Zap, ShieldCheck, Clock } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const FEATURES = [
  {
    icon: Zap,
    title: "Clasificación instantánea",
    description: "Tipo e impacto detectados en segundos sin intervención humana.",
  },
  {
    icon: ShieldCheck,
    title: "Resolución automática",
    description: "Las incidencias documentadas se cierran directamente con la respuesta correcta.",
  },
  {
    icon: Clock,
    title: "Trazabilidad completa",
    description: "Cada ejecución genera log y ticket con toda la cadena de decisión.",
  },
];

export default function Page() {
  return (
    <main className="min-h-[calc(100vh-3.5rem)]">
      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary mb-6">
          <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
          Agente activo
        </div>
        <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
          Soporte operativo{" "}
          <span className="text-primary">inteligente</span>
        </h1>
        <p className="mt-4 max-w-xl mx-auto text-muted-foreground text-lg leading-relaxed">
          Clasifica incidencias técnicas y funcionales, resuelve automáticamente las documentadas
          y escala con trazabilidad completa las que requieren atención humana.
        </p>

        {/* CTA cards */}
        <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-lg mx-auto">
          <a href="/chat" className="group">
            <Card className="h-full border-2 border-transparent transition-all duration-200 group-hover:border-primary/30 group-hover:shadow-md group-hover:-translate-y-0.5">
              <CardContent className="p-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                    <MessageSquare className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-left">
                    <p className="font-semibold text-sm">Chat de soporte</p>
                    <p className="text-xs text-muted-foreground">Reportar incidencia</p>
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform duration-200 group-hover:translate-x-1 group-hover:text-primary" />
              </CardContent>
            </Card>
          </a>

          <a href="/incidents" className="group">
            <Card className="h-full border-2 border-transparent transition-all duration-200 group-hover:border-primary/30 group-hover:shadow-md group-hover:-translate-y-0.5">
              <CardContent className="p-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                    <LayoutList className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-left">
                    <p className="font-semibold text-sm">Incidencias</p>
                    <p className="text-xs text-muted-foreground">Ver historial</p>
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform duration-200 group-hover:translate-x-1 group-hover:text-primary" />
              </CardContent>
            </Card>
          </a>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {FEATURES.map(({ icon: Icon, title, description }) => (
            <div key={title} className="flex gap-3 rounded-xl border border-border bg-card p-5">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                <Icon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium text-sm">{title}</p>
                <p className="mt-1 text-xs text-muted-foreground leading-relaxed">{description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
