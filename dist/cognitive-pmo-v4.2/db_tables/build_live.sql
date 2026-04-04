--
-- PostgreSQL database dump
--

\restrict OzIe1YUhZq4UuaiMmbMEXtZPeuK4ht1QCMMG5uuawAETFVFT0K4EKTnh8M7u6h5

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
-- Data for Name: build_live; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.build_live DISABLE TRIGGER ALL;

COPY public.build_live (id_proyecto, nombre, pm_asignado, prioridad, estado, fecha_inicio, fecha_fin_prevista, progreso_pct, total_tareas, tareas_completadas, sprint_actual, total_sprints, presupuesto_bac, presupuesto_consumido, risk_score, gate_actual, story_points_total, story_points_completados, velocity_media) FROM stdin;
PRJ-MN36W1K3	{"nombre":"Plataforma de Contenedores OpenShift On-Premise","resumen":"Implementar Red Hat OpenShift en nuestros data centers para orquestar contenedores Docker. Necesitamos 3 clústeres (desarrollo, pre-producción y producción) para acelerar el time-to-market de aplicaciones digitales. Actualmente los despliegues tardan semanas y son manuales.","presupuesto_propuesto":650000,"fecha_fin_deseada":"2027-01-01","duracion_semanas_calculada":41,"prioridad":"Media","justificacion":"Las FinTech nos superan en velocidad de entrega. Necesitamos DevOps y CI/CD para competir. Además queremos preparar la infraestructura para futuro MLOps e IA.","fecha_solicitud":"2026-03-23","origen":"negocio"}	Pendiente	Alta	EN_EJECUCION	2026-03-23 12:56:15.111523	\N	0	0	0	1	0	0	0	0	G2-PLANIFICACION	0	0	0
PRJ-MN3SH4W2	{"nombre":"Plataforma de Contenedores OpenShift On-Premise","resumen":"Implementar Red Hat OpenShift en 3 clústeres para orquestar contenedores Docker y automatizar CI/CD","presupuesto_propuesto":650000,"fecha_fin_deseada":"2027-01-01","duracion_semanas_calculada":41,"prioridad":"Media","justificacion":"FinTech nos superan en velocidad de entrega","fecha_solicitud":"2026-03-23","origen":"negocio"}	Pendiente	Alta	EN_EJECUCION	2026-03-23 23:00:31.145743	\N	0	0	0	1	0	0	0	0	G2-PLANIFICACION	0	0	0
PRJ-MN5YI9GX	{"nombre":"Aplicar control de acceso a la red (NAC) en oficinas comerciales","resumen":"Proyecto estratégico para aplicar control de acceso a la red (nac) en oficinas comerciales. Inversión de 265,854€ durante 32 semanas. Alineado con la estrategia de transformación digital y modernización tecnológica del banco.","presupuesto_propuesto":265854,"fecha_fin_deseada":null,"duracion_semanas_calculada":null,"prioridad":"Alta","justificacion":"• Cumplimiento normativo BCE/DORA obligatorio\\n• Brechas de seguridad detectadas en auditoría\\n• Necesidad de proteger activos críticos del banco","fecha_solicitud":"2026-03-25","origen":"negocio"}	Pendiente	Alta	EN_EJECUCION	2026-03-25 11:24:53.921058	\N	0	0	0	1	16	0	0	0	G2-PLANIFICACION	405	0	0
PRJ-MN6J2GT3	Definición e implementación de CCoE	Pendiente	Alta	EN_EJECUCION	2026-03-25 21:00:28.727667	\N	0	0	0	1	19	287638	0	0	G2-PLANIFICACION	334	0	0
PRJ-MN7U6DZ2	Nuevo modelo de gestion de Ticketing	Pendiente	Alta	EN_EJECUCION	2026-03-26 18:59:13.640461	\N	0	0	0	1	16	229968	0	0	G2-PLANIFICACION	304	0	0
\.


ALTER TABLE public.build_live ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

\unrestrict OzIe1YUhZq4UuaiMmbMEXtZPeuK4ht1QCMMG5uuawAETFVFT0K4EKTnh8M7u6h5

