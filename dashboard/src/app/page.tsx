import { Button } from "@/components/ui/button";

// TODO loang-template: replace this landing with the real dashboard. Keep
// `<html lang="es">` from layout.tsx — UI is Spanish by default for Loang.
export default function Page() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
      <h1 className="text-3xl font-semibold tracking-tight">Loang Agent</h1>
      <p className="max-w-md text-muted-foreground">
        Plantilla del dashboard. Esta página es solo placeholder — edítala y bórrala
        cuando el proyecto cliente añada sus rutas reales.
      </p>
      <Button variant="outline">Botón de muestra</Button>
    </main>
  );
}
