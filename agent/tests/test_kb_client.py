"""Unit tests for agent.services.clients.kb_client.

Uses a temporary directory as the KB root via the KB_PATH env var so
the real agent/knowledge/ files are never touched.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agent.services.clients import kb_client


@pytest.fixture()
def kb_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temp KB directory and point KB_PATH at it."""
    root = tmp_path / "knowledge"
    root.mkdir()
    monkeypatch.setenv("KB_PATH", str(root))
    return root


# ---------------------------------------------------------------------------
# Empty / missing cases
# ---------------------------------------------------------------------------

def test_search_returns_empty_list_for_no_keywords(kb_root: Path) -> None:
    (kb_root / "doc.md").write_text("# Login\nRestablece tu contraseña.", encoding="utf-8")
    assert kb_client.search([]) == []


def test_search_returns_empty_list_when_kb_dir_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KB_PATH", str(tmp_path / "nonexistent"))
    result = kb_client.search(["login"])
    assert result == []


def test_search_returns_empty_list_when_no_files_match(kb_root: Path) -> None:
    (kb_root / "shipping.md").write_text("# Envíos\nInformación sobre envíos.", encoding="utf-8")
    result = kb_client.search(["checkout", "pagar"])
    assert result == []


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def test_search_returns_result_for_matching_keyword(kb_root: Path) -> None:
    (kb_root / "login.md").write_text(
        "# Recuperación de contraseña\nPara recuperar tu contraseña ve a la sección login.",
        encoding="utf-8",
    )
    results = kb_client.search(["login"])
    assert len(results) == 1
    result = results[0]
    assert "login.md" in result["path"]
    assert result["score"] >= 1
    assert result["title"] == "Recuperación de contraseña"
    assert "contraseña" in result["excerpt"]


def test_search_orders_results_by_score_descending(kb_root: Path) -> None:
    (kb_root / "high.md").write_text(
        "# Checkout\nEl checkout falla. El checkout no procesa pagos. Checkout error.",
        encoding="utf-8",
    )
    (kb_root / "low.md").write_text(
        "# Pago\nEl pago mediante checkout no funciona.",
        encoding="utf-8",
    )
    results = kb_client.search(["checkout"])
    assert len(results) == 2
    assert results[0]["score"] > results[1]["score"]


def test_search_respects_top_k_limit(kb_root: Path) -> None:
    for i in range(5):
        (kb_root / f"doc{i}.md").write_text(
            f"# Doc {i}\nEste documento habla de login y contraseña.",
            encoding="utf-8",
        )
    results = kb_client.search(["login"], top_k=2)
    assert len(results) <= 2


def test_search_top_k_default_is_3(kb_root: Path) -> None:
    for i in range(5):
        (kb_root / f"faq{i}.md").write_text(
            f"# FAQ {i}\nInformación sobre el checkout y los pagos.",
            encoding="utf-8",
        )
    results = kb_client.search(["checkout"])
    assert len(results) <= 3


# ---------------------------------------------------------------------------
# File filtering
# ---------------------------------------------------------------------------

def test_search_skips_files_starting_with_underscore(kb_root: Path) -> None:
    (kb_root / "_deprecated.md").write_text(
        "# Antiguo\nEste archivo contiene login y checkout información.",
        encoding="utf-8",
    )
    results = kb_client.search(["login", "checkout"])
    assert all("_deprecated" not in r["path"] for r in results)


def test_search_finds_files_in_subdirectories(kb_root: Path) -> None:
    subdir = kb_root / "faqs"
    subdir.mkdir()
    (subdir / "acceso.md").write_text(
        "# Acceso a la cuenta\nProblemas de login y acceso.",
        encoding="utf-8",
    )
    results = kb_client.search(["login"])
    assert len(results) == 1
    assert "acceso.md" in results[0]["path"]


# ---------------------------------------------------------------------------
# Title extraction
# ---------------------------------------------------------------------------

def test_search_extracts_title_from_h1_header(kb_root: Path) -> None:
    (kb_root / "doc.md").write_text(
        "# Mi Título de Prueba\nContenido con checkout y pago.",
        encoding="utf-8",
    )
    results = kb_client.search(["checkout"])
    assert results[0]["title"] == "Mi Título de Prueba"


def test_search_uses_sin_titulo_when_no_h1(kb_root: Path) -> None:
    (kb_root / "doc.md").write_text(
        "## Subtítulo sin H1\nContenido con checkout y pago.",
        encoding="utf-8",
    )
    results = kb_client.search(["checkout"])
    assert results[0]["title"] == "Sin título"


# ---------------------------------------------------------------------------
# Excerpt
# ---------------------------------------------------------------------------

def test_search_excerpt_is_capped_at_600_chars(kb_root: Path) -> None:
    long_content = "# Doc\n" + "checkout " * 200
    (kb_root / "long.md").write_text(long_content, encoding="utf-8")
    results = kb_client.search(["checkout"])
    assert len(results[0]["excerpt"]) <= 600
