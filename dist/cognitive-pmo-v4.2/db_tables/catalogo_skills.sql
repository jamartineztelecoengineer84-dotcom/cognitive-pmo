--
-- PostgreSQL database dump
--

\restrict CRIyjAo8Y3ccHBzOkiRAv20zw9B51NajdAAZ2tlEjgnPXYz2Tr4PBw25kfLj5wE

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
-- Data for Name: catalogo_skills; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.catalogo_skills DISABLE TRIGGER ALL;

COPY public.catalogo_skills (id_skill, nombre_skill, categoria, silo) FROM stdin;
1	Git: Clonar repositorios	Git	Backend
2	Git: Crear ramas	Git	Backend
3	Git: Commits descriptivos	Git	Backend
4	Git: Resolver conflictos	Git	Backend
5	Git: Pull Requests	Git	Backend
6	Git: Rebase básico	Git	Backend
7	HTML: Semántica básica	HTML	Frontend
8	CSS: Flexbox	CSS	Frontend
9	CSS: Grid Layout	CSS	Frontend
10	CSS: Media Queries	CSS	Frontend
11	JS: Manipulación DOM	JS	Frontend
12	JS: Fetch / Axios	JS	Frontend
13	JS: Array Methods	JS	Frontend
14	JS: Async / Await	JS	Frontend
15	JS: Debugging	JS	Frontend
16	API: Códigos HTTP	API	Backend
17	API: Testing con Postman	API	Backend
18	API: Auth JWT	API	Backend
19	Backend: Crear Endpoint REST	Backend	Backend
20	Backend: Validar Inputs	Backend	Backend
21	Backend: Conexión a DB	Backend	Backend
22	Backend: Logging errores	Backend	Backend
23	Testing: Escribir Test Unitario	Testing	QA
24	Testing: Ejecutar Test Suite	Testing	QA
25	Linux: Navegación	Linux	DevOps
26	Linux: Gestión Archivos	Linux	DevOps
27	Linux: Ver contenido	Linux	DevOps
28	Linux: Búsqueda (grep)	Linux	DevOps
29	Linux: Permisos	Linux	DevOps
30	Linux: Procesos	Linux	DevOps
31	Linux: SSH Conexión	Linux	DevOps
32	Linux: SSH Keys	Linux	DevOps
33	Linux: Edición (Nano/Vim)	Linux	DevOps
34	Linux: Tareas (Crontab)	Linux	DevOps
35	Windows: Unir a Dominio	Windows	Windows
36	Windows: Gestión Servicios	Windows	Windows
37	Windows: Visor Eventos	Windows	Windows
38	Windows: RDP	Windows	Windows
39	Windows: PowerShell Básico	Windows	Windows
40	AD: Crear Usuario	AD	Windows
41	AD: Reset Password	AD	Windows
42	AD: Grupos Seguridad	AD	Windows
43	AD: Deshabilitar Usuario	AD	Windows
44	Redes: Crimpar RJ45	Redes	Redes
45	Redes: IP/Gateway	Redes	Redes
46	Redes: Ping	Redes	Redes
47	Redes: Tracert	Redes	Redes
48	Redes: Flush DNS	Redes	Redes
49	Redes: Netstat	Redes	Redes
50	Redes: IP Estática Config	Redes	Redes
51	Redes: DHCP Reserva	Redes	Redes
52	Redes: DNS Registros	Redes	Redes
53	Redes: VLAN Config Switch	Redes	Redes
54	Redes: Port Security	Redes	Redes
55	VPN: Configurar Cliente	VPN	Redes
56	WiFi: Diagnóstico Señal	WiFi	Redes
57	SQL: Select Simple	SQL	BBDD
58	SQL: Where	SQL	BBDD
59	SQL: Inner Join	SQL	BBDD
60	SQL: Left Join	SQL	BBDD
61	SQL: Insert Into	SQL	BBDD
62	SQL: Update	SQL	BBDD
63	SQL: Delete	SQL	BBDD
64	SQL: Backup DB	SQL	BBDD
65	SQL: Restore DB	SQL	BBDD
66	SQL: Create Table	SQL	BBDD
67	SQL: Alter Table	SQL	BBDD
68	Cloud: VM Start/Stop	Cloud	DevOps
69	Cloud: Crear Bucket	Cloud	DevOps
70	Cloud: Subir Archivos	Cloud	DevOps
71	Cloud: Security Groups	Cloud	DevOps
72	Docker: Run Container	Docker	DevOps
73	Docker: Listar	Docker	DevOps
74	Docker: Logs	Docker	DevOps
75	Docker: Exec	Docker	DevOps
76	Docker: Prune	Docker	DevOps
77	Seguridad: Phishing ID	Seguridad	Seguridad
78	Seguridad: Forzar Cambio Pass	Seguridad	Seguridad
79	Seguridad: Configurar MFA	Seguridad	Seguridad
80	Seguridad: Revisar Logs Acceso	Seguridad	Seguridad
81	Seguridad: Agente Antivirus	Seguridad	Seguridad
82	Seguridad: Nmap Scan	Seguridad	Seguridad
83	Seguridad: Bloqueo IP Firewall	Seguridad	Seguridad
84	Seguridad: Permisos Carpetas	Seguridad	Seguridad
85	Hardware: Instalar RAM	Hardware	Soporte
86	Hardware: Cambiar Disco	Hardware	Soporte
87	Hardware: Limpieza Interna	Hardware	Soporte
88	Hardware: Clonado Disco	Hardware	Soporte
89	Hardware: Impresora en Red	Hardware	Soporte
90	Hardware: Escáner a SMB	Hardware	Soporte
91	Hardware: Inventario Activos	Hardware	Soporte
92	Hardware: Diagnóstico Fuente	Hardware	Soporte
93	Doc: Escribir Documentación	Doc	Soporte
94	Ticket: Registro Incidencia	Ticket	Soporte
95	Ticket: Priorización	Ticket	Soporte
96	Ticket: Escalado Nivel	Ticket	Soporte
97	Agile: Daily Standup	Agile	Soporte
98	Agile: Estimación Tareas	Agile	Soporte
99	Idioma: Leer Inglés Técnico	Idioma	Soporte
100	Idioma: Email en Inglés	Idioma	Soporte
\.


ALTER TABLE public.catalogo_skills ENABLE TRIGGER ALL;

--
-- Name: catalogo_skills_id_skill_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.catalogo_skills_id_skill_seq', 181, true);


--
-- PostgreSQL database dump complete
--

\unrestrict CRIyjAo8Y3ccHBzOkiRAv20zw9B51NajdAAZ2tlEjgnPXYz2Tr4PBw25kfLj5wE

