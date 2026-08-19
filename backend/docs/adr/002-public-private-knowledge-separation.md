# ADR 002: Separate public knowledge from private user context

Status: accepted for Phase 2.5

Approved public documents and private user records use separate stores, identifiers, access paths, retention rules, and evidence types. Public retrieval cannot access private memory, and private context is assembled only for the authenticated user and requested purpose.

This prevents corpus operations from leaking user data and makes every citation's trust domain visible.
