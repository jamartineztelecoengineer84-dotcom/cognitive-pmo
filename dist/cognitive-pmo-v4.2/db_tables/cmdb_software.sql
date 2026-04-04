--
-- PostgreSQL database dump
--

\restrict 1gyePHIwmSgU2Hwgy6DSnN0tmNAh1pRL9yY1aAfE2m4i7CNyCKT1qHKseTe63dQ

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
-- Data for Name: cmdb_software; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.cmdb_software DISABLE TRIGGER ALL;

COPY public.cmdb_software (id_software, nombre, version, editor, tipo_licencia, num_licencias, licencias_usadas, coste_anual, fecha_renovacion, estado, critico_negocio) FROM stdin;
1	Red Hat Enterprise Linux	9.2	Red Hat	SUSCRIPCION	80	62	96000.00	\N	ACTIVO	t
2	Windows Server	2022	Microsoft	COMERCIAL	45	38	54000.00	\N	ACTIVO	t
3	Oracle Database Enterprise	19c	Oracle	COMERCIAL	4	2	280000.00	\N	ACTIVO	t
4	PostgreSQL	15.6	PostgreSQL Global	OPEN_SOURCE	0	0	0.00	\N	ACTIVO	t
5	MongoDB Enterprise	7.0	MongoDB Inc	SUSCRIPCION	3	3	36000.00	\N	ACTIVO	f
6	Redis Enterprise	7.2	Redis Ltd	SUSCRIPCION	1	1	18000.00	\N	ACTIVO	t
7	Elasticsearch Platinum	8.12	Elastic	SUSCRIPCION	1	1	42000.00	\N	ACTIVO	f
8	VMware vSphere Enterprise Plus	8.0	Broadcom	COMERCIAL	24	20	72000.00	\N	ACTIVO	t
9	Red Hat OpenShift	4.14	Red Hat	SUSCRIPCION	2	2	120000.00	\N	ACTIVO	t
10	Microsoft 365 E5	Latest	Microsoft	SUSCRIPCION	850	820	408000.00	\N	ACTIVO	f
11	CrowdStrike Falcon	6.x	CrowdStrike	SUSCRIPCION	850	850	180000.00	\N	ACTIVO	t
12	Splunk Enterprise	9.2	Splunk	SUSCRIPCION	1	1	90000.00	\N	ACTIVO	t
13	CyberArk Privilege Cloud	13.2	CyberArk	SUSCRIPCION	1	1	65000.00	\N	ACTIVO	t
14	Veeam Backup & Replication	12	Veeam	SUSCRIPCION	1	1	24000.00	\N	ACTIVO	t
15	ServiceNow ITSM	Tokyo	ServiceNow	SUSCRIPCION	200	185	102000.00	\N	ACTIVO	f
16	PAN-OS	11.1	Palo Alto Networks	SUSCRIPCION	2	2	48000.00	\N	ACTIVO	t
17	FortiOS	7.4	Fortinet	SUSCRIPCION	1	1	18000.00	\N	ACTIVO	t
18	Cisco NX-OS	10.3	Cisco	COMERCIAL	4	4	12000.00	\N	ACTIVO	t
19	Kong Enterprise	3.5	Kong Inc	SUSCRIPCION	1	1	36000.00	\N	ACTIVO	t
20	Apache Kafka (Confluent)	3.6	Confluent	SUSCRIPCION	1	1	28800.00	\N	ACTIVO	t
21	Grafana Enterprise	10.3	Grafana Labs	SUSCRIPCION	1	1	14400.00	\N	ACTIVO	f
22	Zabbix	6.4	Zabbix	OPEN_SOURCE	0	0	0.00	\N	ACTIVO	f
23	Temenos T24 Transact	R22	Temenos	COMERCIAL	1	1	500000.00	\N	ACTIVO	t
24	F5 BIG-IP ASM	17.1	F5 Networks	COMERCIAL	2	2	42000.00	\N	ACTIVO	t
25	Cisco AnyConnect	5.1	Cisco	SUSCRIPCION	2000	1200	24000.00	\N	ACTIVO	f
26	Git / GitLab Enterprise	16.8	GitLab	SUSCRIPCION	150	142	27000.00	\N	ACTIVO	f
27	Jira Software	9.x	Atlassian	SUSCRIPCION	150	140	21600.00	\N	ACTIVO	f
28	Confluence	8.x	Atlassian	SUSCRIPCION	150	130	12600.00	\N	ACTIVO	f
29	Flowise AI	1.8	FlowiseAI	OPEN_SOURCE	0	0	0.00	\N	ACTIVO	f
30	SonarQube Enterprise	10.4	SonarSource	SUSCRIPCION	1	1	15000.00	\N	ACTIVO	f
\.


ALTER TABLE public.cmdb_software ENABLE TRIGGER ALL;

--
-- Name: cmdb_software_id_software_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cmdb_software_id_software_seq', 30, true);


--
-- PostgreSQL database dump complete
--

\unrestrict 1gyePHIwmSgU2Hwgy6DSnN0tmNAh1pRL9yY1aAfE2m4i7CNyCKT1qHKseTe63dQ

