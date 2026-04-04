--
-- PostgreSQL database dump
--

\restrict pyardBsoQwEqElekWsvtul1sECNzOVqqAUpjWRyHqvudsCMIZP46WnwomHaNQyO

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
-- Data for Name: rbac_permisos; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.rbac_permisos DISABLE TRIGGER ALL;

COPY public.rbac_permisos (id_permiso, code, modulo, accion, descripcion, criticidad) FROM stdin;
1	dashboard.ver	dashboard	ver	Ver dashboard principal	BAJA
2	dashboard.ejecutivo	dashboard	ver	Ver dashboard ejecutivo con KPIs estratégicos	MEDIA
3	dashboard.exportar	dashboard	exportar	Exportar datos del dashboard	MEDIA
4	team.ver	team	ver	Ver listado de técnicos	BAJA
5	team.crear	team	crear	Crear nuevo técnico	ALTA
6	team.editar	team	editar	Editar datos de técnicos	ALTA
7	team.eliminar	team	eliminar	Eliminar técnico	CRITICA
8	team.asignar	team	ejecutar	Asignar técnico a incidencia/proyecto	ALTA
9	team.ver_salarios	team	ver	Ver información salarial (confidencial)	CRITICA
10	proyectos.ver	proyectos	ver	Ver cartera de proyectos	BAJA
11	proyectos.crear	proyectos	crear	Crear nuevo proyecto	ALTA
12	proyectos.editar	proyectos	editar	Editar proyecto existente	ALTA
13	proyectos.eliminar	proyectos	eliminar	Eliminar proyecto	CRITICA
14	proyectos.aprobar	proyectos	aprobar	Aprobar cambio de estado de proyecto	CRITICA
15	proyectos.pausar	proyectos	ejecutar	Pausar proyecto por riesgo P1	CRITICA
16	incidencias.ver	incidencias	ver	Ver incidencias	BAJA
17	incidencias.crear	incidencias	crear	Crear nueva incidencia	MEDIA
18	incidencias.editar	incidencias	editar	Editar incidencia	MEDIA
19	incidencias.eliminar	incidencias	eliminar	Eliminar incidencia	CRITICA
20	incidencias.escalar	incidencias	ejecutar	Escalar incidencia a nivel superior	ALTA
21	kanban.ver	kanban	ver	Ver tablero Kanban	BAJA
22	kanban.crear	kanban	crear	Crear tarea en Kanban	MEDIA
23	kanban.editar	kanban	editar	Editar/mover tarea en Kanban	MEDIA
24	kanban.eliminar	kanban	eliminar	Eliminar tarea de Kanban	ALTA
25	presupuestos.ver	presupuestos	ver	Ver presupuestos	MEDIA
26	presupuestos.crear	presupuestos	crear	Crear presupuesto	ALTA
27	presupuestos.editar	presupuestos	editar	Editar presupuesto	ALTA
28	presupuestos.eliminar	presupuestos	eliminar	Eliminar presupuesto	CRITICA
29	presupuestos.aprobar	presupuestos	aprobar	Aprobar presupuesto	CRITICA
30	presupuestos.ver_total	presupuestos	ver	Ver totales y desglose completo	ALTA
31	gobernanza.ver	gobernanza	ver	Ver scoring de gobernanza	MEDIA
32	gobernanza.editar	gobernanza	editar	Editar parámetros de gobernanza	ALTA
33	gobernanza.dashboard	gobernanza	ver	Ver dashboard de gobernanza	MEDIA
34	pmo.managers.ver	pmo	ver	Ver Project Managers	BAJA
35	pmo.managers.crear	pmo	crear	Crear Project Manager	ALTA
36	pmo.managers.editar	pmo	editar	Editar Project Manager	ALTA
37	warroom.ver	warroom	ver	Ver war room y sesiones	MEDIA
38	warroom.crear	warroom	crear	Iniciar sesión de war room	ALTA
39	warroom.participar	warroom	ejecutar	Participar en war room (enviar mensajes)	MEDIA
40	warroom.cerrar	warroom	ejecutar	Cerrar sesión de war room	ALTA
41	alertas.ver	alertas	ver	Ver alertas inteligentes	BAJA
42	alertas.crear	alertas	crear	Crear alerta	MEDIA
43	alertas.gestionar	alertas	editar	Acknowledge/resolver alertas	ALTA
44	compliance.ver	compliance	ver	Ver auditorías y compliance	MEDIA
45	compliance.crear	compliance	crear	Crear auditoría	ALTA
46	compliance.editar	compliance	editar	Editar auditoría	ALTA
47	compliance.dashboard	compliance	ver	Ver dashboard de compliance	MEDIA
48	postmortem.ver	postmortem	ver	Ver postmortems	MEDIA
49	postmortem.crear	postmortem	crear	Crear postmortem	MEDIA
50	postmortem.aprobar	postmortem	aprobar	Aprobar postmortem	ALTA
51	simulacion.ver	simulacion	ver	Ver simulaciones what-if	MEDIA
52	simulacion.ejecutar	simulacion	ejecutar	Ejecutar simulación	ALTA
53	documentacion.ver	documentacion	ver	Ver repositorio documental	BAJA
54	documentacion.crear	documentacion	crear	Crear documento	MEDIA
55	documentacion.editar	documentacion	editar	Editar documento	MEDIA
56	documentacion.eliminar	documentacion	eliminar	Eliminar documento	ALTA
57	planes.ver	planes	ver	Ver planes RUN y BUILD	BAJA
58	planes.crear	planes	crear	Crear plan	MEDIA
59	planes.eliminar	planes	eliminar	Eliminar plan	ALTA
60	agentes.ver	agentes	ver	Ver configuración de agentes IA	MEDIA
61	agentes.configurar	agentes	admin	Configurar chatflows de Flowise	CRITICA
62	agentes.chat	agentes	ejecutar	Interactuar con agentes IA	MEDIA
63	agentes.metricas	agentes	ver	Ver métricas de rendimiento de agentes	MEDIA
64	devtools.ver	devtools	ver	Ver herramientas de desarrollo	ALTA
65	devtools.sql	devtools	ejecutar	Ejecutar SQL directo	CRITICA
66	devtools.files	devtools	ver	Ver archivos del servidor	CRITICA
67	rbac.ver	rbac	ver	Ver configuración RBAC	ALTA
68	rbac.usuarios	rbac	admin	Gestionar usuarios del sistema	CRITICA
69	rbac.roles	rbac	admin	Gestionar roles y permisos	CRITICA
70	rbac.audit	rbac	ver	Ver log de auditoría	ALTA
71	directorio.ver	directorio	ver	Ver organigrama corporativo	BAJA
72	directorio.editar	directorio	editar	Editar directorio corporativo	CRITICA
73	prediccion.ver	prediccion	ver	Ver predicciones de demanda	MEDIA
74	catalogo.ver	catalogo	ver	Ver catálogos (skills, incidencias)	BAJA
75	catalogo.editar	catalogo	editar	Editar catálogos maestros	ALTA
76	cmdb.ver	cmdb	ver	Ver inventario CMDB, activos, VLANs, IPs	BAJA
77	cmdb.crear	cmdb	crear	Crear activos, VLANs, IPs, relaciones	ALTA
78	cmdb.editar	cmdb	editar	Editar activos, VLANs, IPs existentes	ALTA
79	cmdb.eliminar	cmdb	eliminar	Eliminar/retirar activos, VLANs, IPs	CRITICA
80	cmdb.costes.ver	cmdb	ver	Ver costes y presupuestos CMDB	MEDIA
81	cmdb.costes.crear	cmdb	crear	Crear entradas de costes CMDB	ALTA
82	cmdb.costes.editar	cmdb	editar	Editar costes CMDB	ALTA
83	cmdb.costes.eliminar	cmdb	eliminar	Eliminar costes CMDB	CRITICA
84	cmdb.compliance	cmdb	ver	Ver panel de compliance y salud CMDB	MEDIA
85	cmdb.impacto	cmdb	ejecutar	Ejecutar simulación de impacto en cascada	ALTA
86	cmdb.dependencias	cmdb	ver	Ver mapa de dependencias entre activos	MEDIA
87	cmdb.dependencias.editar	cmdb	editar	Crear/editar relaciones entre activos	ALTA
\.


ALTER TABLE public.rbac_permisos ENABLE TRIGGER ALL;

--
-- Name: rbac_permisos_id_permiso_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rbac_permisos_id_permiso_seq', 87, true);


--
-- PostgreSQL database dump complete
--

\unrestrict pyardBsoQwEqElekWsvtul1sECNzOVqqAUpjWRyHqvudsCMIZP46WnwomHaNQyO

