"""Adapters to systems outside the agent.

This package is the seam between the agent's domain logic (``phases/``) and
the external systems the project integrates with (CRM, billing, messaging).

The single-centralised-client pattern (Playbook §5.1.7) lives under
``services/clients/``: one Python module per provider, exposing a small
domain-shaped interface that hides HTTP/SDK details.
"""
