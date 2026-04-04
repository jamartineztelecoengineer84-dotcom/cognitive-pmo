--
-- PostgreSQL database dump
--

\restrict hqJsjSYDXOZVulV1ln7oCAclVX0tYxovX7CoA0UXmjTJHQkXHLct3P0eB7BGlqa

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
-- Data for Name: war_room_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.war_room_sessions DISABLE TRIGGER ALL;

COPY public.war_room_sessions (id, session_name, session_type, status, participants, context, summary, decisions, started_at, closed_at) FROM stdin;
8c7328ac-107f-479e-a490-078bf57a261e	CRISIS P1 — Cascada servicios financieros 19/03/2026	CRISIS_P1	ACTIVE	["AG-001", "AG-002", "AG-004", "AG-008", "AG-012", "Jose Antonio Martinez"]	{"trigger": "CASCADE_FAILURE alert CORR-2026-001", "start_time": "2026-03-19T09:15:00", "services_affected": ["SWIFT", "Bizum", "Card Processing"]}	\N	[]	2026-03-19 21:40:09.92593+00	\N
2f41af0b-95c7-4373-a868-5d379c9da8f9	Fallo en firma de operaciones (OTP SMS no llega)	AD_HOC	ACTIVE	["AG-008", "AG-012"]	{}	\N	[]	2026-03-19 21:42:42.089527+00	\N
89f1071f-5745-4756-8207-5a7ecf02bc6b	CRISIS P1 — Cascada servicios financieros 19/03/2026	CRISIS_P1	ACTIVE	["AG-001", "AG-002", "AG-004", "AG-008", "AG-012", "Jose Antonio Martinez"]	{"trigger": "CASCADE_FAILURE alert CORR-2026-001", "start_time": "2026-03-19T09:15:00", "services_affected": ["SWIFT", "Bizum", "Card Processing"]}	\N	[]	2026-03-19 21:48:15.602981+00	\N
\.


ALTER TABLE public.war_room_sessions ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

\unrestrict hqJsjSYDXOZVulV1ln7oCAclVX0tYxovX7CoA0UXmjTJHQkXHLct3P0eB7BGlqa

