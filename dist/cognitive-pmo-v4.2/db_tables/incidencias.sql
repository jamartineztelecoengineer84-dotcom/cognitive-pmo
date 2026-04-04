--
-- PostgreSQL database dump
--

\restrict 16wgeY6c2nHSOPa0DXtfaEk6e9RD8oyafRPmPPWpoPXo9NPbGUbRkQQczRV5TRH

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
-- Data for Name: incidencias; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.incidencias DISABLE TRIGGER ALL;

COPY public.incidencias (id_incidencia, descripcion, prioridad, categoria, estado, sla_limite, tecnico_asignado, fecha_creacion, flag_build_vs_run, impacto_negocio) FROM stdin;
INC-02990DA7	Test incidencia	Alta	Redes	QUEUED	4h	FTE-001	2026-03-19 17:45:00.982413	t	Medio
\.


ALTER TABLE public.incidencias ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

\unrestrict 16wgeY6c2nHSOPa0DXtfaEk6e9RD8oyafRPmPPWpoPXo9NPbGUbRkQQczRV5TRH

