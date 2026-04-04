--
-- PostgreSQL database dump
--

\restrict ugdE4ZeLIBNxISGdjFctiY41hAscdEmlpxdbc7OMaFkxYlFe7BjmTlhMWQEhImg

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
-- Data for Name: build_sprints; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.build_sprints DISABLE TRIGGER ALL;

COPY public.build_sprints (id, id_proyecto, sprint_number, nombre, sprint_goal, fecha_inicio, fecha_fin, story_points_planificados, story_points_completados, estado, burndown_data, velocity, notas_retro, created_at) FROM stdin;
PS-MN6IK6Y0-S1	PS-MN6IK6Y0	1	Sprint 1	Auditoría inicial de infraestructura y procesos existentes	\N	\N	13	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:28.953874
PS-MN6IK6Y0-S2	PS-MN6IK6Y0	2	Sprint 2	Evaluación de capacidades y definición de arquitectura objetivo	\N	\N	16	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:28.960441
PS-MN6IK6Y0-S3	PS-MN6IK6Y0	3	Sprint 3	Definición de roadmap de transformación y plan de capacitación	\N	\N	18	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:28.968063
PS-MN6IK6Y0-S4	PS-MN6IK6Y0	4	Sprint 4	Validación y aprobación del diseño organizacional	\N	\N	13	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:28.975795
PS-MN6IK6Y0-S5	PS-MN6IK6Y0	5	Sprint 5	Análisis y mapeo de procesos PMBOK actuales	\N	\N	21	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:28.983079
PS-MN6IK6Y0-S6	PS-MN6IK6Y0	6	Sprint 6	Diseño de procesos PMBOK optimizados	\N	\N	19	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:28.990503
PS-MN6IK6Y0-S7	PS-MN6IK6Y0	7	Sprint 7	Análisis y diseño de procesos ITIL	\N	\N	20	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:28.997767
PS-MN6IK6Y0-S8	PS-MN6IK6Y0	8	Sprint 8	Implementación de herramientas y procesos ITIL	\N	\N	18	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:29.007534
PS-MN6IK6Y0-S9	PS-MN6IK6Y0	9	Sprint 9	Integración PMBOK-ITIL y documentación	\N	\N	19	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:29.014477
PS-MN6IK6Y0-S10	PS-MN6IK6Y0	10	Sprint 10	Validación y pruebas piloto de procesos	\N	\N	19	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:29.021613
PS-MN6IK6Y0-S11	PS-MN6IK6Y0	11	Sprint 11	Auditoría y preparación de infraestructura base	\N	\N	21	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:29.028804
PS-MN6IK6Y0-S12	PS-MN6IK6Y0	12	Sprint 12	Instalación y configuración base de OpenShift	\N	\N	21	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:29.035549
PS-MN6IK6Y0-S13	PS-MN6IK6Y0	13	Sprint 13	Configuración de servicios core y almacenamiento	\N	\N	21	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:29.040203
PS-MN6IK6Y0-S14	PS-MN6IK6Y0	14	Sprint 14	Integración con sistemas bancarios y seguridad	\N	\N	21	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:29.047519
PS-MN6IK6Y0-S15	PS-MN6IK6Y0	15	Sprint 15	Testing integral y documentación técnica	\N	\N	19	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:29.055491
PS-MN6IK6Y0-S16	PS-MN6IK6Y0	16	Sprint 16	Diseño y preparación de programas formativos	\N	\N	13	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:29.065788
PS-MN6IK6Y0-S17	PS-MN6IK6Y0	17	Sprint 17	Desarrollo de materiales y recursos formativos	\N	\N	21	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:29.071322
PS-MN6IK6Y0-S18	PS-MN6IK6Y0	18	Sprint 18	Ejecución de formaciones y capacitación	\N	\N	13	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:29.078795
PS-MN6IK6Y0-S19	PS-MN6IK6Y0	19	Sprint 19	Validación conocimientos y puesta en marcha	\N	\N	8	0	PLANIFICADO	[]	0	\N	2026-03-25 21:00:29.086579
PS-MN7E7EQZ-S1	PS-MN7E7EQZ	1	Sprint 1	Auditoría de infraestructura existente y análisis de requisitos	\N	\N	21	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.846575
PS-MN7E7EQZ-S2	PS-MN7E7EQZ	2	Sprint 2	Definición de arquitectura objetivo y requisitos técnicos	\N	\N	18	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.859698
PS-MN7E7EQZ-S3	PS-MN7E7EQZ	3	Sprint 3	Planificación detallada de implementación y recursos	\N	\N	16	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.866786
PS-MN7E7EQZ-S4	PS-MN7E7EQZ	4	Sprint 4	Validación de diseño y preparación para implementación	\N	\N	13	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.877142
PS-MN7E7EQZ-S5	PS-MN7E7EQZ	5	Sprint 5	Preparación de infraestructura base OpenShift	\N	\N	21	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.886122
PS-MN7E7EQZ-S6	PS-MN7E7EQZ	6	Sprint 6	Despliegue completo de clusters OpenShift	\N	\N	34	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.898059
PS-MN7E7EQZ-S7	PS-MN7E7EQZ	7	Sprint 7	Integración con sistemas existentes	\N	\N	21	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.908791
PS-MN7E7EQZ-S8	PS-MN7E7EQZ	8	Sprint 8	Optimización y hardening de seguridad	\N	\N	34	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.919977
PS-MN7E7EQZ-S9	PS-MN7E7EQZ	9	Sprint 9	Validación y testing de la plataforma	\N	\N	21	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.931897
PS-MN7E7EQZ-S10	PS-MN7E7EQZ	10	Sprint 10	Análisis y documentación de procesos actuales	\N	\N	13	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.94067
PS-MN7E7EQZ-S11	PS-MN7E7EQZ	11	Sprint 11	Diseño e implementación de procesos estandarizados	\N	\N	21	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.948783
PS-MN7E7EQZ-S12	PS-MN7E7EQZ	12	Sprint 12	Validación y documentación final de procesos	\N	\N	11	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.959766
PS-MN7E7EQZ-S13	PS-MN7E7EQZ	13	Sprint 13	Preparación de materiales de capacitación y evaluación de infraestructura	\N	\N	21	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.969254
PS-MN7E7EQZ-S14	PS-MN7E7EQZ	14	Sprint 14	Ejecución de capacitación y preparación del despliegue piloto	\N	\N	18	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.978528
PS-MN7E7EQZ-S15	PS-MN7E7EQZ	15	Sprint 15	Despliegue piloto y validación inicial	\N	\N	13	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.989216
PS-MN7E7EQZ-S16	PS-MN7E7EQZ	16	Sprint 16	Validación final y preparación para producción	\N	\N	8	0	PLANIFICADO	[]	0	\N	2026-03-26 18:59:13.997287
\.


ALTER TABLE public.build_sprints ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

\unrestrict ugdE4ZeLIBNxISGdjFctiY41hAscdEmlpxdbc7OMaFkxYlFe7BjmTlhMWQEhImg

