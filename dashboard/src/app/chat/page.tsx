import { findCustomerById } from "@/lib/db";
import { Card, CardContent } from "@/components/ui/card";
import ChatWidget from "./ChatWidget";

const DEMO_CUSTOMER_ID =
  process.env.DEMO_CUSTOMER_ID ?? "00000000-0000-0000-0000-000000000001";

export default async function ChatPage() {
  let customer = null;
  let dbError = false;

  try {
    customer = await findCustomerById(DEMO_CUSTOMER_ID);
  } catch {
    dbError = true;
  }

  if (dbError || !customer) {
    return (
      <main className="flex min-h-[calc(100vh-3.5rem)] flex-col items-center justify-center gap-4 p-8 text-center">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 pb-6 flex flex-col gap-3 text-center">
            <h1 className="text-lg font-semibold">Configuración requerida</h1>
            <p className="text-sm text-muted-foreground">
              Ejecuta{" "}
              <code className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">
                docker compose exec agent alembic upgrade head
              </code>{" "}
              para aplicar las migraciones e inicializar el cliente demo.
            </p>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] flex-col">
      <div className="border-b border-border bg-card/50 px-6 py-3 shrink-0">
        <div className="max-w-3xl mx-auto flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <p className="text-sm font-medium">{customer.name}</p>
          <span className="text-muted-foreground text-xs">· sesión activa</span>
        </div>
      </div>
      <ChatWidget customerId={customer.id} />
    </div>
  );
}
