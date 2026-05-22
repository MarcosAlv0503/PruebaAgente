"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { FileDown, Loader2 } from "lucide-react";
import type { ReportStats } from "@/lib/report-types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type RGB = [number, number, number];

type JsPDFWithPlugin = import("jspdf").jsPDF & {
  lastAutoTable: { finalY: number };
};

// ---------------------------------------------------------------------------
// PDF constants
// ---------------------------------------------------------------------------

const INDIGO: RGB = [79, 70, 229];
const EMERALD: RGB = [16, 185, 129];
const AMBER: RGB = [245, 158, 11];
const RED: RGB = [239, 68, 68];
const SLATE_900: RGB = [15, 23, 42];
const SLATE_500: RGB = [100, 116, 139];
const SLATE_200: RGB = [226, 232, 240];
const SLATE_50: RGB = [248, 250, 252];
const WHITE: RGB = [255, 255, 255];

const PAGE_W = 210;
const PAGE_H = 297;
const ML = 20;
const MR = 20;
const CW = PAGE_W - ML - MR;
const MARGIN_BOTTOM = 18;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function capitalize(str: string): string {
  return str.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function truncate(str: string, maxLen: number): string {
  return str.length > maxLen ? str.slice(0, maxLen - 1) + "…" : str;
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-ES", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

// ---------------------------------------------------------------------------
// PDF generation
// ---------------------------------------------------------------------------

async function generatePdf(stats: ReportStats): Promise<void> {
  const [{ jsPDF }, { default: autoTable }] = await Promise.all([
    import("jspdf"),
    import("jspdf-autotable"),
  ]);

  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const today = new Date().toLocaleDateString("es-ES", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });

  // ---- helpers that close over doc ----------------------------------------

  function setFill(c: RGB): void {
    doc.setFillColor(c[0], c[1], c[2]);
  }
  function setDraw(c: RGB): void {
    doc.setDrawColor(c[0], c[1], c[2]);
  }
  function setTxt(c: RGB): void {
    doc.setTextColor(c[0], c[1], c[2]);
  }

  function drawSection(title: string, y: number): number {
    doc.setFontSize(12);
    doc.setFont("helvetica", "bold");
    setTxt(SLATE_900);
    doc.text(title, ML, y);
    setDraw(INDIGO);
    doc.setLineWidth(0.6);
    doc.line(ML, y + 2, ML + CW, y + 2);
    doc.setLineWidth(0.3);
    return y + 11;
  }

  function drawBar(
    label: string,
    value: number,
    max: number,
    percent: number,
    x: number,
    y: number,
    color: RGB,
  ): number {
    const BAR_OFFSET = 50;
    const BAR_W = 85;
    const BAR_H = 7;

    doc.setFontSize(8.5);
    doc.setFont("helvetica", "normal");
    setTxt(SLATE_500);
    doc.text(label, x, y + BAR_H - 1);

    setFill(SLATE_200);
    doc.rect(x + BAR_OFFSET, y, BAR_W, BAR_H, "F");

    if (value > 0 && max > 0) {
      setFill(color);
      const fillW = Math.max((value / max) * BAR_W, 1);
      doc.rect(x + BAR_OFFSET, y, fillW, BAR_H, "F");
    }

    doc.setFontSize(8.5);
    doc.setFont("helvetica", "bold");
    setTxt(SLATE_900);
    doc.text(
      `${value}  (${percent}%)`,
      x + BAR_OFFSET + BAR_W + 3,
      y + BAR_H - 1,
    );

    return y + BAR_H + 4;
  }

  function checkPage(y: number, needed: number): number {
    if (y + needed > PAGE_H - MARGIN_BOTTOM) {
      doc.addPage();
      // Compact header on continuation pages
      setFill(INDIGO);
      doc.rect(0, 0, PAGE_W, 10, "F");
      doc.setFontSize(7.5);
      doc.setFont("helvetica", "bold");
      setTxt(WHITE);
      doc.text("Loang · Informe del Agente", ML, 7);
      doc.text(today, PAGE_W - MR, 7, { align: "right" });
      return 18;
    }
    return y;
  }

  // ---- Page 1 header -------------------------------------------------------

  setFill(INDIGO);
  doc.rect(0, 0, PAGE_W, 38, "F");
  doc.setFontSize(22);
  doc.setFont("helvetica", "bold");
  setTxt(WHITE);
  doc.text("Informe del Agente", ML, 21);
  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  doc.text("Loang · Soporte Operativo", ML, 30);
  doc.text(today, PAGE_W - MR, 30, { align: "right" });

  let y = 46;

  // ---- Summary box ---------------------------------------------------------

  setFill(SLATE_50);
  setDraw(SLATE_200);
  doc.setLineWidth(0.3);
  doc.roundedRect(ML, y, CW, 28, 3, 3, "FD");

  doc.setFontSize(10);
  doc.setFont("helvetica", "bold");
  setTxt(SLATE_900);
  doc.text("Total de incidencias:", ML + 5, y + 10);
  doc.setFont("helvetica", "normal");
  doc.text(String(stats.total), ML + 57, y + 10);

  if (stats.minDate && stats.maxDate) {
    doc.setFont("helvetica", "bold");
    doc.text("Período:", ML + 5, y + 20);
    doc.setFont("helvetica", "normal");
    doc.text(`${fmtDate(stats.minDate)} — ${fmtDate(stats.maxDate)}`, ML + 57, y + 20);
  }

  y += 36;

  // ---- Section 1: Resolution method ----------------------------------------

  y = drawSection("1. Método de resolución", y);

  const totalSafe = Math.max(stats.total, 1);
  const methods: Array<{ label: string; value: number; color: RGB }> = [
    { label: "Determinista", value: stats.resolutionMethod.deterministic, color: EMERALD },
    { label: "LLM Ligero", value: stats.resolutionMethod.lightLlm, color: INDIGO },
    { label: "LLM Pesado", value: stats.resolutionMethod.heavyLlm, color: RED },
  ];
  const maxMethod = Math.max(...methods.map((m) => m.value), 1);

  for (const m of methods) {
    y = checkPage(y, 11);
    const pct = Math.round((m.value / totalSafe) * 100);
    y = drawBar(m.label, m.value, maxMethod, pct, ML, y, m.color);
  }

  doc.setFontSize(7.5);
  doc.setFont("helvetica", "italic");
  setTxt(SLATE_500);
  doc.text(
    "Determinista: reglas sin LLM  •  LLM Ligero: Claude Haiku + KB  •  LLM Pesado: escalado a Claude Sonnet",
    ML,
    y + 4,
  );
  y += 14;

  // ---- Section 2: Confidence -----------------------------------------------

  y = checkPage(y, 65);
  y = drawSection("2. Confianza de clasificación", y);

  if (stats.confidence.avg !== null) {
    const avgStr = (stats.confidence.avg * 100).toFixed(1) + "%";
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    setTxt(SLATE_900);
    doc.text("Confianza media: ", ML, y + 5);
    doc.setFont("helvetica", "bold");
    doc.text(avgStr, ML + 40, y + 5);
    y += 13;
  }

  const confTotal = Math.max(
    stats.confidence.high + stats.confidence.medium + stats.confidence.low,
    1,
  );
  const confBars: Array<{ label: string; value: number; color: RGB }> = [
    { label: "Alta  (>75%)", value: stats.confidence.high, color: EMERALD },
    { label: "Media (50–75%)", value: stats.confidence.medium, color: AMBER },
    { label: "Baja  (<50%)", value: stats.confidence.low, color: RED },
  ];
  const maxConf = Math.max(...confBars.map((b) => b.value), 1);

  for (const b of confBars) {
    y = checkPage(y, 11);
    const pct = Math.round((b.value / confTotal) * 100);
    y = drawBar(b.label, b.value, maxConf, pct, ML, y, b.color);
  }
  y += 6;

  // ---- Section 3: Resolution by type ---------------------------------------

  y = checkPage(y, 50);
  y = drawSection("3. Resolución por tipo de incidencia", y);

  if (stats.typeStats.length === 0) {
    doc.setFontSize(9);
    setTxt(SLATE_500);
    doc.text("Sin datos disponibles.", ML, y + 6);
    y += 16;
  } else {
    const sorted = [...stats.typeStats]
      .sort(
        (a, b) =>
          b.unresolved / Math.max(b.total, 1) -
          a.unresolved / Math.max(a.total, 1),
      )
      .slice(0, 10);

    const tableBody = sorted.map((t) => [
      capitalize(t.type),
      String(t.total),
      String(t.total - t.unresolved),
      String(t.unresolved),
      `${Math.round((t.unresolved / Math.max(t.total, 1)) * 100)}%`,
    ]);

    autoTable(doc, {
      startY: y,
      head: [["Tipo de incidencia", "Total", "Resueltas", "Sin resolver", "% sin resolver"]],
      body: tableBody,
      styles: {
        fontSize: 8.5,
        cellPadding: { top: 2.5, bottom: 2.5, left: 3, right: 3 },
        textColor: SLATE_900,
      },
      headStyles: {
        fillColor: INDIGO,
        textColor: WHITE,
        fontStyle: "bold",
        fontSize: 8.5,
      },
      alternateRowStyles: { fillColor: SLATE_50 },
      columnStyles: {
        0: { cellWidth: 63 },
        1: { cellWidth: 22, halign: "center" },
        2: { cellWidth: 25, halign: "center" },
        3: { cellWidth: 27, halign: "center" },
        4: { cellWidth: 33, halign: "center" },
      },
      margin: { left: ML, right: MR },
    });

    y = (doc as unknown as JsPDFWithPlugin).lastAutoTable.finalY + 8;
  }

  // ---- Section 4: Top topics -----------------------------------------------

  y = checkPage(y, 20 + Math.min(stats.topTopics.length, 10) * 8);
  y = drawSection("4. Temas más tratados", y);

  if (stats.topTopics.length === 0) {
    doc.setFontSize(9);
    setTxt(SLATE_500);
    doc.text("Sin datos disponibles.", ML, y + 6);
  } else {
    // Numbered list
    for (let i = 0; i < Math.min(stats.topTopics.length, 10); i++) {
      y = checkPage(y, 8);
      const t = stats.topTopics[i];
      doc.setFontSize(9);
      doc.setFont("helvetica", "bold");
      setTxt(SLATE_900);
      doc.text(`${i + 1}.`, ML, y + 5);
      doc.setFont("helvetica", "normal");
      doc.text(capitalize(t.topic), ML + 9, y + 5);
      setTxt(SLATE_500);
      doc.text(
        `${t.count} incidencias · ${t.percent}%`,
        ML + 95,
        y + 5,
      );
      y += 7;
    }

    y += 8;

    // Bar chart
    y = checkPage(y, 20 + Math.min(stats.topTopics.length, 10) * 12);
    y = drawSection("Distribución visual", y);

    const maxCount = Math.max(...stats.topTopics.map((t) => t.count), 1);
    for (const t of stats.topTopics.slice(0, 10)) {
      y = checkPage(y, 12);
      y = drawBar(
        truncate(capitalize(t.topic), 18),
        t.count,
        maxCount,
        t.percent,
        ML,
        y,
        INDIGO,
      );
    }
  }

  // ---- Footer on all pages ------------------------------------------------

  const pageCount = doc.getNumberOfPages();
  for (let p = 1; p <= pageCount; p++) {
    doc.setPage(p);
    doc.setFontSize(7.5);
    doc.setFont("helvetica", "normal");
    setTxt(SLATE_500);
    doc.text(
      "Loang · Soporte Operativo — Informe generado automáticamente",
      ML,
      PAGE_H - 8,
    );
    doc.text(`${p} / ${pageCount}`, PAGE_W - MR, PAGE_H - 8, { align: "right" });
  }

  const fileName = `informe-agente-${new Date().toISOString().slice(0, 10)}.pdf`;
  doc.save(fileName);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ReportButton() {
  const [loading, setLoading] = useState(false);

  async function handleGenerate() {
    setLoading(true);
    try {
      const res = await fetch("/api/report");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const stats = (await res.json()) as ReportStats;
      await generatePdf(stats);
    } catch {
      alert(
        "No se pudo generar el informe. Asegúrate de que la base de datos está en ejecución (make up).",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleGenerate}
      disabled={loading}
      className="flex items-center gap-2"
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <FileDown className="h-4 w-4" />
      )}
      {loading ? "Generando…" : "Generar informe"}
    </Button>
  );
}
