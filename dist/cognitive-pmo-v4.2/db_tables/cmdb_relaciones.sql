--
-- PostgreSQL database dump
--

\restrict WIcxppykOETAKke3RH7cdfPjTA1NPj4Vx23Ppd7gjdWV719G81cewCFCbynMz4R

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
-- Data for Name: cmdb_relaciones; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.cmdb_relaciones DISABLE TRIGGER ALL;

COPY public.cmdb_relaciones (id_relacion, id_activo_origen, id_activo_destino, tipo_relacion, descripcion, criticidad) FROM stdin;
1	38	1	PROTEGE_A	CrowdStrike protege servidores	ALTA
2	42	1	RESPALDA_A	DR replica servidor principal	CRITICA
3	41	1	MONITORIZA	Zabbix monitoriza servidores	ALTA
4	11	1	EJECUTA_EN	Oracle en servidor Core Banking	CRITICA
5	33	3	EJECUTA_EN	SWIFT Gateway en servidor dedicado	CRITICA
6	39	5	PROTEGE_A	CyberArk gestiona accesos AD	CRITICA
7	5	6	RESPALDA_A	DC2 replica DC1	CRITICA
8	40	9	MONITORIZA	Grafana monitoriza Kubernetes	ALTA
9	40	9	EJECUTA_EN	Grafana en Kubernetes	MEDIA
10	34	9	EJECUTA_EN	Kafka en Kubernetes	CRITICA
11	30	9	EJECUTA_EN	API Gateway en Kubernetes	CRITICA
12	28	9	EJECUTA_EN	Banca Online en Kubernetes	CRITICA
13	27	9	EJECUTA_EN	Core Banking corre en Kubernetes	CRITICA
14	43	11	RESPALDA_A	Data Guard replica Oracle	CRITICA
15	27	11	DEPENDE_DE	Core Banking depende de Oracle RAC	CRITICA
16	31	12	DEPENDE_DE	Pasarela pagos usa PostgreSQL	CRITICA
17	32	13	DEPENDE_DE	Motor riesgo usa MongoDB	ALTA
18	32	14	DEPENDE_DE	Motor riesgo usa Redis cache	ALTA
19	37	15	DEPENDE_DE	SIEM usa Elasticsearch	ALTA
20	17	16	RESPALDA_A	Veeam respalda SAN NetApp	ALTA
21	11	16	DEPENDE_DE	Oracle usa SAN NetApp	CRITICA
22	9	16	DEPENDE_DE	Kubernetes usa SAN para PVs	CRITICA
23	21	18	DEPENDE_DE	WAF tras firewall perimetral	CRITICA
24	25	20	DEPENDE_DE	Balanceador tras firewall interno	ALTA
25	18	22	CONECTA_A	Firewall conecta a switch core	CRITICA
26	9	22	CONECTA_A	Kubernetes conecta a switch core	ALTA
27	30	25	DEPENDE_DE	API Gateway tras balanceador	ALTA
28	29	30	DEPENDE_DE	App Móvil usa API Gateway	CRITICA
29	28	30	DEPENDE_DE	Banca Online usa API Gateway	CRITICA
30	31	34	DEPENDE_DE	Pasarela pagos publica en Kafka	ALTA
31	125	5	DEPENDE_DE	VDI usa AD	ALTA
32	117	5	DEPENDE_DE	NAC depende de AD	CRITICA
33	61	5	DEPENDE_DE	Vault depende de AD	CRITICA
34	139	9	MONITORIZA	Datadog monitoriza K8s	ALTA
35	99	9	EJECUTA_EN	CRM en K8s	ALTA
36	94	9	EJECUTA_EN	Notificaciones en K8s	ALTA
37	95	9	EJECUTA_EN	Auth service en K8s	CRITICA
38	106	11	DEPENDE_DE	ETL lee Oracle	ALTA
39	97	11	DEPENDE_DE	AML usa Oracle	CRITICA
40	106	13	DEPENDE_DE	ETL escribe MongoDB	ALTA
41	98	13	DEPENDE_DE	BI usa MongoDB	ALTA
42	103	13	DEPENDE_DE	Scoring usa MongoDB	ALTA
43	141	16	RESPALDA_A	Commvault respalda SAN	ALTA
44	125	16	DEPENDE_DE	VDI usa SAN	ALTA
45	54	16	DEPENDE_DE	GitLab usa SAN	ALTA
46	84	22	CONECTA_A	Router WAN a switch core	CRITICA
47	90	24	CONECTA_A	WLC a switch acceso	MEDIA
48	134	28	SIRVE_A	CDN sirve a Banca Online	ALTA
49	104	30	DEPENDE_DE	Open Banking usa API Gateway	CRITICA
50	102	31	DEPENDE_DE	Bizum usa Pasarela Pagos	CRITICA
51	118	37	DEPENDE_DE	SOAR depende de SIEM	ALTA
52	142	42	RESPALDA_A	Zerto replica a DR	CRITICA
53	86	84	DEPENDE_DE	MPLS sobre WAN	CRITICA
54	29	95	DEPENDE_DE	App Móvil usa Auth	CRITICA
55	28	95	DEPENDE_DE	Banca Online usa Auth	CRITICA
\.


ALTER TABLE public.cmdb_relaciones ENABLE TRIGGER ALL;

--
-- Name: cmdb_relaciones_id_relacion_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cmdb_relaciones_id_relacion_seq', 55, true);


--
-- PostgreSQL database dump complete
--

\unrestrict WIcxppykOETAKke3RH7cdfPjTA1NPj4Vx23Ppd7gjdWV719G81cewCFCbynMz4R

