--
-- PostgreSQL database dump
--

\restrict wYuKdbpRiGfM2F6agCUUqZtmk3H32gIrzwL2l7im5W1cnLOaUcvH8whzxBD6zJC

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
-- Data for Name: build_sprint_items; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.build_sprint_items DISABLE TRIGGER ALL;

COPY public.build_sprint_items (id, id_proyecto, id_sprint, sprint_number, item_key, tipo, titulo, descripcion, silo, prioridad, story_points, estado, id_tecnico, nombre_tecnico, subtareas_total, subtareas_completadas, id_tarea_padre, horas_estimadas, horas_reales, criterios_aceptacion, dod_checklist, bloqueador, orden_backlog, created_at) FROM stdin;
7ec78dec-9c47-4ec5-861e-3634024d8f2e	PS-MN6IK6Y0	PS-MN6IK6Y0-S1	1	PROJ-001	TASK	Inventario completo de infraestructura tecnológica actual	Auditar servidores, storage, red y aplicaciones existentes	Linux	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.955929
27faa3cc-f3b4-43f0-bd8f-b1b2f2d7d32f	PS-MN6IK6Y0	PS-MN6IK6Y0-S1	1	PROJ-002	SPIKE	Análisis de procesos operativos actuales	Documentar workflows, procedimientos y gaps identificados	PMO	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.958999
6e6727ba-e8fe-40d2-8de5-ed92a5003b30	PS-MN6IK6Y0	PS-MN6IK6Y0-S2	2	PROJ-003	STORY	Evaluación de capacidades técnicas del equipo	Assessment de skills actuales vs requeridos para OpenShift	RRHH	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.962858
36621fb6-2b50-4fbd-b79e-f94498c3c0d2	PS-MN6IK6Y0	PS-MN6IK6Y0-S2	2	PROJ-004	TASK	Diseño de arquitectura objetivo OpenShift	Definir topología, sizing y componentes de la plataforma	Arquitectura	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.964224
6be2ac75-2710-4e0c-9afa-d7767d8a3a5b	PS-MN6IK6Y0	PS-MN6IK6Y0-S2	2	PROJ-005	SPIKE	Análisis de impacto organizacional	Evaluar cambios necesarios en estructura y roles	PMO	Media	3	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.966675
0181c3df-ce08-4f3c-bbea-efc070be4349	PS-MN6IK6Y0	PS-MN6IK6Y0-S3	3	PROJ-006	STORY	Roadmap detallado de transformación tecnológica	Cronograma de migración y fases de implementación	PMO	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.970498
eaf1f179-9e5b-430a-917e-3fea8624fdf4	PS-MN6IK6Y0	PS-MN6IK6Y0-S3	3	PROJ-007	STORY	Plan de capacitación técnica especializada	Programa formativo OpenShift, Kubernetes y DevOps	RRHH	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.971928
d2c6d6fa-4ea6-4ab7-84fc-1b1fbb382bee	PS-MN6IK6Y0	PS-MN6IK6Y0-S3	3	PROJ-008	TASK	Definición de métricas y KPIs de éxito	Establecer indicadores para medir progreso y ROI	PMO	Media	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.974441
4e18674d-80bf-4c1d-8cde-4575cfa3490a	PS-MN6IK6Y0	PS-MN6IK6Y0-S4	4	PROJ-009	STORY	Validación técnica del diseño con stakeholders	Revisión y aprobación de arquitectura por comité técnico	Arquitectura	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.978196
e6bd592d-ef0b-4127-86d4-8d0cbfd7c8b2	PS-MN6IK6Y0	PS-MN6IK6Y0-S4	4	PROJ-010	TASK	Documentación final de análisis organizacional	Consolidar hallazgos, recomendaciones y plan aprobado	PMO	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.979487
5e8fb447-26f9-4adf-828f-b8a2b547ae89	PS-MN6IK6Y0	PS-MN6IK6Y0-S4	4	PROJ-011	TASK	Preparación para fase de implementación	Setup inicial para procesos PMBOK/ITIL en Fase 2	PMO	Media	3	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.981831
5c89c718-ae7f-4dc9-8b1f-7610da868078	PS-MN6IK6Y0	PS-MN6IK6Y0-S5	5	PROJ-012	TASK	Auditoría de procesos de gestión de proyectos existentes	Inventario completo de procesos actuales de gestión de proyectos	PMO	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.985482
6929d6ed-1082-4809-91f3-6ea60377b9d2	PS-MN6IK6Y0	PS-MN6IK6Y0-S5	5	PROJ-013	SPIKE	Identificación de gaps en metodología PMBOK	Análisis de brechas entre procesos actuales y estándares PMBOK	PMO	Alta	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.986755
360d8692-cd0e-4fed-b6e8-376b9e44f406	PS-MN6IK6Y0	PS-MN6IK6Y0-S5	5	PROJ-014	TASK	Documentación de procesos de inicio de proyectos	Mapeo detallado de procesos de iniciación según PMBOK	PMO	Media	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.989155
650de658-533d-47e8-90ff-5f12f6c27120	PS-MN6IK6Y0	PS-MN6IK6Y0-S6	6	PROJ-015	STORY	Diseño de procesos de planificación PMBOK	Definición de procesos optimizados de planificación de proyectos	PMO	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.993002
bd4da949-081d-42f7-9395-08732be69122	PS-MN6IK6Y0	PS-MN6IK6Y0-S6	6	PROJ-016	STORY	Definición de procesos de ejecución y control	Procesos de monitoreo y control según estándares PMBOK	PMO	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.99428
cfd219fe-c288-4792-ada5-b87a1b258357	PS-MN6IK6Y0	PS-MN6IK6Y0-S6	6	PROJ-017	TASK	Plantillas y formularios PMBOK	Creación de plantillas estándar para procesos PMBOK	PMO	Media	3	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:28.996558
a0870475-8313-488a-9844-ad3a07a74eed	PS-MN6IK6Y0	PS-MN6IK6Y0-S7	7	PROJ-018	TASK	Auditoría de procesos de gestión de servicios TI	Inventario de procesos actuales de gestión de servicios TI	Infraestructura	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.000013
7fd55602-9333-4679-98a6-1effc9586028	PS-MN6IK6Y0	PS-MN6IK6Y0-S7	7	PROJ-019	SPIKE	Identificación de gaps en framework ITIL	Análisis de brechas entre procesos actuales y estándares ITIL v4	Infraestructura	Alta	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.001221
ad262314-711b-4341-b8fa-91d6c969a86b	PS-MN6IK6Y0	PS-MN6IK6Y0-S7	7	PROJ-020	STORY	Diseño de procesos de gestión de incidentes ITIL	Definición de procesos optimizados de gestión de incidentes	Infraestructura	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.003995
9b23a238-0604-4e5c-a256-1d744b665914	PS-MN6IK6Y0	PS-MN6IK6Y0-S7	7	PROJ-021	STORY	Diseño de procesos de gestión de cambios ITIL	Procesos de control de cambios según ITIL v4	Infraestructura	Media	2	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.005277
19b301dd-6327-468d-b185-666feccf50af	PS-MN6IK6Y0	PS-MN6IK6Y0-S8	8	PROJ-022	TASK	Configuración de herramienta de gestión de servicios	Setup y configuración de ITSM tool para procesos ITIL	Infraestructura	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.008571
105ee6bb-cce3-42ce-a651-547804d31698	PS-MN6IK6Y0	PS-MN6IK6Y0-S8	8	PROJ-023	STORY	Implementación de catálogo de servicios	Definición e implementación del catálogo de servicios TI	Infraestructura	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.010917
108bb14c-974f-4d7d-bbdd-5593f334f147	PS-MN6IK6Y0	PS-MN6IK6Y0-S8	8	PROJ-024	TASK	Configuración de workflows ITIL	Automatización de workflows para incidentes y cambios	Infraestructura	Media	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.01218
8fc1cebe-95f3-42a8-a49a-52b20ec4aa0a	PS-MN6IK6Y0	PS-MN6IK6Y0-S9	9	PROJ-025	STORY	Integración de procesos PMBOK e ITIL	Alineación y sincronización entre procesos de proyectos y servicios	PMO	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.015713
2645a9c0-d159-4a58-8f16-02bc260e0e37	PS-MN6IK6Y0	PS-MN6IK6Y0-S9	9	PROJ-026	TASK	Documentación completa de procesos integrados	Manual de procesos PMBOK-ITIL integrados	PMO	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.018049
d3e5794d-d9b0-41dd-b747-268b4197982d	PS-MN6IK6Y0	PS-MN6IK6Y0-S9	9	PROJ-027	TASK	Definición de métricas y KPIs	Establecimiento de indicadores de rendimiento para procesos	PMO	Media	3	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.019348
66320fcb-98e3-4e9a-b602-c65f268fa3d4	PS-MN6IK6Y0	PS-MN6IK6Y0-S10	10	PROJ-028	TASK	Pruebas piloto de procesos PMBOK	Ejecución de pruebas piloto con proyectos reales	PMO	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.02276
4daf8c6d-0f0c-4c9d-bb6e-92d1351b7c74	PS-MN6IK6Y0	PS-MN6IK6Y0-S10	10	PROJ-029	TASK	Pruebas piloto de procesos ITIL	Validación de procesos ITIL en entorno controlado	Infraestructura	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.025045
69a0d83b-30ec-4bcb-8c88-54e67f84f1ee	PS-MN6IK6Y0	PS-MN6IK6Y0-S10	10	PROJ-030	TASK	Ajustes y optimizaciones finales	Refinamiento de procesos basado en resultados de pruebas	PMO	Media	3	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.026482
ea746149-ebff-4be9-9135-5a97dc41c345	PS-MN6IK6Y0	PS-MN6IK6Y0-S11	11	PROJ-031	TASK	Inventario completo de hardware disponible	Auditar servidores físicos y virtuales disponibles para OpenShift	Linux	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.029941
50f9f49e-205c-4dab-947e-d720e3e1cfdd	PS-MN6IK6Y0	PS-MN6IK6Y0-S11	11	PROJ-032	TASK	Análisis de capacidad de red existente	Evaluar ancho de banda y latencia para clusters distribuidos	Redes	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.03214
1659256f-7cce-4e73-910a-0c20e740acd5	PS-MN6IK6Y0	PS-MN6IK6Y0-S11	11	PROJ-033	SPIKE	Evaluación de almacenamiento compartido	Investigar opciones de storage para persistent volumes	Storage	Media	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.033299
9da609e7-8e0f-4c8a-8d0b-bb7c2b1ef116	PS-MN6IK6Y0	PS-MN6IK6Y0-S12	12	PROJ-034	TASK	Instalación cluster OpenShift master	Desplegar nodos master con alta disponibilidad	Linux	Crítica	13	TODO	\N	\N	6	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.036746
e380e037-220b-4e54-8ddb-bdb02a822f07	PS-MN6IK6Y0	PS-MN6IK6Y0-S12	12	PROJ-035	TASK	Configuración de red SDN	Implementar OpenShift SDN con políticas de red	Redes	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.039002
2a7d5a87-61c5-4ac1-8810-82f19ba74930	PS-MN6IK6Y0	PS-MN6IK6Y0-S13	13	PROJ-036	TASK	Configuración de registry interno	Desplegar registry de imágenes con almacenamiento persistente	Linux	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.042445
b7fb3e94-1c67-4ebe-8cee-868f262ffcd0	PS-MN6IK6Y0	PS-MN6IK6Y0-S13	13	PROJ-037	TASK	Implementación de storage classes	Configurar clases de almacenamiento dinámico	Storage	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.04386
b27f85d1-8aaa-4a01-a72b-bdd0db8a4d96	PS-MN6IK6Y0	PS-MN6IK6Y0-S13	13	PROJ-038	TASK	Setup de logging centralizado	Implementar ELK stack para logs de aplicaciones	Monitoring	Media	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.046127
f70e47fd-165b-46fe-bdbc-373d0c5c138d	PS-MN6IK6Y0	PS-MN6IK6Y0-S14	14	PROJ-039	TASK	Integración con Active Directory	Configurar LDAP/OAuth para autenticación corporativa	Seguridad	Crítica	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.049935
7fae1084-b5f9-498c-8be3-094ae3897ea4	PS-MN6IK6Y0	PS-MN6IK6Y0-S14	14	PROJ-040	TASK	Configuración de políticas de seguridad	Implementar Security Context Constraints y Network Policies	Seguridad	Crítica	8	TODO	\N	\N	5	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.051361
e08f971f-d4ca-4c60-a4bb-f20dea0e4695	PS-MN6IK6Y0	PS-MN6IK6Y0-S14	14	PROJ-041	TASK	Setup de monitorización con Prometheus	Desplegar stack de monitorización y alertas	Monitoring	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.053962
84af4fac-bc55-4a99-8ccd-36da297f3db3	PS-MN6IK6Y0	PS-MN6IK6Y0-S15	15	PROJ-042	TASK	Pruebas de carga y rendimiento	Ejecutar tests de stress en la plataforma completa	Testing	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.058155
eb9d15d4-94c0-441e-8962-ddd41f4211c8	PS-MN6IK6Y0	PS-MN6IK6Y0-S15	15	PROJ-043	TASK	Validación de backup y recovery	Probar procedimientos de respaldo y restauración	Storage	Crítica	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.059494
bef51757-5605-4730-9224-34d76f210c0c	PS-MN6IK6Y0	PS-MN6IK6Y0-S15	15	PROJ-044	STORY	Documentación técnica de arquitectura	Generar documentación completa de la plataforma	Documentación	Media	3	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.061733
ecee9baf-4e6e-4c45-beb8-ee751bb8705e	PS-MN6IK6Y0	PS-MN6IK6Y0-S15	15	PROJ-045	STORY	Runbook de operaciones	Crear guías operativas para el equipo de soporte	Documentación	Media	3	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.063016
b278cf37-3a0b-44d3-bee9-470d370749cd	PS-MN6IK6Y0	PS-MN6IK6Y0-S16	16	PROJ-046	TASK	Análisis de necesidades formativas por rol	Identificar gaps de conocimiento en equipos técnicos y de gestión	RRHH	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.067262
8de11ff6-aaf2-4125-aba2-b0e2dcf86dbb	PS-MN6IK6Y0	PS-MN6IK6Y0-S16	16	PROJ-047	STORY	Diseño curricular programa OpenShift	Crear contenidos formativos para administración de contenedores	Linux	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.069924
dc4d02a8-4acf-4b5d-8444-304782c92e01	PS-MN6IK6Y0	PS-MN6IK6Y0-S17	17	PROJ-048	TASK	Creación de laboratorios prácticos PMBOK	Desarrollar casos prácticos para metodologías de gestión	PMO	Alta	8	TODO	\N	\N	5	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.07356
fffea815-993a-4388-b1e7-46ecae97aaef	PS-MN6IK6Y0	PS-MN6IK6Y0-S17	17	PROJ-049	STORY	Documentación técnica ITIL v4	Adaptar procesos ITIL al contexto bancario específico	ITIL	Media	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.074763
fa02f8e3-abbc-4968-b1e3-14a8b55ac856	PS-MN6IK6Y0	PS-MN6IK6Y0-S17	17	PROJ-050	TASK	Configuración entorno formativo cloud	Preparar infraestructura de laboratorios en AWS/Azure	Cloud	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.077364
d0d74aa5-0b67-4716-b12c-0dd2ed6cd00a	PS-MN6IK6Y0	PS-MN6IK6Y0-S18	18	PROJ-051	STORY	Formación técnica equipos Linux/OpenShift	Sesiones hands-on para administradores de sistemas	Linux	Crítica	8	TODO	\N	\N	6	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.08126
bcae25c3-ff72-4d65-bd3b-434eced876fd	PS-MN6IK6Y0	PS-MN6IK6Y0-S18	18	PROJ-052	STORY	Workshop gestión de proyectos PMBOK	Capacitación en metodologías ágiles y tradicionales	PMO	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.083929
05b4f19a-44e4-4adb-a696-e5bc73baed5f	PS-MN6IK6Y0	PS-MN6IK6Y0-S19	19	PROJ-053	TASK	Evaluación competencias técnicas	Certificación de conocimientos adquiridos	QA	Alta	3	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.088063
9e85d6ee-7e83-4874-ab84-61781fbf0c22	PS-MN6IK6Y0	PS-MN6IK6Y0-S19	19	PROJ-054	STORY	Go-live asistido plataforma	Acompañamiento en primera puesta en producción	DevOps	Crítica	5	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-25 21:00:29.090389
cfac10b5-6299-411d-93ba-a6045cf96a7b	PS-MN7E7EQZ	PS-MN7E7EQZ-S1	1	PROJ-001	TASK	Inventario completo de hardware para clusters OpenShift	Consultar CMDB y realizar inventario físico de servidores disponibles	Linux	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.849506
638c3d91-a430-4e31-82a3-bd6f085178a5	PS-MN7E7EQZ	PS-MN7E7EQZ-S1	1	PROJ-002	TASK	Análisis de configuraciones de red actuales	Documentar topología de red y configuraciones existentes	Redes	Alta	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.854656
e13008d1-ea38-4a6f-a646-972492294bf5	PS-MN7E7EQZ	PS-MN7E7EQZ-S1	1	PROJ-003	TASK	Evaluación de sistemas de almacenamiento	Análisis de capacidad y rendimiento de storage actual	Storage	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.856631
30e356f3-a051-4973-9deb-3fd57eb734b2	PS-MN7E7EQZ	PS-MN7E7EQZ-S2	2	PROJ-004	STORY	Diseño de arquitectura de clusters OpenShift	Definir arquitectura de referencia para clusters OpenShift	Arquitectura	Alta	13	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.861631
29cd2938-f07f-4b27-906c-587ce0f7c7fe	PS-MN7E7EQZ	PS-MN7E7EQZ-S2	2	PROJ-005	TASK	Especificación de requisitos de red	Documentar requisitos de conectividad y seguridad de red	Redes	Media	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.864836
7136f852-9125-4d60-be25-d4e8c9cf23fa	PS-MN7E7EQZ	PS-MN7E7EQZ-S3	3	PROJ-006	STORY	Plan de implementación por fases	Crear cronograma detallado de implementación	PMO	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.869704
0488fb1a-0cf2-46f5-b036-62c5811f9185	PS-MN7E7EQZ	PS-MN7E7EQZ-S3	3	PROJ-007	SPIKE	Análisis de riesgos técnicos	Identificar y evaluar riesgos técnicos del proyecto	Arquitectura	Media	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.871732
722822bd-e887-4d0e-9890-055e23585f95	PS-MN7E7EQZ	PS-MN7E7EQZ-S3	3	PROJ-008	TASK	Definición de métricas y KPIs	Establecer métricas de éxito y monitoreo	Monitoreo	Media	3	TODO	\N	\N	1	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.874706
1583b2a4-c84e-40c4-ba89-4261355c0194	PS-MN7E7EQZ	PS-MN7E7EQZ-S4	4	PROJ-009	STORY	Revisión y validación de arquitectura	Validar diseño con stakeholders y ajustar según feedback	Arquitectura	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.880413
31e0660a-91f2-4188-a0fe-0c6a2c7459e5	PS-MN7E7EQZ	PS-MN7E7EQZ-S4	4	PROJ-010	TASK	Preparación de entorno de desarrollo	Configurar entorno inicial para pruebas de concepto	Linux	Media	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.882471
a51080fb-a024-44ab-8edd-2cf84cf32c7b	PS-MN7E7EQZ	PS-MN7E7EQZ-S5	5	PROJ-011	TASK	Inventario y validación de hardware para clusters	Auditoría completa de servidores disponibles en CMDB para OpenShift	Linux	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.88858
db588300-2bc5-4a63-8302-a7df28d77a7b	PS-MN7E7EQZ	PS-MN7E7EQZ-S5	5	PROJ-012	TASK	Configuración inicial de nodos master	Instalación y configuración base de nodos control plane	Linux	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.892166
de13714a-929f-462b-b49c-a3914bd12b75	PS-MN7E7EQZ	PS-MN7E7EQZ-S5	5	PROJ-013	SPIKE	Análisis de requisitos de red para clusters	Investigación de topología de red y VLANs necesarias	Redes	Media	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.894779
8ce4eb63-fde7-4778-a6c5-61ed9aca7921	PS-MN7E7EQZ	PS-MN7E7EQZ-S6	6	PROJ-014	TASK	Configuración de nodos worker	Despliegue y configuración de nodos de trabajo	Linux	Alta	13	TODO	\N	\N	5	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.900208
bdcb8329-697a-408a-b16a-d257c206acde	PS-MN7E7EQZ	PS-MN7E7EQZ-S6	6	PROJ-015	TASK	Implementación de networking SDN	Configuración de OpenShift SDN y políticas de red	Redes	Alta	13	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.903472
19e2d71d-8f4d-47b6-854d-b67cb30d11d0	PS-MN7E7EQZ	PS-MN7E7EQZ-S6	6	PROJ-016	TASK	Configuración de almacenamiento persistente	Setup de storage classes y persistent volumes	Storage	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.905331
e92de598-1f1e-4743-8810-a9d3ea37d18b	PS-MN7E7EQZ	PS-MN7E7EQZ-S7	7	PROJ-017	TASK	Integración con Active Directory	Configuración de autenticación LDAP con AD corporativo	Seguridad	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.91091
dbd5eebc-a3f0-46a4-8e5f-3994fd0858af	PS-MN7E7EQZ	PS-MN7E7EQZ-S7	7	PROJ-018	TASK	Configuración de monitoreo y logging	Implementación de Prometheus, Grafana y ELK stack	Monitoreo	Media	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.914397
f1bff05a-12ae-4c3d-b0e9-77edcbf14ea8	PS-MN7E7EQZ	PS-MN7E7EQZ-S7	7	PROJ-019	TASK	Setup de backup y disaster recovery	Configuración de políticas de backup para etcd y aplicaciones	Storage	Media	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.916703
f6ade472-458c-4ce5-b534-498926754cd2	PS-MN7E7EQZ	PS-MN7E7EQZ-S8	8	PROJ-020	TASK	Implementación de políticas de seguridad	Configuración de Security Context Constraints y Network Policies	Seguridad	Alta	13	TODO	\N	\N	5	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.922091
052953a0-aadd-4bb9-ae6a-a23471948c9e	PS-MN7E7EQZ	PS-MN7E7EQZ-S8	8	PROJ-021	TASK	Optimización de performance de clusters	Tuning de kernel y configuración de recursos	Linux	Media	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.92543
b788bbbb-a4ac-4b23-abab-eccd7f2f42b8	PS-MN7E7EQZ	PS-MN7E7EQZ-S8	8	PROJ-022	TASK	Configuración de certificados SSL/TLS	Implementación de certificados corporativos y rotación automática	Seguridad	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.92721
7e018af3-5b63-4c49-9334-8d75d7b42936	PS-MN7E7EQZ	PS-MN7E7EQZ-S8	8	PROJ-023	TASK	Setup de registry interno de imágenes	Configuración de registry privado para imágenes de contenedores	DevOps	Media	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.930025
9d0852f1-f43d-4840-832b-35df0c6ed691	PS-MN7E7EQZ	PS-MN7E7EQZ-S9	9	PROJ-024	TASK	Testing de alta disponibilidad	Pruebas de failover y recuperación de nodos	Testing	Alta	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.934607
fdae54be-268e-41b2-b1b5-3f1ff8137b46	PS-MN7E7EQZ	PS-MN7E7EQZ-S9	9	PROJ-025	TASK	Validación de performance y carga	Pruebas de stress y benchmarking de la plataforma	Testing	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.936205
a3dfd7ac-fe30-49ef-9713-9ad40f2ab131	PS-MN7E7EQZ	PS-MN7E7EQZ-S9	9	PROJ-026	TASK	Documentación técnica de implementación	Creación de runbooks y documentación de arquitectura	Documentación	Media	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.938867
dcd31ccc-0267-4a7b-ac47-06c5eb055559	PS-MN7E7EQZ	PS-MN7E7EQZ-S10	10	PROJ-027	TASK	Auditoría de procesos de infraestructura existentes	Documentar procesos actuales de gestión de infraestructura	Linux	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.943194
5bfe8f21-0afe-4c75-8014-481017b31158	PS-MN7E7EQZ	PS-MN7E7EQZ-S10	10	PROJ-028	TASK	Inventario de herramientas de monitoreo actuales	Catalogar herramientas de monitoreo en uso	Redes	Media	3	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.944741
4c96aee9-77ce-4f08-b4f1-253ee44d801e	PS-MN7E7EQZ	PS-MN7E7EQZ-S10	10	PROJ-029	SPIKE	Análisis de gaps en procedimientos operativos	Identificar brechas entre procesos actuales y mejores prácticas	Seguridad	Alta	5	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.947274
36c5403b-b810-4148-9179-4ebda61f609d	PS-MN7E7EQZ	PS-MN7E7EQZ-S11	11	PROJ-030	STORY	Diseño de procedimientos de backup estandarizados	Crear procedimientos estándar para backups en OpenShift	Linux	Alta	8	TODO	\N	\N	5	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.951924
24bec8f9-85e1-432f-9f12-fcaac2660090	PS-MN7E7EQZ	PS-MN7E7EQZ-S11	11	PROJ-031	TASK	Implementación de templates de monitoreo	Crear templates reutilizables para monitoreo de servicios	Redes	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.954322
ca3f9915-fe5b-4f4b-a4a2-a838c0acebb8	PS-MN7E7EQZ	PS-MN7E7EQZ-S11	11	PROJ-032	STORY	Estandarización de políticas de seguridad	Definir políticas de seguridad estándar para la plataforma	Seguridad	Alta	8	TODO	\N	\N	6	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.957755
0a269816-0ef7-447f-91c8-317295bccfe7	PS-MN7E7EQZ	PS-MN7E7EQZ-S12	12	PROJ-033	TASK	Testing de procedimientos automatizados	Validar funcionamiento de scripts y procedimientos automatizados	Linux	Alta	5	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.962691
a3d91511-aa05-4e7c-b6d7-4da2ca991e8a	PS-MN7E7EQZ	PS-MN7E7EQZ-S12	12	PROJ-034	STORY	Documentación de runbooks operativos	Crear runbooks para operaciones diarias	Redes	Media	3	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.964589
17f0fdbb-0928-4097-88e9-efa244973dbf	PS-MN7E7EQZ	PS-MN7E7EQZ-S12	12	PROJ-035	TASK	Validación de compliance y auditoría	Verificar cumplimiento de normativas bancarias	Seguridad	Alta	3	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.967414
1ed8a9f7-2f87-4900-81b4-3fc031a915df	PS-MN7E7EQZ	PS-MN7E7EQZ-S13	13	PROJ-036	TASK	Desarrollo de contenidos de capacitación técnica	Crear materiales formativos para OpenShift y herramientas DevOps	DevOps	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.97209
c9498516-e67d-4461-9b3f-4ff971c351fc	PS-MN7E7EQZ	PS-MN7E7EQZ-S13	13	PROJ-037	SPIKE	Evaluación de infraestructura para despliegue	Análisis de capacidad y readiness de la infraestructura objetivo	Linux	Alta	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.973769
69896123-0d8d-482c-9284-b692288239eb	PS-MN7E7EQZ	PS-MN7E7EQZ-S13	13	PROJ-038	TASK	Preparación de entornos de laboratorio	Configurar entornos de práctica para capacitación	Linux	Media	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.9765
42c4b857-cd52-4807-b16c-b4f2667528ac	PS-MN7E7EQZ	PS-MN7E7EQZ-S14	14	PROJ-039	STORY	Sesiones de capacitación técnica al equipo	Impartir formación práctica en OpenShift y metodologías DevOps	DevOps	Alta	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.981893
d8977378-583f-40ef-ae79-9cda030affdf	PS-MN7E7EQZ	PS-MN7E7EQZ-S14	14	PROJ-040	TASK	Configuración de entorno piloto	Preparar infraestructura para despliegue piloto inicial	Linux	Alta	8	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.983924
dbde5383-16c8-4c1b-ac62-8c672de4a61d	PS-MN7E7EQZ	PS-MN7E7EQZ-S14	14	PROJ-041	TASK	Validación de conocimientos adquiridos	Evaluación práctica de competencias del equipo capacitado	QA	Media	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.987177
52eaddd3-8644-4caf-9ed6-170ed416f21e	PS-MN7E7EQZ	PS-MN7E7EQZ-S15	15	PROJ-042	STORY	Ejecución de despliegue piloto	Implementar solución en entorno piloto con aplicaciones seleccionadas	DevOps	Crítica	8	TODO	\N	\N	4	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.992128
afac0d5d-a4d8-4ed6-ad93-f6f0dc3c501a	PS-MN7E7EQZ	PS-MN7E7EQZ-S15	15	PROJ-043	TASK	Monitoreo y métricas del piloto	Implementar dashboards y alertas para seguimiento del piloto	Monitoreo	Alta	5	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.993991
369c5fb2-b4ad-42e3-b4b4-6ed7e7b2a7ad	PS-MN7E7EQZ	PS-MN7E7EQZ-S16	16	PROJ-044	SPIKE	Análisis de resultados del piloto	Evaluación de métricas y lecciones aprendidas del despliegue piloto	QA	Alta	3	TODO	\N	\N	2	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:13.999219
7e8764ba-6d34-4743-a830-bfb0e085248e	PS-MN7E7EQZ	PS-MN7E7EQZ-S16	16	PROJ-045	TASK	Documentación final y plan de rollout	Crear documentación de producción y estrategia de despliegue masivo	DevOps	Alta	5	TODO	\N	\N	3	0	\N	0	0	[]	[]	\N	0	2026-03-26 18:59:14.002171
\.


ALTER TABLE public.build_sprint_items ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

\unrestrict wYuKdbpRiGfM2F6agCUUqZtmk3H32gIrzwL2l7im5W1cnLOaUcvH8whzxBD6zJC

