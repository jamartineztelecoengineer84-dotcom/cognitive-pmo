--
-- PostgreSQL database dump
--

\restrict M7CAtCcVeMXrdeydC6TqT0vguv0YfGXmMtWQA7ISMApZ4MmZEUjrTCHohK2tJvb

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
-- Data for Name: incidencias_live; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.incidencias_live DISABLE TRIGGER ALL;

COPY public.incidencias_live (ticket_id, incidencia_detectada, prioridad, categoria, estado, sla_horas, tecnico_asignado, area_afectada, fecha_creacion, fecha_limite, progreso_pct, total_tareas, tareas_completadas, agente_origen, canal_entrada, reportado_por, servicio_afectado, impacto_negocio, notas) FROM stdin;
INC-20260325-CE97	[RE-RUN RUN-CAT-649] P4 | Lentitud en aplicativo de Agentes (Citrix)	P4	\N	IN_PROGRESS	72	\N	\N	2026-03-25 12:47:52.377921	2026-03-28 12:47:52.377921	0	0	0	AG-001					\N
\.


ALTER TABLE public.incidencias_live ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

\unrestrict M7CAtCcVeMXrdeydC6TqT0vguv0YfGXmMtWQA7ISMApZ4MmZEUjrTCHohK2tJvb

