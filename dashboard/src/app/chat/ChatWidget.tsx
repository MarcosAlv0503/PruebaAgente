"use client";

import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AlertTriangle, Bot, CheckCircle2, Loader2, Send } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Classification {
  type?: string;
  severity?: string;
  confidence?: number;
}

type ExecutionStatus = "pending" | "running" | "succeeded" | "failed" | "cancelled";

interface AgentMessage {
  id: string;
  role: "agent";
  execStatus: ExecutionStatus;
  text: string;
  classification?: Classification;
  escalated?: boolean;
  ticketRef?: string;
  timestamp: Date;
}

interface UserMessage {
  id: string;
  role: "user";
  text: string;
  timestamp: Date;
}

type Message = UserMessage | AgentMessage;

// ---------------------------------------------------------------------------
// Form schema
// ---------------------------------------------------------------------------

const schema = z.object({
  message: z
    .string()
    .min(1, "Escribe un mensaje")
    .max(2000, "Máximo 2000 caracteres"),
});
type FormValues = z.infer<typeof schema>;

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SEVERITY_VARIANT = {
  critical: "destructive",
  high: "warning",
  medium: "secondary",
  low: "secondary",
} as const satisfies Record<string, "destructive" | "warning" | "secondary">;

const POLL_INTERVAL_MS = 2_000;
const POLL_TIMEOUT_MS = 120_000;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

interface PollResult {
  text: string;
  execStatus: ExecutionStatus;
  classification?: Classification;
  escalated: boolean;
  ticketRef?: string;
}

async function pollUntilDone(executionId: string): Promise<PollResult> {
  const deadline = Date.now() + POLL_TIMEOUT_MS;

  while (Date.now() < deadline) {
    await new Promise<void>((r) => setTimeout(r, POLL_INTERVAL_MS));

    try {
      const res = await fetch(`/api/incidents/${executionId}`);
      if (!res.ok) continue;

      const data = (await res.json()) as {
        status: ExecutionStatus;
        output?: {
          auto_resolved?: boolean;
          classification?: Classification;
          final_response?: string;
          ticket_ref?: string;
        } | null;
      };

      if (data.status === "pending" || data.status === "running") continue;

      const output = data.output ?? {};
      return {
        text: output.final_response ?? "Sin respuesta del agente.",
        execStatus: data.status,
        classification: output.classification,
        escalated: !(output.auto_resolved ?? true),
        ticketRef: output.ticket_ref ?? undefined,
      };
    } catch {
      // transient network error — keep polling
    }
  }

  return {
    text: "Tiempo de espera agotado. Inténtalo de nuevo.",
    execStatus: "failed",
    escalated: true,
  };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ChatWidget({ customerId }: { customerId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [threadId] = useState<string>(() => crypto.randomUUID());
  const bottomRef = useRef<HTMLDivElement>(null);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const messageValue = watch("message") ?? "";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function onSubmit(values: FormValues) {
    const userMsgId = crypto.randomUUID();
    const agentMsgId = crypto.randomUUID();
    const externalId = crypto.randomUUID();
    const now = new Date();

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", text: values.message, timestamp: now },
      { id: agentMsgId, role: "agent", execStatus: "pending", text: "", timestamp: now },
    ]);
    reset();

    const history = messages.flatMap(
      (m): { role: "user" | "assistant"; content: string }[] => {
        if (m.role === "user") return [{ role: "user", content: m.text }];
        if (m.role === "agent" && m.execStatus === "succeeded" && m.text)
          return [{ role: "assistant", content: m.text }];
        return [];
      },
    );

    try {
      const res = await fetch("/api/incidents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: values.message,
          customer_id: customerId,
          external_id: externalId,
          reported_at: now.toISOString(),
          reporter: "Operador",
          channel: "web",
          thread_id: threadId,
          conversation_history: history,
        }),
      });

      if (!res.ok) {
        const err = (await res.json()) as { error?: string };
        setMessages((prev) =>
          prev.map((m) =>
            m.id === agentMsgId
              ? ({ ...m, execStatus: "failed", text: err.error ?? "Error al enviar la incidencia." } as AgentMessage)
              : m,
          ),
        );
        return;
      }

      setMessages((prev) =>
        prev.map((m) =>
          m.id === agentMsgId ? ({ ...m, execStatus: "running" } as AgentMessage) : m,
        ),
      );

      const queued = (await res.json()) as { execution_id: string };
      const result = await pollUntilDone(queued.execution_id);

      setMessages((prev) =>
        prev.map((m) => (m.id === agentMsgId ? ({ ...m, ...result } as AgentMessage) : m)),
      );
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === agentMsgId
            ? ({ ...m, execStatus: "failed", text: "Error de conexión con el servidor." } as AgentMessage)
            : m,
        ),
      );
    }
  }

  return (
    <div className="flex flex-1 flex-col max-w-3xl mx-auto w-full px-4 py-6 gap-4 min-h-0">
      {/* Message list */}
      <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-1">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-3 pt-16 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
              <Bot className="h-6 w-6 text-primary" />
            </div>
            <p className="text-muted-foreground text-sm max-w-xs">
              Describe una incidencia de la tienda para comenzar. El agente la clasificará y
              resolverá automáticamente si es posible.
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex gap-2.5",
              msg.role === "user" ? "justify-end" : "justify-start",
            )}
          >
            {msg.role === "agent" && (
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary mt-1">
                <Bot className="h-3.5 w-3.5 text-primary-foreground" />
              </div>
            )}

            {msg.role === "user" ? (
              <div className="max-w-[80%] rounded-2xl rounded-tr-sm px-4 py-3 bg-primary text-primary-foreground text-sm leading-relaxed shadow-sm">
                {msg.text}
              </div>
            ) : (
              <AgentBubble msg={msg} />
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-2 shrink-0">
        <Textarea
          placeholder="Ej: El checkout no deja finalizar el pedido desde hace 20 minutos…"
          rows={3}
          {...register("message")}
          disabled={isSubmitting}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              void handleSubmit(onSubmit)();
            }
          }}
          className="resize-none bg-card focus-visible:ring-primary/50"
        />
        <div className="flex items-center justify-between">
          {errors.message ? (
            <p className="text-xs text-red-600">{errors.message.message}</p>
          ) : (
            <p className="text-xs text-muted-foreground">
              {messageValue.length}/2000 · Ctrl+Enter para enviar
            </p>
          )}
          <Button type="submit" disabled={isSubmitting} size="sm" className="gap-1.5">
            {isSubmitting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Send className="h-3.5 w-3.5" />
            )}
            Enviar
          </Button>
        </div>
      </form>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Agent bubble sub-component
// ---------------------------------------------------------------------------

function AgentBubble({ msg }: { msg: AgentMessage }) {
  const isPending = msg.execStatus === "pending" || msg.execStatus === "running";

  return (
    <Card className="max-w-[85%] shadow-sm border-border/60">
      <CardContent className="p-4">
        {isPending ? (
          <div className="flex items-center gap-2.5 text-muted-foreground text-sm py-0.5">
            <div className="flex gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-primary/60 animate-bounce [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 rounded-full bg-primary/60 animate-bounce [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 rounded-full bg-primary/60 animate-bounce" />
            </div>
            <span>Analizando incidencia…</span>
          </div>
        ) : msg.execStatus === "failed" && !msg.text ? (
          <div className="flex items-center gap-2 text-red-600 text-sm">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>Error al procesar. Inténtalo de nuevo.</span>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {/* Badges */}
            {(msg.classification ?? msg.escalated !== undefined) && (
              <div className="flex flex-wrap gap-1.5">
                {msg.classification?.type && (
                  <Badge variant="outline" className="capitalize text-xs">
                    {msg.classification.type}
                  </Badge>
                )}
                {msg.classification?.severity && (
                  <Badge
                    variant={
                      SEVERITY_VARIANT[
                        msg.classification.severity as keyof typeof SEVERITY_VARIANT
                      ] ?? "secondary"
                    }
                    className="capitalize text-xs"
                  >
                    {msg.classification.severity}
                  </Badge>
                )}
                {msg.escalated !== undefined && (
                  msg.escalated ? (
                    <Badge variant="warning" className="flex items-center gap-1 text-xs">
                      <AlertTriangle className="h-2.5 w-2.5" /> Escalado
                    </Badge>
                  ) : (
                    <Badge variant="success" className="flex items-center gap-1 text-xs">
                      <CheckCircle2 className="h-2.5 w-2.5" /> Auto-resuelto
                    </Badge>
                  )
                )}
                {msg.classification?.confidence !== undefined && (
                  <Badge variant="secondary" className="text-xs tabular-nums">
                    {Math.round(msg.classification.confidence * 100)}% confianza
                  </Badge>
                )}
              </div>
            )}

            {/* Response text */}
            <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.text}</p>

            {/* Ticket ref */}
            {msg.ticketRef && (
              <p className="text-xs text-muted-foreground border-t border-border pt-2 mt-1 font-mono">
                Ticket: {msg.ticketRef.split(/[/\\]/).pop()}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
