--
-- PostgreSQL database dump
--

\restrict WJrt0kByBEZVdYo3z8sIyA77cmjB8wpK1PINF4xUiC2sqJ0KTR9d8g2f9HgWeUN

-- Dumped from database version 15.16 (Debian 15.16-1.pgdg13+1)
-- Dumped by pg_dump version 15.17 (Debian 15.17-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: whatif_simulations; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.whatif_simulations DISABLE TRIGGER ALL;

COPY public.whatif_simulations (id, simulation_name, scenario_type, input_params, baseline_snapshot, simulation_result, risk_score, confidence_level, recommendations, affected_projects, affected_resources, kpi_deltas, created_by, created_at) FROM stdin;
68f8ca27-fbf6-478f-8de0-4be3152e3e16	Cascada P1 — 3 incidencias críticas simultáneas en infraestructura financiera	P1_CASCADE	{"description": "Simulación de escenario de crisis donde 3 incidencias P1 se producen simultáneamente afectando servicios financieros críticos: SWIFT, Bizum y procesamiento de tarjetas. Se evalúa la capacidad del pool de 150 técnicos para responder y el impacto en los proyectos BUILD activos.", "simultaneous_p1": 3, "affected_services": ["SWIFT Alliance", "Bizum", "Card Processing"]}	{"available_n3_plus": 12, "total_technicians": 150, "active_p1_incidents": 1, "pool_utilization_pct": 68, "build_projects_active": 28}	{"base_case": {"risk": 62, "cost_delta": "-€45K", "sla_impact": "-12%", "burnout_risk": 55, "timeline_delta": "+5d", "resolution_time_h": 6.0}, "best_case": {"risk": 35, "cost_delta": "€0", "sla_impact": "+0%", "burnout_risk": 30, "timeline_delta": "0d", "resolution_time_h": 3.5}, "worst_case": {"risk": 88, "cost_delta": "-€120K", "sla_impact": "-28%", "burnout_risk": 82, "timeline_delta": "+15d", "resolution_time_h": 12.0}}	62.00	0.78	{"Establecer equipo de crisis pre-designado de 6 técnicos N3+ para escenarios de cascada","Activar freeze automático de BUILD cuando hay 2+ P1 simultáneas","Contratar 3 técnicos N3 de refuerzo en infraestructura financiera antes de Q2","Implementar failover automático para SWIFT y Bizum (reducir MTTR en 40%)","Crear procedimiento de comunicación BCE para cascadas que afecten servicios de pago"}	{PRJ0034,PRJ0035,PRJ0043,PRJ0039,PRJ0041}	{FTE-067,FTE-082,FTE-091,FTE-103,FTE-044,FTE-056}	{"burnout_index": 55, "mttr_increase": "+35%", "estimated_cost": "-€45K", "sla_compliance": "-12%", "pool_utilization": "92%", "build_freeze_projects": 8}	AG-010	2026-03-19 21:40:09.919283+00
51f20125-a68a-4bcc-9078-b6d1a4d2718d	Cascada P1 — 3 incidencias críticas simultáneas en infraestructura financiera	P1_CASCADE	{"description": "Simulación de escenario de crisis donde 3 incidencias P1 se producen simultáneamente afectando servicios financieros críticos: SWIFT, Bizum y procesamiento de tarjetas. Se evalúa la capacidad del pool de 150 técnicos para responder y el impacto en los proyectos BUILD activos.", "simultaneous_p1": 3, "affected_services": ["SWIFT Alliance", "Bizum", "Card Processing"]}	{"available_n3_plus": 12, "total_technicians": 150, "active_p1_incidents": 1, "pool_utilization_pct": 68, "build_projects_active": 28}	{"base_case": {"risk": 62, "cost_delta": "-€45K", "sla_impact": "-12%", "burnout_risk": 55, "timeline_delta": "+5d", "resolution_time_h": 6.0}, "best_case": {"risk": 35, "cost_delta": "€0", "sla_impact": "+0%", "burnout_risk": 30, "timeline_delta": "0d", "resolution_time_h": 3.5}, "worst_case": {"risk": 88, "cost_delta": "-€120K", "sla_impact": "-28%", "burnout_risk": 82, "timeline_delta": "+15d", "resolution_time_h": 12.0}}	62.00	0.78	{"Establecer equipo de crisis pre-designado de 6 técnicos N3+ para escenarios de cascada","Activar freeze automático de BUILD cuando hay 2+ P1 simultáneas","Contratar 3 técnicos N3 de refuerzo en infraestructura financiera antes de Q2","Implementar failover automático para SWIFT y Bizum (reducir MTTR en 40%)","Crear procedimiento de comunicación BCE para cascadas que afecten servicios de pago"}	{PRJ0034,PRJ0035,PRJ0043,PRJ0039,PRJ0041}	{FTE-067,FTE-082,FTE-091,FTE-103,FTE-044,FTE-056}	{"burnout_index": 55, "mttr_increase": "+35%", "estimated_cost": "-€45K", "sla_compliance": "-12%", "pool_utilization": "92%", "build_freeze_projects": 8}	AG-010	2026-03-19 21:48:15.594408+00
\.


ALTER TABLE public.whatif_simulations ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

\unrestrict WJrt0kByBEZVdYo3z8sIyA77cmjB8wpK1PINF4xUiC2sqJ0KTR9d8g2f9HgWeUN

