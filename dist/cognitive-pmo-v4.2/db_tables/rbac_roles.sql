--
-- PostgreSQL database dump
--

\restrict 7rFo6U21BedC0ZEtOZs8Bl0Zl79ztIqGVLqc1OU8Y2TxpJtduHdNVkLPrMKbzYS

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
-- Data for Name: rbac_roles; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.rbac_roles DISABLE TRIGGER ALL;

COPY public.rbac_roles (id_role, code, nombre, descripcion, nivel_jerarquico, color, icono, activo, created_at) FROM stdin;
1	SUPERADMIN	Super Administrador	Acceso total al sistema. Dios mode.	0	#EF4444	crown	t	2026-03-20 13:23:35.113914
2	CEO	Chief Executive Officer	Dirección general. Dashboard ejecutivo y reportes estratégicos.	1	#DC2626	building	t	2026-03-20 13:23:35.113914
3	CTO	Chief Technology Officer	Dirección tecnológica. Visión completa técnica y arquitectura.	1	#B91C1C	cpu	t	2026-03-20 13:23:35.113914
4	CIO	Chief Information Officer	Dirección de información. Gobernanza TI y compliance.	1	#991B1B	database	t	2026-03-20 13:23:35.113914
5	CISO	Chief Information Security Officer	Dirección de seguridad. Auditorías, compliance y war room.	1	#7F1D1D	shield-alert	t	2026-03-20 13:23:35.113914
6	CFO	Chief Financial Officer	Dirección financiera. Presupuestos y control de costes.	1	#F59E0B	banknote	t	2026-03-20 13:23:35.113914
7	VP_ENGINEERING	VP of Engineering	Vice Presidencia de Ingeniería. Gestión técnica global.	2	#8B5CF6	code	t	2026-03-20 13:23:35.113914
8	VP_OPERATIONS	VP of Operations	Vice Presidencia de Operaciones. RUN y disponibilidad.	2	#6366F1	activity	t	2026-03-20 13:23:35.113914
9	VP_PMO	VP of PMO	Vice Presidencia PMO. Gobernanza de proyectos y portfolio.	2	#4F46E5	briefcase	t	2026-03-20 13:23:35.113914
10	DIRECTOR_IT	Director de IT	Dirección departamental IT. Gestión de equipos y recursos.	3	#2563EB	monitor	t	2026-03-20 13:23:35.113914
11	DIRECTOR_SEC	Director de Seguridad	Dirección de ciberseguridad. Gestión de incidentes de seguridad.	3	#0891B2	shield	t	2026-03-20 13:23:35.113914
12	DIRECTOR_INFRA	Director de Infraestructura	Dirección de infraestructura y redes.	3	#0D9488	server	t	2026-03-20 13:23:35.113914
13	DIRECTOR_DATA	Director de Datos	Dirección de datos y BBDD.	3	#059669	hard-drive	t	2026-03-20 13:23:35.113914
14	PMO_SENIOR	PMO Senior / Program Manager	Gestión de programas. Gobernanza, presupuestos, riesgos.	4	#10B981	folder-kanban	t	2026-03-20 13:23:35.113914
15	PMO_JUNIOR	PMO Junior / Project Manager	Gestión de proyectos individuales. Kanban y seguimiento.	5	#34D399	clipboard-list	t	2026-03-20 13:23:35.113914
16	TEAM_LEAD	Team Lead / Jefe de Equipo	Líder técnico de silo. Gestión de equipo y asignaciones.	5	#06B6D4	users	t	2026-03-20 13:23:35.113914
17	TECH_SENIOR	Técnico Senior (N3-N4)	Técnico experto. Resolución avanzada e incidencias críticas.	6	#3B82F6	wrench	t	2026-03-20 13:23:35.113914
18	TECH_JUNIOR	Técnico Junior (N1-N2)	Técnico base. Operaciones y soporte estándar.	7	#60A5FA	tool	t	2026-03-20 13:23:35.113914
19	QA_LEAD	QA Lead	Líder de calidad. Testing, compliance y auditoría técnica.	5	#A855F7	check-circle	t	2026-03-20 13:23:35.113914
20	DEVOPS_LEAD	DevOps Lead	Líder DevOps. CI/CD, infraestructura como código.	5	#EC4899	git-branch	t	2026-03-20 13:23:35.113914
21	AUDITOR	Auditor / Compliance	Auditoría y cumplimiento. Solo lectura + reportes de compliance.	4	#F97316	file-search	t	2026-03-20 13:23:35.113914
22	OBSERVADOR	Observador / Stakeholder	Solo lectura. Dashboards y reportes ejecutivos.	8	#9CA3AF	eye	t	2026-03-20 13:23:35.113914
23	READONLY	Solo Lectura	Acceso mínimo de solo lectura a dashboards públicos.	9	#D1D5DB	lock	t	2026-03-20 13:23:35.113914
\.


ALTER TABLE public.rbac_roles ENABLE TRIGGER ALL;

--
-- Name: rbac_roles_id_role_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rbac_roles_id_role_seq', 23, true);


--
-- PostgreSQL database dump complete
--

\unrestrict 7rFo6U21BedC0ZEtOZs8Bl0Zl79ztIqGVLqc1OU8Y2TxpJtduHdNVkLPrMKbzYS

