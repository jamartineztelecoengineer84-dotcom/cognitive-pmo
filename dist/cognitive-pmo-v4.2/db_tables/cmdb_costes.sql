--
-- PostgreSQL database dump
--

\restrict MJj0XZSmWfuQY8ZoE4BBVjVZb1jkfgeELnjOKpMxZhlVwhJbaJpoqfhHj6Nl8PG

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
-- Data for Name: cmdb_costes; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.cmdb_costes DISABLE TRIGGER ALL;

COPY public.cmdb_costes (id_coste, id_activo, concepto, categoria, tipo, importe, moneda, periodicidad, fecha_inicio, fecha_fin, proveedor, centro_coste, id_proyecto, notas, created_at) FROM stdin;
1	1	Servidor HP ProLiant DL380 - Compra	HARDWARE	CAPEX	45000.00	EUR	UNICO	2024-01-15	\N	HP Enterprise	IT-INFRA	PRY-2024-001	Servidor principal de producción	2026-03-20 17:36:26.398082
2	1	Mantenimiento servidor HP ProLiant	MANTENIMIENTO	OPEX	850.00	EUR	MENSUAL	2024-02-01	2026-12-31	HP Enterprise	IT-INFRA	PRY-2024-001	Contrato de mantenimiento 24x7	2026-03-20 17:36:26.398082
3	2	Servidor Dell PowerEdge R740 - Compra	HARDWARE	CAPEX	38000.00	EUR	UNICO	2024-03-10	\N	Dell Technologies	IT-INFRA	PRY-2024-001	Servidor de base de datos	2026-03-20 17:36:26.398082
4	2	Soporte Dell ProSupport	SOPORTE	OPEX	1200.00	EUR	TRIMESTRAL	2024-04-01	2027-03-31	Dell Technologies	IT-INFRA	PRY-2024-001	\N	2026-03-20 17:36:26.398082
5	3	Licencia Oracle Database Enterprise	LICENCIAS	OPEX	18500.00	EUR	ANUAL	2024-01-01	2026-12-31	Oracle	IT-SW	PRY-2024-002	Licencia por procesador	2026-03-20 17:36:26.398082
6	3	Consultoría migración Oracle	CONSULTORIA	OPEX	25000.00	EUR	UNICO	2024-06-01	2024-09-30	Accenture	IT-SW	PRY-2024-002	Migración de esquemas	2026-03-20 17:36:26.398082
7	4	Licencia VMware vSphere Enterprise Plus	SOFTWARE	OPEX	12000.00	EUR	ANUAL	2024-01-01	2026-12-31	VMware	IT-VIRTUAL	PRY-2024-001	Licencia virtualización	2026-03-20 17:36:26.398082
8	4	Formación VMware avanzada	FORMACION	OPEX	4500.00	EUR	UNICO	2024-05-15	2024-05-20	VMware Education	IT-VIRTUAL	\N	Curso para equipo de 3 personas	2026-03-20 17:36:26.398082
9	5	Firewall Palo Alto PA-5250	HARDWARE	CAPEX	62000.00	EUR	UNICO	2024-02-20	\N	Palo Alto Networks	IT-SEGURIDAD	PRY-2024-003	Firewall perimetral principal	2026-03-20 17:36:26.398082
10	5	Suscripción Threat Prevention	SOFTWARE	OPEX	8500.00	EUR	ANUAL	2024-03-01	2027-02-28	Palo Alto Networks	IT-SEGURIDAD	PRY-2024-003	\N	2026-03-20 17:36:26.398082
11	6	Switch Cisco Catalyst 9300	HARDWARE	CAPEX	15000.00	EUR	UNICO	2024-01-20	\N	Cisco	IT-RED	PRY-2024-001	Switch core datacenter	2026-03-20 17:36:26.398082
12	6	Cisco SmartNet Total Care	MANTENIMIENTO	OPEX	450.00	EUR	MENSUAL	2024-02-01	2027-01-31	Cisco	IT-RED	PRY-2024-001	Soporte 8x5xNBD	2026-03-20 17:36:26.398082
13	7	Balanceador F5 BIG-IP i5800	HARDWARE	CAPEX	42000.00	EUR	UNICO	2024-04-15	\N	F5 Networks	IT-RED	PRY-2024-003	Balanceador de carga principal	2026-03-20 17:36:26.398082
14	7	Soporte F5 Premium	SOPORTE	OPEX	2100.00	EUR	TRIMESTRAL	2024-05-01	2027-04-30	F5 Networks	IT-RED	PRY-2024-003	\N	2026-03-20 17:36:26.398082
15	8	Almacenamiento NetApp FAS8700	HARDWARE	CAPEX	95000.00	EUR	UNICO	2024-01-10	\N	NetApp	IT-STORAGE	PRY-2024-001	Storage principal producción	2026-03-20 17:36:26.398082
16	8	NetApp SupportEdge Premium	MANTENIMIENTO	OPEX	1800.00	EUR	MENSUAL	2024-02-01	2027-01-31	NetApp	IT-STORAGE	PRY-2024-001	\N	2026-03-20 17:36:26.398082
17	9	Licencia ServiceNow ITSM	SOFTWARE	OPEX	35000.00	EUR	ANUAL	2024-01-01	2026-12-31	ServiceNow	IT-GESTION	PRY-2024-004	Plataforma ITSM	2026-03-20 17:36:26.398082
18	9	Consultoría implementación ServiceNow	CONSULTORIA	OPEX	55000.00	EUR	UNICO	2024-01-15	2024-06-30	Deloitte	IT-GESTION	PRY-2024-004	\N	2026-03-20 17:36:26.398082
19	10	AWS EC2 Reserved Instances	CLOUD	OPEX	4200.00	EUR	MENSUAL	2024-01-01	2026-12-31	Amazon Web Services	IT-CLOUD	PRY-2024-005	Instancias reservadas 3 años	2026-03-20 17:36:26.398082
20	10	AWS S3 Storage	CLOUD	OPEX	1500.00	EUR	MENSUAL	2024-01-01	\N	Amazon Web Services	IT-CLOUD	PRY-2024-005	Almacenamiento objetos	2026-03-20 17:36:26.398082
21	11	Azure SQL Database	CLOUD	OPEX	3200.00	EUR	MENSUAL	2024-03-01	\N	Microsoft Azure	IT-CLOUD	PRY-2024-005	Base de datos cloud	2026-03-20 17:36:26.398082
22	11	Azure ExpressRoute	CLOUD	OPEX	2800.00	EUR	MENSUAL	2024-03-01	2027-02-28	Microsoft Azure	IT-CLOUD	PRY-2024-005	Conexión dedicada	2026-03-20 17:36:26.398082
23	12	Splunk Enterprise License	SOFTWARE	OPEX	28000.00	EUR	ANUAL	2024-01-01	2026-12-31	Splunk	IT-SEGURIDAD	PRY-2024-003	SIEM y análisis de logs	2026-03-20 17:36:26.398082
24	12	Formación Splunk Admin	FORMACION	OPEX	3200.00	EUR	UNICO	2024-04-10	2024-04-14	Splunk Education	IT-SEGURIDAD	\N	\N	2026-03-20 17:36:26.398082
25	13	Ingeniero DevOps Senior	RRHH	OPEX	5500.00	EUR	MENSUAL	2024-01-01	\N	\N	IT-DEV	PRY-2024-002	Recurso dedicado al proyecto	2026-03-20 17:36:26.398082
26	14	Administrador de sistemas	RRHH	OPEX	4800.00	EUR	MENSUAL	2024-01-01	\N	\N	IT-INFRA	PRY-2024-001	Administrador de infraestructura	2026-03-20 17:36:26.398082
27	15	Analista de seguridad	RRHH	OPEX	5200.00	EUR	MENSUAL	2024-01-01	\N	\N	IT-SEGURIDAD	PRY-2024-003	Especialista en ciberseguridad	2026-03-20 17:36:26.398082
28	1	UPS APC Smart-UPS 3000	HARDWARE	CAPEX	8500.00	EUR	UNICO	2024-02-15	\N	APC by Schneider	IT-INFRA	PRY-2024-001	SAI para rack servidores	2026-03-20 17:36:26.398082
29	2	Extensión garantía servidor	MANTENIMIENTO	OPEX	2400.00	EUR	ANUAL	2025-01-01	2027-12-31	Dell Technologies	IT-INFRA	PRY-2024-001	\N	2026-03-20 17:36:26.398082
30	3	Consultoría performance tuning	CONSULTORIA	OPEX	12000.00	EUR	UNICO	2025-01-15	2025-03-15	DBA Experts SL	IT-SW	PRY-2024-002	Optimización de queries críticas	2026-03-20 17:36:26.398082
31	4	VMware Tanzu Basic	SOFTWARE	OPEX	8000.00	EUR	ANUAL	2025-01-01	2027-12-31	VMware	IT-VIRTUAL	\N	Gestión de contenedores	2026-03-20 17:36:26.398082
32	5	Auditoría de seguridad externa	CONSULTORIA	OPEX	18000.00	EUR	ANUAL	2024-06-01	2026-05-31	KPMG	IT-SEGURIDAD	PRY-2024-003	Auditoría PCI-DSS	2026-03-20 17:36:26.398082
33	6	Cableado estructurado Cat6a	HARDWARE	CAPEX	12000.00	EUR	UNICO	2024-03-01	\N	Nexans	IT-RED	PRY-2024-001	Cableado datacenter	2026-03-20 17:36:26.398082
34	7	SSL Wildcard Certificate	LICENCIAS	OPEX	1200.00	EUR	ANUAL	2024-04-01	2026-03-31	DigiCert	IT-SEGURIDAD	\N	Certificado wildcard *.banco.es	2026-03-20 17:36:26.398082
35	8	NetApp Cloud Volumes ONTAP	CLOUD	OPEX	2200.00	EUR	MENSUAL	2025-01-01	\N	NetApp	IT-CLOUD	PRY-2024-005	Replicación cloud DR	2026-03-20 17:36:26.398082
36	9	ServiceNow ITOM Discovery	SOFTWARE	OPEX	15000.00	EUR	ANUAL	2025-01-01	2027-12-31	ServiceNow	IT-GESTION	PRY-2024-004	Módulo de descubrimiento	2026-03-20 17:36:26.398082
37	10	AWS CloudWatch Enhanced	CLOUD	OPEX	800.00	EUR	MENSUAL	2024-06-01	\N	Amazon Web Services	IT-CLOUD	PRY-2024-005	Monitorización avanzada	2026-03-20 17:36:26.398082
38	11	Soporte Microsoft Premier	SOPORTE	OPEX	6000.00	EUR	TRIMESTRAL	2024-01-01	2026-12-31	Microsoft	IT-CLOUD	PRY-2024-005	\N	2026-03-20 17:36:26.398082
39	13	Arquitecto Cloud	RRHH	OPEX	6500.00	EUR	MENSUAL	2024-06-01	\N	\N	IT-CLOUD	PRY-2024-005	Recurso senior cloud	2026-03-20 17:36:26.398082
40	14	Seguro ciberriesgos	OTROS	OPEX	22000.00	EUR	ANUAL	2024-01-01	2026-12-31	AXA	IT-SEGURIDAD	\N	Póliza de ciberriesgos	2026-03-20 17:36:26.398082
\.


ALTER TABLE public.cmdb_costes ENABLE TRIGGER ALL;

--
-- Name: cmdb_costes_id_coste_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cmdb_costes_id_coste_seq', 40, true);


--
-- PostgreSQL database dump complete
--

\unrestrict MJj0XZSmWfuQY8ZoE4BBVjVZb1jkfgeELnjOKpMxZhlVwhJbaJpoqfhHj6Nl8PG

