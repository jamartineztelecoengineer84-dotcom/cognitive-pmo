--
-- PostgreSQL database dump
--

\restrict LT4zdOdQiU8FmfkeuXb4KbhgPCyhqiN9io2JS5TUkbIPcsfE49qABCWwriHeNRt

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
-- Data for Name: pmo_project_managers; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.pmo_project_managers DISABLE TRIGGER ALL;

COPY public.pmo_project_managers (id_pm, nombre, nivel, especialidad, skills_json, skill_principal, total_skills, estado, max_proyectos, email, telefono, certificaciones, fecha_alta, scoring_promedio, proyectos_completados, proyectos_activos, tasa_exito, carga_actual, created_at) FROM stdin;
PM-002	Miguel Ángel Torres López	PM-Lead	Infraestructura	["Gestión de Infraestructura IT", "Planificación de Capacidad", "ITIL Service Management", "Gestión de Proveedores HW", "Disaster Recovery Planning", "Virtualización y Cloud"]	Gestión de Infraestructura IT	6	ASIGNADO	4	miguel.angel@bcc-bank.es	+34 615675482	{PMP,"ITIL v4",TOGAF,COBIT}	2026-03-20	8.40	0	4	94.20	100	2026-03-20 09:13:39.945142+00
PM-004	Roberto Martín Sánchez	PM-Lead	Aplicaciones	["Gestión de Desarrollo SW", "Agile/Scrum Mastery", "DevOps Pipeline Management", "API Strategy", "Microservicios Architecture", "Quality Assurance"]	Gestión de Desarrollo SW	6	ASIGNADO	4	roberto.martin@bcc-bank.es	+34 612191002	{PMP,"Scrum Master","SAFe Agilist",PMI-ACP}	2026-03-20	8.80	0	3	91.30	75	2026-03-20 09:13:39.965452+00
PM-005	Ana Belén García Moreno	PM-Sr	Data & Analytics	["Data Governance", "BI & Analytics Strategy", "Data Migration Planning", "Machine Learning Ops", "Data Quality Management", "ETL Architecture"]	Data Governance	6	SOBRECARGADO	3	ana.belen@bcc-bank.es	+34 681796440	{PMP,"ITIL v4","Six Sigma GB"}	2026-03-20	7.70	0	4	93.50	133	2026-03-20 09:13:39.975551+00
PM-006	Francisco Javier Ruiz Ortega	PM-Sr	Transformación Digital	["Digital Strategy", "Cloud Transformation", "Process Automation", "Innovation Management", "Vendor Management", "Business Case Development"]	Digital Strategy	6	ASIGNADO	3	francisco.javier@bcc-bank.es	+34 641121274	{PMP,PRINCE2,"AWS Solutions Architect"}	2026-03-20	7.00	0	1	89.70	33	2026-03-20 09:13:39.988514+00
PM-007	Laura Fernández Castro	PM-Sr	Infraestructura	["Gestión de Infraestructura IT", "Planificación de Capacidad", "ITIL Service Management", "Gestión de Proveedores HW", "Disaster Recovery Planning", "Virtualización y Cloud"]	Gestión de Infraestructura IT	6	ASIGNADO	3	laura.fernandez@bcc-bank.es	+34 651743309	{PMP,"ITIL v4",PRINCE2}	2026-03-20	8.30	0	3	95.10	100	2026-03-20 09:13:40.001422+00
PM-008	David Sánchez Herrera	PM-Sr	Aplicaciones	["Gestión de Desarrollo SW", "Agile/Scrum Mastery", "DevOps Pipeline Management", "API Strategy", "Microservicios Architecture", "Quality Assurance"]	Gestión de Desarrollo SW	6	ASIGNADO	3	david.sanchez@bcc-bank.es	+34 627849943	{"Scrum Master",PMI-ACP,"SAFe Agilist"}	2026-03-20	7.00	0	2	88.40	66	2026-03-20 09:13:40.013814+00
PM-009	María José López Díaz	PM-Sr	Gobernanza	["Portfolio Management", "Demand Management", "Resource Capacity Planning", "Change Management", "Benefits Realization", "Stakeholder Management"]	Portfolio Management	6	DISPONIBLE	3	maria.jose@bcc-bank.es	+34 689022921	{PMP,PRINCE2,"Lean IT",COBIT}	2026-03-20	6.80	0	0	92.60	0	2026-03-20 09:13:40.027317+00
PM-010	Carlos Alberto Pérez Molina	PM-Sr	Seguridad	["Gestión de Riesgos Ciber", "Compliance Regulatorio", "ISO 27001 Lead", "GDPR/LOPD Implementation", "Security Architecture", "Incident Response Planning"]	Gestión de Riesgos Ciber	6	ASIGNADO	3	carlos.alberto@bcc-bank.es	+34 698574148	{PMP,"ISO 27001 LA","DORA Specialist"}	2026-03-20	8.80	0	2	96.00	66	2026-03-20 09:13:40.037743+00
PM-011	Isabel Moreno Gutiérrez	PM-Jr	Infraestructura	["Gestión de Infraestructura IT", "Planificación de Capacidad", "ITIL Service Management", "Gestión de Proveedores HW", "Disaster Recovery Planning", "Virtualización y Cloud"]	Gestión de Infraestructura IT	6	SOBRECARGADO	2	isabel.moreno@bcc-bank.es	+34 647853224	{PRINCE2,"ITIL v4"}	2026-03-20	7.80	0	10	85.00	200	2026-03-20 09:13:40.049261+00
PM-012	Alejandro Navarro Blanco	PM-Jr	Aplicaciones	["Gestión de Desarrollo SW", "Agile/Scrum Mastery", "DevOps Pipeline Management", "API Strategy", "Microservicios Architecture", "Quality Assurance"]	Gestión de Desarrollo SW	6	SOBRECARGADO	2	alejandro.navarro@bcc-bank.es	+34 672186377	{"Scrum Master",PMI-ACP}	2026-03-20	8.90	0	4	82.50	200	2026-03-20 09:13:40.061979+00
PM-013	Sofía Martínez Ramos	PM-Jr	Data & Analytics	["Data Governance", "BI & Analytics Strategy", "Data Migration Planning", "Machine Learning Ops", "Data Quality Management", "ETL Architecture"]	Data Governance	6	SOBRECARGADO	2	sofia.martinez@bcc-bank.es	+34 688202110	{PMP}	2026-03-20	7.70	0	5	87.30	200	2026-03-20 09:13:40.075268+00
PM-015	Patricia Vázquez Luna	PM-Sr	Gobernanza	["Portfolio Management", "Demand Management", "Resource Capacity Planning", "Change Management", "Benefits Realization", "Stakeholder Management"]	Portfolio Management	6	DISPONIBLE	3	patricia.vazquez@bcc-bank.es	+34 639314914	{PMP,PRINCE2,"Six Sigma BB",TOGAF}	2026-03-20	6.60	0	0	94.80	0	2026-03-20 09:13:40.103203+00
PM-014	Raúl Gómez Serrano	PM-Jr	Transformación Digital	["Digital Strategy", "Cloud Transformation", "Process Automation", "Innovation Management", "Vendor Management", "Business Case Development"]	Digital Strategy	6	VACACIONES	2	raul.gomez@bcc-bank.es	+34 666323212	{PRINCE2,"Scrum Master"}	2026-03-20	6.40	0	2	84.10	100	2026-03-20 09:13:40.088811+00
PM-003	Carmen Jiménez Navarro	PM-Lead	Seguridad	[]	\N	0	SOBRECARGADO	4	carmen.jimenez@bcc-bank.es	+34 679738661	{PMP,"ISO 27001 LA",CRISC,CISM}	2026-03-20	7.40	0	5	97.80	125	2026-03-20 09:13:39.954842+00
PM-001	Elena Rodríguez Vega	PM-Dir	Gobernanza	["Liderazgo de Equipos", "Visión Estratégica", "Gestión Presupuestaria", "Change Management", "Reporting & Dashboards", "Gestión de Riesgos"]	\N	6	ASIGNADO	5	elena.rodriguez@bcc-bank.es	+34 636050594	{PMP,PRINCE2,PMI-ACP,TOGAF,"SAFe Agilist"}	2026-03-20	6.20	0	1	96.50	20	2026-03-20 09:13:39.924462+00
\.


ALTER TABLE public.pmo_project_managers ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

\unrestrict LT4zdOdQiU8FmfkeuXb4KbhgPCyhqiN9io2JS5TUkbIPcsfE49qABCWwriHeNRt

