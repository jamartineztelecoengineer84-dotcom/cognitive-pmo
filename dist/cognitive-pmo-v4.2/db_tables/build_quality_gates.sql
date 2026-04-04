--
-- PostgreSQL database dump
--

\restrict f5xocJiOG84lwsucJSCBhlzwMm50Qmq8dszrVbYebjjlgaeXZbbvYScTyOy1HgL

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
-- Data for Name: build_quality_gates; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.build_quality_gates DISABLE TRIGGER ALL;

COPY public.build_quality_gates (id, id_proyecto, fase, gate_name, criterios_json, checklist_json, dod_json, responsable_qa, estado, fecha_revision, notas, created_at) FROM stdin;
350fa7fe-97f2-457d-bbc4-59325d412523	openshift-platform-2026	G0	Gate Idea	["Business Case aprobado", "Presupuesto orientativo", "Sponsor identificado"]	["Formulario Business Case completo", "Prioridad asignada"]	[]	\N	PENDING	\N	\N	2026-03-23 12:54:07.050541
54f78a31-9f76-48d6-a76b-400373d539bd	openshift-platform-2026	G1	Gate Inicio	["Acta Constitución firmada", "EDT/WBS aprobado", "Equipo formado"]	["Objetivos SMART definidos", "Alcance documentado", "PM asignado"]	[]	\N	PENDING	\N	\N	2026-03-23 12:54:07.062973
13c7134d-83eb-4dd7-9530-a4f4f863d144	openshift-platform-2026	G2	Gate Planificación	["Presupuesto aprobado", "Gantt baseline", "Riesgos aceptados", "Kickoff realizado"]	["BAC definitivo", "Sprints planificados", "DoD por tarea", "Stakeholders notificados"]	[]	\N	PENDING	\N	\N	2026-03-23 12:54:07.067159
e39bf640-d736-43e3-948a-e7c4b39332b2	openshift-platform-2026	G3	Gate Ejecución	["Sprint Review OK", "CPI > 0.9", "SPI > 0.85", "Sin P1 abiertos"]	["Demo a stakeholders", "Retrospectiva completada", "Riesgos actualizados"]	[]	\N	PENDING	\N	\N	2026-03-23 12:54:07.071286
5e28d4bc-2754-4d9a-9425-5918a489fd67	openshift-platform-2026	G4	Gate Cierre	["Todos los entregables aceptados", "Decommission completado", "Lecciones aprendidas"]	["Acta de cierre firmada", "Postmortem escrito", "Recursos liberados"]	[]	\N	PENDING	\N	\N	2026-03-23 12:54:07.076086
62aa8a77-ea64-4332-b0f4-7d938781ee00	openshift-platform-2026	G5	Gate Beneficios	["ROI verificado a 6 meses", "KPIs objetivo cumplidos"]	["Informe de beneficios", "Comparación BAC vs AC final"]	[]	\N	PENDING	\N	\N	2026-03-23 12:54:07.079857
f4ab4ac2-afed-467e-accf-c7643e97bf3c	PROJ-OPENSHIFT-001	G0	Gate Idea	["Business Case aprobado", "Presupuesto orientativo", "Sponsor identificado"]	["Formulario Business Case completo", "Prioridad asignada"]	[]	\N	PENDING	\N	\N	2026-03-23 22:59:36.905757
bf6f09a3-285f-4513-89b8-7e7058ef1d62	PROJ-OPENSHIFT-001	G1	Gate Inicio	["Acta Constitución firmada", "EDT/WBS aprobado", "Equipo formado"]	["Objetivos SMART definidos", "Alcance documentado", "PM asignado"]	[]	\N	PENDING	\N	\N	2026-03-23 22:59:36.913732
12e09fd6-9bdd-4a7c-a2ea-ac88ff447687	PROJ-OPENSHIFT-001	G2	Gate Planificación	["Presupuesto aprobado", "Gantt baseline", "Riesgos aceptados", "Kickoff realizado"]	["BAC definitivo", "Sprints planificados", "DoD por tarea", "Stakeholders notificados"]	[]	\N	PENDING	\N	\N	2026-03-23 22:59:36.918469
c95e2ad4-dd0e-4662-a218-a4a702604fcb	PROJ-OPENSHIFT-001	G3	Gate Ejecución	["Sprint Review OK", "CPI > 0.9", "SPI > 0.85", "Sin P1 abiertos"]	["Demo a stakeholders", "Retrospectiva completada", "Riesgos actualizados"]	[]	\N	PENDING	\N	\N	2026-03-23 22:59:36.921672
38d82f28-01d9-489e-a9d5-d4d42888ba0f	PROJ-OPENSHIFT-001	G4	Gate Cierre	["Todos los entregables aceptados", "Decommission completado", "Lecciones aprendidas"]	["Acta de cierre firmada", "Postmortem escrito", "Recursos liberados"]	[]	\N	PENDING	\N	\N	2026-03-23 22:59:36.926476
4ac1ef91-2fd3-494b-a0f9-f2708f26ad53	PROJ-OPENSHIFT-001	G5	Gate Beneficios	["ROI verificado a 6 meses", "KPIs objetivo cumplidos"]	["Informe de beneficios", "Comparación BAC vs AC final"]	[]	\N	PENDING	\N	\N	2026-03-23 22:59:36.929981
b2e3840e-2d90-48c5-b316-7a2186b8375f	Plataforma-OpenShift-OnPremise	G0	Gate Idea	["Business Case aprobado", "Presupuesto orientativo", "Sponsor identificado"]	["Formulario Business Case completo", "Prioridad asignada"]	[]	\N	PENDING	\N	\N	2026-03-24 10:11:27.800278
7bc1e0df-7e03-49b3-ac6f-257026cf9e92	Plataforma-OpenShift-OnPremise	G1	Gate Inicio	["Acta Constitución firmada", "EDT/WBS aprobado", "Equipo formado"]	["Objetivos SMART definidos", "Alcance documentado", "PM asignado"]	[]	\N	PENDING	\N	\N	2026-03-24 10:11:27.808845
50ce72e8-3fcb-4d67-a23d-093038a0d6f5	Plataforma-OpenShift-OnPremise	G2	Gate Planificación	["Presupuesto aprobado", "Gantt baseline", "Riesgos aceptados", "Kickoff realizado"]	["BAC definitivo", "Sprints planificados", "DoD por tarea", "Stakeholders notificados"]	[]	\N	PENDING	\N	\N	2026-03-24 10:11:27.812141
b83d569c-ffe5-42c6-8869-c3bf5b8b1b46	Plataforma-OpenShift-OnPremise	G3	Gate Ejecución	["Sprint Review OK", "CPI > 0.9", "SPI > 0.85", "Sin P1 abiertos"]	["Demo a stakeholders", "Retrospectiva completada", "Riesgos actualizados"]	[]	\N	PENDING	\N	\N	2026-03-24 10:11:27.816494
5ad0b950-3580-4931-b6b9-1be578f77e39	Plataforma-OpenShift-OnPremise	G4	Gate Cierre	["Todos los entregables aceptados", "Decommission completado", "Lecciones aprendidas"]	["Acta de cierre firmada", "Postmortem escrito", "Recursos liberados"]	[]	\N	PENDING	\N	\N	2026-03-24 10:11:27.819714
343f0ebf-2cf2-4b56-9e04-36af0f610e4f	Plataforma-OpenShift-OnPremise	G5	Gate Beneficios	["ROI verificado a 6 meses", "KPIs objetivo cumplidos"]	["Informe de beneficios", "Comparación BAC vs AC final"]	[]	\N	PENDING	\N	\N	2026-03-24 10:11:27.824005
ce6d925d-f7ee-4c13-8028-794d9aa0c93c	Modelo de gestión de secretos	G0	Gate Idea	["Business Case aprobado", "Presupuesto orientativo", "Sponsor identificado"]	["Formulario Business Case completo", "Prioridad asignada"]	[]	\N	PENDING	\N	\N	2026-03-24 12:47:41.426047
a9d23338-0952-4fd1-89d1-dd08aafc2ea0	Modelo de gestión de secretos	G1	Gate Inicio	["Acta Constitución firmada", "EDT/WBS aprobado", "Equipo formado"]	["Objetivos SMART definidos", "Alcance documentado", "PM asignado"]	[]	\N	PENDING	\N	\N	2026-03-24 12:47:41.435678
c380165e-88fc-47a1-916a-dd8ae7ca2b78	Modelo de gestión de secretos	G2	Gate Planificación	["Presupuesto aprobado", "Gantt baseline", "Riesgos aceptados", "Kickoff realizado"]	["BAC definitivo", "Sprints planificados", "DoD por tarea", "Stakeholders notificados"]	[]	\N	PENDING	\N	\N	2026-03-24 12:47:41.44964
4ae858a9-5c7c-4037-847c-f88ae996c4f3	Modelo de gestión de secretos	G3	Gate Ejecución	["Sprint Review OK", "CPI > 0.9", "SPI > 0.85", "Sin P1 abiertos"]	["Demo a stakeholders", "Retrospectiva completada", "Riesgos actualizados"]	[]	\N	PENDING	\N	\N	2026-03-24 12:47:41.454793
206e86d0-2c44-4590-9f52-52ac5189ff1f	Modelo de gestión de secretos	G4	Gate Cierre	["Todos los entregables aceptados", "Decommission completado", "Lecciones aprendidas"]	["Acta de cierre firmada", "Postmortem escrito", "Recursos liberados"]	[]	\N	PENDING	\N	\N	2026-03-24 12:47:41.45866
9f12ae83-8486-4b8e-9a2e-ca628536c8a2	Modelo de gestión de secretos	G5	Gate Beneficios	["ROI verificado a 6 meses", "KPIs objetivo cumplidos"]	["Informe de beneficios", "Comparación BAC vs AC final"]	[]	\N	PENDING	\N	\N	2026-03-24 12:47:41.463982
1fb9127f-340d-4fd1-8c95-ef2e620a9545	NAC-OFICINAS-2026	G0	Gate Idea	["Business Case aprobado", "Presupuesto orientativo", "Sponsor identificado"]	["Formulario Business Case completo", "Prioridad asignada"]	[]	\N	PENDING	\N	\N	2026-03-25 11:10:13.205229
b8977755-5cf1-48e2-828c-9fa0e0a67a4d	NAC-OFICINAS-2026	G1	Gate Inicio	["Acta Constitución firmada", "EDT/WBS aprobado", "Equipo formado"]	["Objetivos SMART definidos", "Alcance documentado", "PM asignado"]	[]	\N	PENDING	\N	\N	2026-03-25 11:10:13.238981
0ab0125f-7b5c-4fa1-aa90-b42d53629598	NAC-OFICINAS-2026	G2	Gate Planificación	["Presupuesto aprobado", "Gantt baseline", "Riesgos aceptados", "Kickoff realizado"]	["BAC definitivo", "Sprints planificados", "DoD por tarea", "Stakeholders notificados"]	[]	\N	PENDING	\N	\N	2026-03-25 11:10:13.242875
b1d02741-17e5-40f7-9db4-6de459b9e646	NAC-OFICINAS-2026	G3	Gate Ejecución	["Sprint Review OK", "CPI > 0.9", "SPI > 0.85", "Sin P1 abiertos"]	["Demo a stakeholders", "Retrospectiva completada", "Riesgos actualizados"]	[]	\N	PENDING	\N	\N	2026-03-25 11:10:13.247642
b03e52e0-643a-42fb-a4f8-a026320d8937	NAC-OFICINAS-2026	G4	Gate Cierre	["Todos los entregables aceptados", "Decommission completado", "Lecciones aprendidas"]	["Acta de cierre firmada", "Postmortem escrito", "Recursos liberados"]	[]	\N	PENDING	\N	\N	2026-03-25 11:10:13.251508
d634f708-2e48-4aaf-9820-656d7291f14f	NAC-OFICINAS-2026	G5	Gate Beneficios	["ROI verificado a 6 meses", "KPIs objetivo cumplidos"]	["Informe de beneficios", "Comparación BAC vs AC final"]	[]	\N	PENDING	\N	\N	2026-03-25 11:10:13.255409
101b4d25-31cc-4c0f-bccc-1099ef256263	plan-sistemas-inteligentes	G0	Gate Idea	["Business Case aprobado", "Presupuesto orientativo", "Sponsor identificado"]	["Formulario Business Case completo", "Prioridad asignada"]	[]	\N	PENDING	\N	\N	2026-03-25 11:45:37.475979
133a5a56-d292-4870-ab17-3c26ec7ff2ba	plan-sistemas-inteligentes	G1	Gate Inicio	["Acta Constitución firmada", "EDT/WBS aprobado", "Equipo formado"]	["Objetivos SMART definidos", "Alcance documentado", "PM asignado"]	[]	\N	PENDING	\N	\N	2026-03-25 11:45:37.503824
de584f3f-895a-49de-92ac-f6357e2af084	plan-sistemas-inteligentes	G2	Gate Planificación	["Presupuesto aprobado", "Gantt baseline", "Riesgos aceptados", "Kickoff realizado"]	["BAC definitivo", "Sprints planificados", "DoD por tarea", "Stakeholders notificados"]	[]	\N	PENDING	\N	\N	2026-03-25 11:45:37.517559
a4e7b194-bd80-43d0-a917-a7b7fa2aea65	plan-sistemas-inteligentes	G3	Gate Ejecución	["Sprint Review OK", "CPI > 0.9", "SPI > 0.85", "Sin P1 abiertos"]	["Demo a stakeholders", "Retrospectiva completada", "Riesgos actualizados"]	[]	\N	PENDING	\N	\N	2026-03-25 11:45:37.52023
d893518b-e0aa-41ae-aa6c-084c26cbaca2	plan-sistemas-inteligentes	G4	Gate Cierre	["Todos los entregables aceptados", "Decommission completado", "Lecciones aprendidas"]	["Acta de cierre firmada", "Postmortem escrito", "Recursos liberados"]	[]	\N	PENDING	\N	\N	2026-03-25 11:45:37.523858
148eca80-c581-4a27-8015-6b6ebdafe966	plan-sistemas-inteligentes	G5	Gate Beneficios	["ROI verificado a 6 meses", "KPIs objetivo cumplidos"]	["Informe de beneficios", "Comparación BAC vs AC final"]	[]	\N	PENDING	\N	\N	2026-03-25 11:45:37.527044
8c9c5491-1820-448c-b4d4-1dcc82636228	Exadata Mission Critical Oracle BD	G0	Gate Idea	["Business Case aprobado", "Presupuesto orientativo", "Sponsor identificado"]	["Formulario Business Case completo", "Prioridad asignada"]	[]	\N	PENDING	\N	\N	2026-03-25 12:20:23.731897
1d3d0b33-25d2-4458-8c1c-c8c45838c623	Exadata Mission Critical Oracle BD	G1	Gate Inicio	["Acta Constitución firmada", "EDT/WBS aprobado", "Equipo formado"]	["Objetivos SMART definidos", "Alcance documentado", "PM asignado"]	[]	\N	PENDING	\N	\N	2026-03-25 12:20:23.740089
fae904fc-081d-4ef3-940e-92a62c4fdec5	Exadata Mission Critical Oracle BD	G2	Gate Planificación	["Presupuesto aprobado", "Gantt baseline", "Riesgos aceptados", "Kickoff realizado"]	["BAC definitivo", "Sprints planificados", "DoD por tarea", "Stakeholders notificados"]	[]	\N	PENDING	\N	\N	2026-03-25 12:20:23.744311
ba5a1d09-abfd-4d16-85df-902db3e7c75b	Exadata Mission Critical Oracle BD	G3	Gate Ejecución	["Sprint Review OK", "CPI > 0.9", "SPI > 0.85", "Sin P1 abiertos"]	["Demo a stakeholders", "Retrospectiva completada", "Riesgos actualizados"]	[]	\N	PENDING	\N	\N	2026-03-25 12:20:23.74718
35ef78df-ae4c-41e0-b12c-998ce39aa9b5	Exadata Mission Critical Oracle BD	G4	Gate Cierre	["Todos los entregables aceptados", "Decommission completado", "Lecciones aprendidas"]	["Acta de cierre firmada", "Postmortem escrito", "Recursos liberados"]	[]	\N	PENDING	\N	\N	2026-03-25 12:20:23.75133
98e00a14-fd07-44c9-9eea-b4087c342b88	Exadata Mission Critical Oracle BD	G5	Gate Beneficios	["ROI verificado a 6 meses", "KPIs objetivo cumplidos"]	["Informe de beneficios", "Comparación BAC vs AC final"]	[]	\N	PENDING	\N	\N	2026-03-25 12:20:23.754268
5aa734e2-03cb-4bf5-9a73-5caa4a1ccbf0	CCoE-2026	G0	Gate Idea	["Business Case aprobado", "Presupuesto orientativo", "Sponsor identificado"]	["Formulario Business Case completo", "Prioridad asignada"]	[]	\N	PENDING	\N	\N	2026-03-25 20:59:05.739194
4b220301-60af-4dbb-b029-c017c7a2f95f	CCoE-2026	G1	Gate Inicio	["Acta Constitución firmada", "EDT/WBS aprobado", "Equipo formado"]	["Objetivos SMART definidos", "Alcance documentado", "PM asignado"]	[]	\N	PENDING	\N	\N	2026-03-25 20:59:05.747688
26a6a248-b391-4fce-b1a7-1958dde00c77	CCoE-2026	G2	Gate Planificación	["Presupuesto aprobado", "Gantt baseline", "Riesgos aceptados", "Kickoff realizado"]	["BAC definitivo", "Sprints planificados", "DoD por tarea", "Stakeholders notificados"]	[]	\N	PENDING	\N	\N	2026-03-25 20:59:05.750727
8e3e3a9d-1368-4728-994c-46e2432ab907	CCoE-2026	G3	Gate Ejecución	["Sprint Review OK", "CPI > 0.9", "SPI > 0.85", "Sin P1 abiertos"]	["Demo a stakeholders", "Retrospectiva completada", "Riesgos actualizados"]	[]	\N	PENDING	\N	\N	2026-03-25 20:59:05.754628
52683feb-6e71-4140-921e-5aa625ad33f2	CCoE-2026	G4	Gate Cierre	["Todos los entregables aceptados", "Decommission completado", "Lecciones aprendidas"]	["Acta de cierre firmada", "Postmortem escrito", "Recursos liberados"]	[]	\N	PENDING	\N	\N	2026-03-25 20:59:05.757238
0acda4e1-a3b5-428c-a4ac-78d71a571516	CCoE-2026	G5	Gate Beneficios	["ROI verificado a 6 meses", "KPIs objetivo cumplidos"]	["Informe de beneficios", "Comparación BAC vs AC final"]	[]	\N	PENDING	\N	\N	2026-03-25 20:59:05.761135
29256c9d-7196-4de4-b78c-75e02408236c	cierre-tecnologico-almeria	G0	Gate Idea	["Business Case aprobado", "Presupuesto orientativo", "Sponsor identificado"]	["Formulario Business Case completo", "Prioridad asignada"]	[]	\N	PENDING	\N	\N	2026-03-26 11:44:57.635027
917a8bd6-366a-4bd3-b64d-289308650046	cierre-tecnologico-almeria	G1	Gate Inicio	["Acta Constitución firmada", "EDT/WBS aprobado", "Equipo formado"]	["Objetivos SMART definidos", "Alcance documentado", "PM asignado"]	[]	\N	PENDING	\N	\N	2026-03-26 11:44:57.6446
ed3d288b-b580-40d6-b625-fcfb92fde33c	cierre-tecnologico-almeria	G2	Gate Planificación	["Presupuesto aprobado", "Gantt baseline", "Riesgos aceptados", "Kickoff realizado"]	["BAC definitivo", "Sprints planificados", "DoD por tarea", "Stakeholders notificados"]	[]	\N	PENDING	\N	\N	2026-03-26 11:44:57.649932
c1c10631-e7a7-49e2-aab0-7773e121d46d	cierre-tecnologico-almeria	G3	Gate Ejecución	["Sprint Review OK", "CPI > 0.9", "SPI > 0.85", "Sin P1 abiertos"]	["Demo a stakeholders", "Retrospectiva completada", "Riesgos actualizados"]	[]	\N	PENDING	\N	\N	2026-03-26 11:44:57.653626
5db31cba-33d4-462a-84f7-ee319dd2e112	cierre-tecnologico-almeria	G4	Gate Cierre	["Todos los entregables aceptados", "Decommission completado", "Lecciones aprendidas"]	["Acta de cierre firmada", "Postmortem escrito", "Recursos liberados"]	[]	\N	PENDING	\N	\N	2026-03-26 11:44:57.658703
5af576f9-c716-42fa-9e6b-e6d256f81bed	cierre-tecnologico-almeria	G5	Gate Beneficios	["ROI verificado a 6 meses", "KPIs objetivo cumplidos"]	["Informe de beneficios", "Comparación BAC vs AC final"]	[]	\N	PENDING	\N	\N	2026-03-26 11:44:57.66228
0be4c33c-8c6a-4060-8d3c-d60552db04cf	Nuevo modelo de gestion de Ticketing	G0	Gate Idea	["Business Case aprobado", "Presupuesto orientativo", "Sponsor identificado"]	["Formulario Business Case completo", "Prioridad asignada"]	[]	\N	PENDING	\N	\N	2026-03-26 18:57:54.593445
01902897-4118-47b0-9b75-af8ea44bb6c2	Nuevo modelo de gestion de Ticketing	G1	Gate Inicio	["Acta Constitución firmada", "EDT/WBS aprobado", "Equipo formado"]	["Objetivos SMART definidos", "Alcance documentado", "PM asignado"]	[]	\N	PENDING	\N	\N	2026-03-26 18:57:54.622121
053b63fd-2b2c-4948-b823-ac3a71d4a76f	Nuevo modelo de gestion de Ticketing	G2	Gate Planificación	["Presupuesto aprobado", "Gantt baseline", "Riesgos aceptados", "Kickoff realizado"]	["BAC definitivo", "Sprints planificados", "DoD por tarea", "Stakeholders notificados"]	[]	\N	PENDING	\N	\N	2026-03-26 18:57:54.62624
f69db472-4e40-483e-8347-9e6f9e5035d9	Nuevo modelo de gestion de Ticketing	G3	Gate Ejecución	["Sprint Review OK", "CPI > 0.9", "SPI > 0.85", "Sin P1 abiertos"]	["Demo a stakeholders", "Retrospectiva completada", "Riesgos actualizados"]	[]	\N	PENDING	\N	\N	2026-03-26 18:57:54.631091
c6a90f93-8997-4052-a76b-fa75d95fcb77	Nuevo modelo de gestion de Ticketing	G4	Gate Cierre	["Todos los entregables aceptados", "Decommission completado", "Lecciones aprendidas"]	["Acta de cierre firmada", "Postmortem escrito", "Recursos liberados"]	[]	\N	PENDING	\N	\N	2026-03-26 18:57:54.634857
b55e7a11-022a-43ec-a7db-b7a285337e20	Nuevo modelo de gestion de Ticketing	G5	Gate Beneficios	["ROI verificado a 6 meses", "KPIs objetivo cumplidos"]	["Informe de beneficios", "Comparación BAC vs AC final"]	[]	\N	PENDING	\N	\N	2026-03-26 18:57:54.639297
\.


ALTER TABLE public.build_quality_gates ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

\unrestrict f5xocJiOG84lwsucJSCBhlzwMm50Qmq8dszrVbYebjjlgaeXZbbvYScTyOy1HgL

