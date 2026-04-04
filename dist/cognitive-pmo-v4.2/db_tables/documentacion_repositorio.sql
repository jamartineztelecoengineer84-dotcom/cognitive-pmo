--
-- PostgreSQL database dump
--

\restrict qA7zXlMPZ33GHzLeDvqKhDqih06UYDkXF1XnnnufR7GRLcNn2GlN4HOi3A56YzE

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
-- Data for Name: documentacion_repositorio; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.documentacion_repositorio DISABLE TRIGGER ALL;

COPY public.documentacion_repositorio (id, titulo, descripcion, tipo, silo, departamento, proyecto_id, incidencia_id, drive_file_id, drive_folder_path, drive_share_url, mime_type, archivo_nombre, archivo_size, archivo_tipo, tags, version, fecha_creacion, fecha_actualizacion, creado_por, activo) FROM stdin;
1	Plan de Proyecto — Red Infraestructura BCC	Plan completo PMBOK 7 para la implementación de la red del centro financiero BCC. Incluye Business Case, WBS, cronograma y análisis de riesgos.	proyecto	BUILD	IT_Architecture	PRJ0034	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/IT_Architecture	\N	application/pdf	Plan_de_Proyecto_-_Red_Infraestructura_B.pdf	2450000	pdf	{PMBOK,infraestructura,red}	1	2026-03-20 12:14:22.779733+00	2026-03-20 12:14:22.779733+00	Jose Antonio Martinez	t
2	Plan de Proyecto — Exadata Mission Critical	Documento de planificación para la implantación de Oracle Exadata como plataforma de BD mission-critical.	proyecto	BUILD	IT_Architecture	PRJ0006	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/IT_Architecture	\N	application/pdf	Plan_de_Proyecto_-_Exadata_Mission_Criti.pdf	3200000	pdf	{Oracle,Exadata,BBDD,mission-critical}	1	2026-03-20 12:14:22.78936+00	2026-03-20 12:14:22.78936+00	Jose Antonio Martinez	t
3	Plan de Proyecto — Clearpass NAC	Plan de renovación de la plataforma NAC con Aruba Clearpass para 120 oficinas.	proyecto	BUILD	IT_Architecture	PRJ0042	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/IT_Architecture	\N	application/pdf	Plan_de_Proyecto_-_Clearpass_NAC.pdf	1800000	pdf	{NAC,seguridad,Aruba,802.1X}	1	2026-03-20 12:14:22.797323+00	2026-03-20 12:14:22.797323+00	Jose Antonio Martinez	t
4	Diseño Técnico — Contenerización Docker/K8s	Documento de diseño técnico para la plataforma de contenerización con Docker y Kubernetes.	proyecto	BUILD	IT_Development	PRJ0046	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/IT_Development	\N	application/vnd.openxmlformats-officedocument.wordprocessingml.document	Diseño_Técnico_-_Contenerización_Docker/.docx	1500000	docx	{Docker,Kubernetes,DevOps,contenedores}	1	2026-03-20 12:14:22.806472+00	2026-03-20 12:14:22.806472+00	Jose Antonio Martinez	t
5	WBS Detallado — Modern Workplace	Estructura de desglose de trabajo completa para el proyecto de evolución del puesto de trabajo.	proyecto	BUILD	PMO_BUILD	PRJ0030	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/PMO_BUILD	\N	application/vnd.openxmlformats-officedocument.spreadsheetml.sheet	WBS_Detallado_-_Modern_Workplace.xlsx	450000	xlsx	{WBS,workplace,Microsoft}	1	2026-03-20 12:14:22.813471+00	2026-03-20 12:14:22.813471+00	Jose Antonio Martinez	t
6	Metodología de Gestión de Proyectos PMBOK 7	Guía metodológica corporativa basada en PMBOK 7 para la gestión de todos los proyectos BUILD.	gobernanza	BUILD	PMO_BUILD	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/PMO_BUILD	\N	application/pdf	Metodología_de_Gestión_de_Proyectos_PMBO.pdf	5400000	pdf	{PMBOK,metodología,estándar}	1	2026-03-20 12:14:22.822012+00	2026-03-20 12:14:22.822012+00	Jose Antonio Martinez	t
7	Plantilla — Acta de Constitución de Proyecto	Template estándar para el Acta de Constitución de nuevos proyectos conforme a PMBOK 7.	plantilla	BUILD	PMO_BUILD	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/PMO_BUILD	\N	application/vnd.openxmlformats-officedocument.wordprocessingml.document	Plantilla_-_Acta_de_Constitución_de_Proy.docx	120000	docx	{plantilla,acta,project-charter}	1	2026-03-20 12:14:22.828635+00	2026-03-20 12:14:22.828635+00	Jose Antonio Martinez	t
8	Plantilla — Registro de Riesgos	Plantilla para el registro y seguimiento de riesgos de proyecto con matriz de probabilidad/impacto.	plantilla	BUILD	PMO_BUILD	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/PMO_BUILD	\N	application/vnd.openxmlformats-officedocument.spreadsheetml.sheet	Plantilla_-_Registro_de_Riesgos.xlsx	85000	xlsx	{plantilla,riesgos,risk-register}	1	2026-03-20 12:14:22.83498+00	2026-03-20 12:14:22.83498+00	Jose Antonio Martinez	t
9	Guía de Scoring de Proyectos — ROI/Riesgo/Capacidad	Marco de puntuación para la evaluación y priorización de la demanda de proyectos.	gobernanza	BUILD	PMO_BUILD	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/PMO_BUILD	\N	application/pdf	Guía_de_Scoring_de_Proyectos_-_ROI/Riesg.pdf	980000	pdf	{scoring,priorización,ROI}	1	2026-03-20 12:14:22.840032+00	2026-03-20 12:14:22.840032+00	Jose Antonio Martinez	t
10	Runbook — Caída VPN SWIFT Alliance	Procedimiento operativo para la gestión de caídas del túnel VPN con SWIFT Alliance. Incluye pasos de diagnóstico y escalado.	incidencia	RUN	IT_Operations	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/IT_Operations	\N	application/pdf	Runbook_-_Caída_VPN_SWIFT_Alliance.pdf	650000	pdf	{runbook,VPN,SWIFT,P1}	1	2026-03-20 12:14:22.84584+00	2026-03-20 12:14:22.84584+00	Jose Antonio Martinez	t
11	Runbook — Caída masiva de Cajeros ATM	Procedimiento de emergencia para caídas masivas de la red de cajeros automáticos.	incidencia	RUN	IT_Support	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/IT_Support	\N	application/pdf	Runbook_-_Caída_masiva_de_Cajeros_ATM.pdf	420000	pdf	{runbook,ATM,cajeros,P1}	1	2026-03-20 12:14:22.85053+00	2026-03-20 12:14:22.85053+00	Jose Antonio Martinez	t
12	Post-Mortem — INC-2026-0839 VPN SWIFT	Informe post-mortem completo de la caída VPN SWIFT del 19/03/2026. Root cause: certificado IKEv2 expirado.	incidencia	RUN	IT_Operations	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/IT_Operations	\N	application/pdf	Post-Mortem_-_INC-2026-0839_VPN_SWIFT.pdf	380000	pdf	{post-mortem,VPN,SWIFT,lecciones}	1	2026-03-20 12:14:22.856402+00	2026-03-20 12:14:22.856402+00	Jose Antonio Martinez	t
13	Procedimiento de Escalado P1/P2	Procedimiento estándar ITIL 4 para el escalado de incidencias P1 y P2 con tiempos SLA.	incidencia	RUN	IT_Support	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/IT_Support	\N	application/pdf	Procedimiento_de_Escalado_P1/P2.pdf	290000	pdf	{escalado,P1,P2,SLA,ITIL}	1	2026-03-20 12:14:22.861332+00	2026-03-20 12:14:22.861332+00	Jose Antonio Martinez	t
14	Catálogo de SLAs por Servicio	Definición de los SLAs (Acuerdos de Nivel de Servicio) para cada servicio crítico del banco.	gobernanza	RUN	PMO_RUN	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/PMO_RUN	\N	application/vnd.openxmlformats-officedocument.spreadsheetml.sheet	Catálogo_de_SLAs_por_Servicio.xlsx	340000	xlsx	{SLA,ITIL,servicios}	1	2026-03-20 12:14:22.867371+00	2026-03-20 12:14:22.867371+00	Jose Antonio Martinez	t
15	Informe Compliance DORA Q1-2026	Informe trimestral de cumplimiento DORA con el estado de los tests de resiliencia operativa digital.	gobernanza	RUN	IT_Security	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/IT_Security	\N	application/pdf	Informe_Compliance_DORA_Q1-2026.pdf	1200000	pdf	{DORA,compliance,BCE,regulatorio}	1	2026-03-20 12:14:22.872397+00	2026-03-20 12:14:22.872397+00	Jose Antonio Martinez	t
16	Política de Gestión de Incidencias ITIL 4	Política corporativa de gestión de incidencias según el marco ITIL 4.	gobernanza	RUN	PMO_RUN	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/PMO_RUN	\N	application/pdf	Política_de_Gestión_de_Incidencias_ITIL_.pdf	780000	pdf	{ITIL,política,incidencias}	1	2026-03-20 12:14:22.878127+00	2026-03-20 12:14:22.878127+00	Jose Antonio Martinez	t
17	Manual de Onboarding — Nuevos Técnicos	Guía de incorporación para nuevos técnicos al equipo de IT. Incluye herramientas, accesos y procedimientos.	formacion	TRANSVERSAL	RRHH	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/RRHH	\N	application/pdf	Manual_de_Onboarding_-_Nuevos_Técnicos.pdf	1100000	pdf	{onboarding,formación,RRHH}	1	2026-03-20 12:14:22.883303+00	2026-03-20 12:14:22.883303+00	Jose Antonio Martinez	t
18	Guía de Seguridad — ISO 27001	Guía corporativa de controles de seguridad de la información conforme a ISO 27001.	gobernanza	TRANSVERSAL	Compliance	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/Compliance	\N	application/pdf	Guía_de_Seguridad_-_ISO_27001.pdf	2800000	pdf	{ISO27001,seguridad,normativa}	1	2026-03-20 12:14:22.889267+00	2026-03-20 12:14:22.889267+00	Jose Antonio Martinez	t
19	Manual de Herramientas — Stack Tecnológico	Catálogo de herramientas tecnológicas aprobadas para uso en proyectos y operaciones.	herramienta	TRANSVERSAL	Gobernanza_General	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/Gobernanza_General	\N	application/pdf	Manual_de_Herramientas_-_Stack_Tecnológi.pdf	560000	pdf	{herramientas,stack,tecnología}	1	2026-03-20 12:14:22.894307+00	2026-03-20 12:14:22.894307+00	Jose Antonio Martinez	t
20	Plan de Formación Continua 2026	Plan anual de formación y certificación para todo el equipo técnico. Incluye Red Hat, AWS, PMP, ITIL.	formacion	TRANSVERSAL	Formacion	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/Formacion	\N	application/vnd.openxmlformats-officedocument.spreadsheetml.sheet	Plan_de_Formación_Continua_2026.xlsx	230000	xlsx	{formación,plan,certificaciones}	1	2026-03-20 12:14:22.90448+00	2026-03-20 12:14:22.90448+00	Jose Antonio Martinez	t
21	Plantilla — Informe Ejecutivo Mensual	Template para el informe mensual de estado dirigido al Comité de Dirección.	plantilla	TRANSVERSAL	Gobernanza_General	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/Gobernanza_General	\N	application/vnd.ms-powerpoint	Plantilla_-_Informe_Ejecutivo_Mensual.pptx	1400000	pptx	{plantilla,informe,ejecutivo}	1	2026-03-20 12:14:22.912268+00	2026-03-20 12:14:22.912268+00	Jose Antonio Martinez	t
22	Política GDPR — Protección de Datos	Política corporativa de protección de datos personales conforme al RGPD y LOPD-GDD.	gobernanza	TRANSVERSAL	Legal	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/Legal	\N	application/pdf	Política_GDPR_-_Protección_de_Datos.pdf	920000	pdf	{GDPR,LOPD,datos,privacidad}	1	2026-03-20 12:14:22.919737+00	2026-03-20 12:14:22.919737+00	Jose Antonio Martinez	t
23	Guía PCI DSS — Requisitos de Seguridad	Guía de cumplimiento PCI DSS para todos los sistemas que procesan datos de tarjetas de pago.	gobernanza	TRANSVERSAL	Compliance	\N	\N	\N	CognitivePMO_Documentacion/{'01_BUILD' if doc.silo=='BUILD' else '02_RUN' if doc.silo=='RUN' else '03_TRANSVERSAL'}/Compliance	\N	application/pdf	Guía_PCI_DSS_-_Requisitos_de_Seguridad.pdf	1650000	pdf	{PCI-DSS,pagos,seguridad,tarjetas}	1	2026-03-20 12:14:22.926742+00	2026-03-20 12:14:22.926742+00	Jose Antonio Martinez	t
\.


ALTER TABLE public.documentacion_repositorio ENABLE TRIGGER ALL;

--
-- Name: documentacion_repositorio_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.documentacion_repositorio_id_seq', 23, true);


--
-- PostgreSQL database dump complete
--

\unrestrict qA7zXlMPZ33GHzLeDvqKhDqih06UYDkXF1XnnnufR7GRLcNn2GlN4HOi3A56YzE

