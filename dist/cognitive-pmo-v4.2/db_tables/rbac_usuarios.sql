--
-- PostgreSQL database dump
--

\restrict W3Er21KZKsCBRqSsGtUSjNuuvaz76slewSpLrEnhYiAexojtazrkREgaDvIz4qq

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
-- Data for Name: rbac_usuarios; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.rbac_usuarios DISABLE TRIGGER ALL;

COPY public.rbac_usuarios (id_usuario, email, password_hash, nombre_completo, avatar_url, id_role, id_recurso, id_pm, id_directivo, departamento, cargo, telefono, ultimo_login, login_count, activo, requiere_cambio_password, created_at, updated_at) FROM stdin;
2	alejandro.vidal@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Alejandro Vidal Montero	\N	2	\N	\N	DIR-001	Dirección General	CEO - Chief Executive Officer	\N	\N	0	t	t	2026-03-20 13:23:35.233471	2026-03-20 13:23:35.233471
4	roberto.navarro@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Roberto Navarro Sáenz	\N	4	\N	\N	DIR-003	Sistemas de Información	CIO - Chief Information Officer	\N	\N	0	t	t	2026-03-20 13:23:35.237843	2026-03-20 13:23:35.237843
5	elena.marquez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Elena Marquez Aguirre	\N	5	\N	\N	DIR-004	Ciberseguridad	CISO - Chief Information Security Officer	\N	\N	0	t	t	2026-03-20 13:23:35.24057	2026-03-20 13:23:35.24057
6	francisco.herrera@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Francisco Herrera Luna	\N	6	\N	\N	DIR-005	Finanzas	CFO - Chief Financial Officer	\N	\N	0	t	t	2026-03-20 13:23:35.242004	2026-03-20 13:23:35.242004
7	miguelangel.ruiz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Miguel Ángel Ruiz Portillo	\N	7	\N	\N	DIR-010	Ingeniería de Software	VP of Engineering	\N	\N	0	t	t	2026-03-20 13:23:35.244309	2026-03-20 13:23:35.244309
8	patricia.lopez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Patricia López de la Fuente	\N	8	\N	\N	DIR-011	Operaciones IT	VP of Operations (IT Ops)	\N	\N	0	t	t	2026-03-20 13:23:35.245376	2026-03-20 13:23:35.245376
9	gonzalo.fernandez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Gonzalo Fernández-Vega	\N	9	\N	\N	DIR-012	PMO Corporativa	VP of PMO	\N	\N	0	t	t	2026-03-20 13:23:35.247318	2026-03-20 13:23:35.247318
10	laura.sanz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Laura Sanz Bermejo	\N	10	\N	\N	DIR-020	Backend Engineering	Directora de Desarrollo Backend	\N	\N	0	t	t	2026-03-20 13:23:35.248254	2026-03-20 13:23:35.248254
11	sergio.morales@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Sergio Morales Pinto	\N	10	\N	\N	DIR-021	Frontend Engineering	Director de Desarrollo Frontend	\N	\N	0	t	t	2026-03-20 13:23:35.248254	2026-03-20 13:23:35.248254
12	natalia.campos@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Natalia Campos Rivero	\N	19	\N	\N	DIR-022	Quality Assurance	Directora de QA & Testing	\N	\N	0	t	t	2026-03-20 13:23:35.250452	2026-03-20 13:23:35.250452
13	javier.iglesias@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Javier Iglesias Roca	\N	12	\N	\N	DIR-023	Infraestructura	Director de Infraestructura & Redes	\N	\N	0	t	t	2026-03-20 13:23:35.251699	2026-03-20 13:23:35.251699
14	marta.fuentes@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Marta Fuentes Escobar	\N	11	\N	\N	DIR-024	Seguridad IT	Directora de Seguridad Operativa	\N	\N	0	t	t	2026-03-20 13:23:35.254027	2026-03-20 13:23:35.254027
15	oscar.blanco@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Óscar Blanco Heredia	\N	13	\N	\N	DIR-025	Data Engineering	Director de Datos & BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.255371	2026-03-20 13:23:35.255371
16	anabelen.gutierrez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Ana Belén Gutiérrez Palacios	\N	20	\N	\N	DIR-026	DevOps	Directora de DevOps & SRE	\N	\N	0	t	t	2026-03-20 13:23:35.257762	2026-03-20 13:23:35.257762
17	ricardo.soto@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Ricardo Soto Mendoza	\N	10	\N	\N	DIR-027	Soporte IT	Director de Soporte & Service Desk	\N	\N	0	t	t	2026-03-20 13:23:35.259275	2026-03-20 13:23:35.259275
18	beatriz.castano@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Beatriz Castaño Villar	\N	10	\N	\N	DIR-028	Sistemas Windows	Directora de Windows & Sistemas	\N	\N	0	t	t	2026-03-20 13:23:35.259275	2026-03-20 13:23:35.259275
19	pablo.rivas@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Pablo Rivas Camacho	\N	14	\N	\N	DIR-030	PMO - Infraestructura	Gerente de Proyecto - Infraestructura	\N	\N	0	t	t	2026-03-20 13:23:35.26171	2026-03-20 13:23:35.26171
20	cristina.vega@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Cristina Vega Salinas	\N	14	\N	\N	DIR-031	PMO - Aplicaciones	Gerente de Proyecto - Aplicaciones	\N	\N	0	t	t	2026-03-20 13:23:35.26171	2026-03-20 13:23:35.26171
21	daniel.prieto@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Daniel Prieto Gallardo	\N	14	\N	\N	DIR-032	PMO - Seguridad	Gerente de Proyecto - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.26171	2026-03-20 13:23:35.26171
22	lucia.romero@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Lucía Romero Ibarra	\N	14	\N	\N	DIR-033	PMO - Digital	Gerente de Proyecto - Digital	\N	\N	0	t	t	2026-03-20 13:23:35.26171	2026-03-20 13:23:35.26171
23	alberto.lozano@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Alberto Lozano Mejía	\N	10	\N	\N	DIR-034	NOC	Subdirector de NOC	\N	\N	0	t	t	2026-03-20 13:23:35.263372	2026-03-20 13:23:35.263372
24	ines.garciacano@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Inés García-Cano Duarte	\N	10	\N	\N	DIR-035	SOC	Subdirectora de SOC	\N	\N	0	t	t	2026-03-20 13:23:35.263372	2026-03-20 13:23:35.263372
25	marcos.morales@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Marcos Morales Guerrero	\N	16	\N	\N	DIR-040	Soporte IT	Jefe de Equipo - Soporte N1/N2	\N	\N	0	t	t	2026-03-20 13:23:35.265811	2026-03-20 13:23:35.265811
26	isabel.alvarez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Isabel Álvarez Calvo	\N	16	\N	\N	DIR-041	Redes	Jefa de Equipo - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.265811	2026-03-20 13:23:35.265811
27	olga.mendez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Olga Méndez Ramos	\N	16	\N	\N	DIR-042	DevOps	Jefa de Equipo - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.265811	2026-03-20 13:23:35.265811
28	marina.nieto@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Marina Nieto Calvo	\N	16	\N	\N	DIR-043	Backend Engineering	Jefa de Equipo - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.265811	2026-03-20 13:23:35.265811
29	raquel.sanchez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Raquel Sánchez Blanco	\N	16	\N	\N	DIR-044	Backend Engineering	Jefa de Equipo - Backend Senior	\N	\N	0	t	t	2026-03-20 13:23:35.265811	2026-03-20 13:23:35.265811
30	felipe.ortiz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Felipe Ortiz Cruz	\N	16	\N	\N	DIR-045	Soporte IT	Jefe de Equipo - Soporte N3/N4	\N	\N	0	t	t	2026-03-20 13:23:35.265811	2026-03-20 13:23:35.265811
31	tomas.soler@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Tomás Soler Ortega	\N	16	\N	\N	DIR-046	Soporte IT	Jefe de Equipo - Soporte Especializado	\N	\N	0	t	t	2026-03-20 13:23:35.265811	2026-03-20 13:23:35.265811
32	diana.sanchez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Diana Sánchez Alonso	\N	16	\N	\N	DIR-047	Seguridad IT	Jefa de Equipo - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.265811	2026-03-20 13:23:35.265811
3	carmen.delgado@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Carmen Delgado Ríos	\N	3	\N	\N	DIR-002	Tecnología	CTO - Chief Technology Officer	\N	2026-03-20 13:24:00.28218	1	t	t	2026-03-20 13:23:35.236216	2026-03-20 13:24:00.28218
33	sandra.ortega@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Sandra Ortega Torres	\N	17	FTE-002	\N	\N	Backend	Técnico N3 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
175	auditor.externo@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Auditor Externo - Deloitte	\N	21	\N	\N	\N	Auditoría Externa	Auditor de Sistemas	\N	\N	0	t	t	2026-03-20 13:23:35.282887	2026-03-20 13:23:35.282887
176	stakeholder@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Comité de Dirección	\N	22	\N	\N	\N	Dirección General	Stakeholder Ejecutivo	\N	\N	0	t	t	2026-03-20 13:23:35.284253	2026-03-20 13:23:35.284253
34	victor.garcia@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Víctor García Ramos	\N	17	FTE-009	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
35	ines.calvo@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Inés Calvo Iglesias	\N	17	FTE-020	\N	\N	Backend	Técnico N3 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
36	valentin.gutierrez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Valentín Gutiérrez Calvo	\N	17	FTE-015	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
37	teresa.diaz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Teresa Díaz Peña	\N	17	FTE-023	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
38	dario.perez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Darío Pérez Delgado	\N	17	FTE-027	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
39	teresa.gomez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Teresa Gómez Morales	\N	17	FTE-029	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
40	alfredo.castillo@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Alfredo Castillo Morales	\N	17	FTE-030	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
41	salvador.castro@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Salvador Castro Iglesias	\N	17	FTE-068	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
42	rosario.pena@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Rosario Peña Suárez	\N	17	FTE-048	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
43	laura.navarro@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Laura Navarro Aguilar	\N	17	FTE-056	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
44	ruben.perez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Rubén Pérez Castro	\N	17	FTE-053	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
45	tamara.pena@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Tamara Peña Fuentes	\N	17	FTE-058	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
46	pedro.flores@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Pedro Flores Suárez	\N	17	FTE-059	\N	\N	BBDD	Técnico N3 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
47	bruno.cabrera@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Bruno Cabrera Cruz	\N	17	FTE-060	\N	\N	Soporte	Técnico N4 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
48	luisa.blanco@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Luisa Blanco Muñoz	\N	17	FTE-072	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
49	marcel.campos@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Marcel Campos Nieto	\N	17	FTE-074	\N	\N	DevOps	Técnico N4 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
50	paco.ortiz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Paco Ortiz Díaz	\N	17	FTE-080	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
51	santiago.blanco@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Santiago Blanco Blanco	\N	17	FTE-077	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
52	eduardo.flores@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Eduardo Flores Martínez	\N	17	FTE-082	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
53	marta.calvo@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Marta Calvo García	\N	17	FTE-086	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
54	angel.morales@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Ángel Morales Pérez	\N	17	FTE-090	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
55	patricia.castillo@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Patricia Castillo Castro	\N	17	FTE-102	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
56	felipe.ibanez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Felipe Ibáñez Gómez	\N	17	FTE-096	\N	\N	Soporte	Técnico N4 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
57	barbara.reyes@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Bárbara Reyes Castillo	\N	17	FTE-104	\N	\N	BBDD	Técnico N3 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
58	valentin.morales@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Valentín Morales Jiménez	\N	17	FTE-107	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
59	fernando.martinez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Fernando Martínez Reyes	\N	17	FTE-105	\N	\N	Soporte	Técnico N4 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
60	wenceslao.garrido@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Wenceslao Garrido Rojas	\N	17	FTE-111	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
61	dolores.navarro@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Dolores Navarro Marín	\N	17	FTE-121	\N	\N	Frontend	Técnico N3 - Frontend	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
62	marina.diez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Marina Díez Ruiz	\N	17	FTE-122	\N	\N	Soporte	Técnico N4 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
63	blanca.mendez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Blanca Méndez Rodríguez	\N	17	FTE-128	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
64	jorge.diaz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Jorge Díaz Vázquez	\N	17	FTE-124	\N	\N	BBDD	Técnico N3 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
65	rosa.ramos@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Rosa Ramos Ramírez	\N	17	FTE-132	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
66	macarena.sanchez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Macarena Sánchez Ramírez	\N	17	FTE-133	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
67	lidia.lozano@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Lidia Lozano Iglesias	\N	17	FTE-140	\N	\N	BBDD	Técnico N3 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
68	manuela.ortega@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Manuela Ortega Caballero	\N	17	FTE-008	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
69	pedro.cabrera@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Pedro Cabrera Pérez	\N	17	FTE-085	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
70	felipe.iglesias@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Felipe Iglesias Cano	\N	17	FTE-141	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
71	marcel.serrano@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Marcel Serrano Iglesias	\N	17	FTE-079	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
72	veronica.arias@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Verónica Arias García	\N	17	FTE-050	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
73	sofia.rodriguez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Sofía Rodríguez Reyes	\N	17	FTE-014	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
74	elena.alvarez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Elena Álvarez Fuentes	\N	17	FTE-119	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
75	rafael.torres@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Rafael Torres Montero	\N	17	FTE-036	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
76	hugo.castro@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Hugo Castro Gil	\N	17	FTE-083	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
77	alfredo.moreno@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Alfredo Moreno Moreno	\N	17	FTE-054	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
78	manuela.parra@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Manuela Parra Bravo	\N	17	FTE-100	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
79	hugo.morales@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Hugo Morales Delgado	\N	17	FTE-005	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
80	lucia.marin@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Lucía Marín Torres	\N	17	FTE-032	\N	\N	Backend	Técnico N3 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
81	david.moya@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	David Moya Moreno	\N	17	FTE-099	\N	\N	DevOps	Técnico N3 - DevOps	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
82	sonia.castillo@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Sonia Castillo Marín	\N	17	FTE-101	\N	\N	Redes	Técnico N3 - Redes	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
83	tamara.martinez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Tamara Martínez Ruiz	\N	17	FTE-112	\N	\N	Soporte	Técnico N4 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
84	martin.crespo@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Martín Crespo Ortiz	\N	17	FTE-024	\N	\N	Backend	Técnico N3 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.267467	2026-03-20 13:23:35.267467
86	adriana.suarez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Adriana Suárez Flores	\N	18	FTE-007	\N	\N	Backend	Técnico N2 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
87	isabel.flores@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Isabel Flores Álvarez	\N	18	FTE-003	\N	\N	Soporte	Técnico N2 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
88	marcel.gonzalez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Marcel González Sánchez	\N	18	FTE-004	\N	\N	Frontend	Técnico N2 - Frontend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
89	marcel.guerrero@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Marcel Guerrero Iglesias	\N	18	FTE-010	\N	\N	Soporte	Técnico N2 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
90	ignacio.prieto@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Ignacio Prieto Cano	\N	18	FTE-013	\N	\N	Soporte	Técnico N2 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
91	gabriel.ruiz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Gabriel Ruiz Medina	\N	18	FTE-016	\N	\N	Backend	Técnico N2 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
92	gonzalo.esteban@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Gonzalo Esteban Blanco	\N	18	FTE-017	\N	\N	QA	Técnico N2 - QA	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
93	santiago.soler@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Santiago Soler Crespo	\N	18	FTE-033	\N	\N	Backend	Técnico N2 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
94	hector.prieto@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Héctor Prieto Molina	\N	18	FTE-022	\N	\N	QA	Técnico N2 - QA	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
95	sofia.parra@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Sofía Parra Fuentes	\N	18	FTE-034	\N	\N	Frontend	Técnico N2 - Frontend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
96	juan.ortiz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Juan Ortiz Ortega	\N	18	FTE-062	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
97	cristina.castillo@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Cristina Castillo Cabrera	\N	18	FTE-028	\N	\N	Soporte	Técnico N2 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
98	rocio.herrero@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Rocío Herrero Reyes	\N	18	FTE-031	\N	\N	Soporte	Técnico N2 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
99	blas.cabrera@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Blas Cabrera Méndez	\N	18	FTE-035	\N	\N	Soporte	Técnico N2 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
100	rene.alvarez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	René Álvarez Fernández	\N	18	FTE-037	\N	\N	Soporte	Técnico N2 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
101	jorge.vazquez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Jorge Vázquez Ramos	\N	18	FTE-038	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
102	alberta.munoz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Alberta Muñoz Díaz	\N	18	FTE-106	\N	\N	Backend	Técnico N2 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
103	pascual.arias@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Pascual Arias Rubio	\N	18	FTE-041	\N	\N	Soporte	Técnico N2 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
104	yolanda.martinez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Yolanda Martínez Alonso	\N	18	FTE-042	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
105	marcel.ibanez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Marcel Ibáñez Gómez	\N	18	FTE-039	\N	\N	Backend	Técnico N2 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
106	valentin.sanz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Valentín Sanz Guerrero	\N	18	FTE-043	\N	\N	Seguridad	Técnico N2 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
107	jorge.medina@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Jorge Medina Carrasco	\N	18	FTE-044	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
108	maria.reyes@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	María Reyes García	\N	18	FTE-045	\N	\N	Seguridad	Técnico N2 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
109	sofia.jimenez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Sofía Jiménez Ramírez	\N	18	FTE-046	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
110	rosario.romero@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Rosario Romero Garrido	\N	18	FTE-047	\N	\N	QA	Técnico N2 - QA	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
111	marcos.cruz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Marcos Cruz Ramos	\N	18	FTE-049	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
112	concha.vargas@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Concha Vargas López	\N	18	FTE-051	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
113	raul.gomez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Raúl Gómez Crespo	\N	18	FTE-055	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
114	xavier.gil@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Xavier Gil Marín	\N	18	FTE-057	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
115	monica.ruiz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Mónica Ruiz Muñoz	\N	18	FTE-081	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
116	raul.morales@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Raúl Morales Flores	\N	18	FTE-069	\N	\N	Seguridad	Técnico N2 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
117	yolanda.delgado@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Yolanda Delgado Benítez	\N	18	FTE-064	\N	\N	Seguridad	Técnico N2 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
118	rafael.garcia@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Rafael García Díaz	\N	18	FTE-065	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
119	eva.guerrero@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Eva Guerrero López	\N	18	FTE-063	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
120	enrique.delgado@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Enrique Delgado Gómez	\N	18	FTE-066	\N	\N	Backend	Técnico N2 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
121	cristina.lozano@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Cristina Lozano Díaz	\N	18	FTE-067	\N	\N	QA	Técnico N2 - QA	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
122	prudencio.ortiz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Prudencio Ortiz Aguilar	\N	18	FTE-071	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
123	valentin.caballero@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Valentín Caballero Torres	\N	18	FTE-078	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
124	lorenzo.guerrero@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Lorenzo Guerrero Romero	\N	18	FTE-076	\N	\N	Seguridad	Técnico N2 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
125	elena.munoz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Elena Muñoz Pérez	\N	18	FTE-075	\N	\N	QA	Técnico N2 - QA	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
126	joaquin.marin@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Joaquín Marín Reyes	\N	18	FTE-087	\N	\N	Soporte	Técnico N2 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
127	adrian.fuentes@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Adrián Fuentes Soler	\N	18	FTE-088	\N	\N	Frontend	Técnico N2 - Frontend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
128	luisa.vargas@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Luisa Vargas Pascual	\N	18	FTE-084	\N	\N	Seguridad	Técnico N2 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
129	raul.vazquez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Raúl Vázquez Blanco	\N	18	FTE-089	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
130	aurora.flores@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Aurora Flores Pérez	\N	18	FTE-091	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
131	tamara.ramos@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Tamara Ramos Pérez	\N	18	FTE-094	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
132	blas.pascual@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Blas Pascual Jiménez	\N	18	FTE-093	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
133	carla.perez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Carla Pérez Fernández	\N	18	FTE-092	\N	\N	Soporte	Técnico N2 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
134	rosa.cabrera@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Rosa Cabrera Gutiérrez	\N	18	FTE-097	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
135	sofia.herrero@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Sofía Herrero Navarro	\N	18	FTE-103	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
136	sofia.navarro@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Sofía Navarro Cano	\N	18	FTE-108	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
137	virginia.ramos@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Virginia Ramos Díez	\N	18	FTE-110	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
138	sofia.alonso@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Sofía Alonso Romero	\N	18	FTE-114	\N	\N	Frontend	Técnico N2 - Frontend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
139	yolanda.vazquez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Yolanda Vázquez Sanz	\N	18	FTE-115	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
140	virginia.pena@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Virginia Peña Molina	\N	18	FTE-116	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
141	margarita.soler@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Margarita Soler Martínez	\N	18	FTE-123	\N	\N	QA	Técnico N2 - QA	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
142	valentina.rodriguez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Valentina Rodríguez García	\N	18	FTE-120	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
143	rosario.vargas@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Rosario Vargas Rubio	\N	18	FTE-118	\N	\N	QA	Técnico N2 - QA	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
144	blas.ruiz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Blas Ruiz Domínguez	\N	18	FTE-126	\N	\N	Frontend	Técnico N2 - Frontend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
145	luisa.moya@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Luisa Moya Vázquez	\N	18	FTE-131	\N	\N	QA	Técnico N2 - QA	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
146	isabel.prieto@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Isabel Prieto Soler	\N	18	FTE-130	\N	\N	Seguridad	Técnico N2 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
147	gloria.molina@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Gloria Molina Ortiz	\N	18	FTE-129	\N	\N	QA	Técnico N2 - QA	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
148	mario.navarro@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Mario Navarro Rodríguez	\N	18	FTE-127	\N	\N	Backend	Técnico N2 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
149	teresa.ramos@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Teresa Ramos Romero	\N	18	FTE-135	\N	\N	Soporte	Técnico N2 - Soporte	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
150	federico.cortes@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Federico Cortés Delgado	\N	18	FTE-138	\N	\N	Frontend	Técnico N2 - Frontend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
151	mercedes.cano@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Mercedes Cano Castillo	\N	18	FTE-146	\N	\N	QA	Técnico N2 - QA	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
152	dolores.campos@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Dolores Campos Ortiz	\N	18	FTE-134	\N	\N	Frontend	Técnico N2 - Frontend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
153	sofia.gonzalez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Sofía González Romero	\N	18	FTE-145	\N	\N	Seguridad	Técnico N2 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
154	silvia.ramirez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Silvia Ramírez Parra	\N	18	FTE-144	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
155	jose.herrera@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	José Herrera Esteban	\N	18	FTE-148	\N	\N	Frontend	Técnico N2 - Frontend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
156	nuria.rubio@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Nuria Rubio Rodríguez	\N	18	FTE-149	\N	\N	Seguridad	Técnico N2 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
157	alvaro.moreno@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Álvaro Moreno Delgado	\N	18	FTE-019	\N	\N	Seguridad	Técnico N2 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
158	mercedes.garcia@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Mercedes García Durán	\N	18	FTE-150	\N	\N	Backend	Técnico N2 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
159	esther.molina@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Esther Molina Marín	\N	18	FTE-117	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
160	rut.moreno@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Rut Moreno Serrano	\N	18	FTE-095	\N	\N	Backend	Técnico N2 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
161	miriam.duran@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Miriam Durán Caballero	\N	18	FTE-061	\N	\N	Windows	Técnico N2 - Windows	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
162	jesus.calvo@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Jesús Calvo Ibáñez	\N	18	FTE-040	\N	\N	Backend	Técnico N2 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
163	alfredo.ortiz@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Alfredo Ortiz Parra	\N	18	FTE-098	\N	\N	Seguridad	Técnico N2 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
164	barbara.romero@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Bárbara Romero Torres	\N	18	FTE-113	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
165	wenceslao.gonzalez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Wenceslao González Cruz	\N	18	FTE-125	\N	\N	Frontend	Técnico N2 - Frontend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
166	leticia.esteban@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Leticia Esteban Esteban	\N	18	FTE-070	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
167	rafael.suarez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Rafael Suárez Reyes	\N	18	FTE-137	\N	\N	Seguridad	Técnico N2 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
168	felipe.rodriguez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Felipe Rodríguez Delgado	\N	18	FTE-018	\N	\N	Backend	Técnico N2 - Backend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
169	jorge.mendez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Jorge Méndez Cortés	\N	18	FTE-052	\N	\N	Seguridad	Técnico N2 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
170	ignacio.carrasco@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Ignacio Carrasco Prieto	\N	18	FTE-073	\N	\N	BBDD	Técnico N2 - BBDD	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
172	jaime.gonzalez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Jaime González Aguilar	\N	18	FTE-136	\N	\N	Frontend	Técnico N2 - Frontend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
173	rut.cabrera@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Rut Cabrera Crespo	\N	18	FTE-142	\N	\N	Seguridad	Técnico N1 - Seguridad	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
174	mercedes.pena@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Mercedes Peña Montero	\N	18	FTE-147	\N	\N	Frontend	Técnico N2 - Frontend	\N	\N	0	t	t	2026-03-20 13:23:35.275898	2026-03-20 13:23:35.275898
1	admin	8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918	Administrador del Sistema	\N	1	\N	\N	\N	IT - Plataforma	System Administrator	\N	2026-03-30 18:35:47.512104	36	t	f	2026-03-20 13:23:35.230933	2026-03-30 18:35:47.512104
171	jorge.sanchez@cognitivepmo.com	5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5	Jorge Sánchez Iglesias	\N	18	FTE-001	\N	\N	Backend	Técnico N2 - Backend	\N	2026-03-20 15:24:01.686188	3	t	t	2026-03-20 13:23:35.275898	2026-03-20 15:24:01.686188
\.


ALTER TABLE public.rbac_usuarios ENABLE TRIGGER ALL;

--
-- Name: rbac_usuarios_id_usuario_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rbac_usuarios_id_usuario_seq', 1008, true);


--
-- PostgreSQL database dump complete
--

\unrestrict W3Er21KZKsCBRqSsGtUSjNuuvaz76slewSpLrEnhYiAexojtazrkREgaDvIz4qq

