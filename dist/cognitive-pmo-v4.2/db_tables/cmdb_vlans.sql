--
-- PostgreSQL database dump
--

\restrict A0QQJbfyyOYUqFbh12uA9KkjsP6CBaeAVqiJHlJ0lFDXmxJaEz9BPWDH646Df20

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
-- Data for Name: cmdb_vlans; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.cmdb_vlans DISABLE TRIGGER ALL;

COPY public.cmdb_vlans (id_vlan, vlan_id, nombre, descripcion, subred, mascara, gateway, entorno, ubicacion, estado, proposito, total_ips, ips_usadas) FROM stdin;
1	10	MGMT-CORE	\N	10.0.10.0/24	255.255.255.0	10.0.10.1	PRODUCCION	CPD Madrid	ACTIVA	Gestión equipos core	254	0
2	20	SERVIDORES-PRO	\N	10.0.20.0/24	255.255.255.0	10.0.20.1	PRODUCCION	CPD Madrid	ACTIVA	Servidores producción	254	0
3	21	SERVIDORES-PRE	\N	10.0.21.0/24	255.255.255.0	10.0.21.1	PREPRODUCCION	CPD Madrid	ACTIVA	Servidores preproducción	254	0
4	22	SERVIDORES-DEV	\N	10.0.22.0/24	255.255.255.0	10.0.22.1	DESARROLLO	CPD Madrid	ACTIVA	Servidores desarrollo	254	0
5	30	BBDD-PRO	\N	10.0.30.0/24	255.255.255.0	10.0.30.1	PRODUCCION	CPD Madrid	ACTIVA	Bases de datos producción	254	0
6	31	BBDD-PRE	\N	10.0.31.0/24	255.255.255.0	10.0.31.1	PREPRODUCCION	CPD Madrid	ACTIVA	Bases de datos pre	254	0
7	40	DMZ-PUBLICA	\N	172.16.40.0/24	255.255.255.0	172.16.40.1	PRODUCCION	CPD Madrid	ACTIVA	DMZ servicios públicos	254	0
8	41	DMZ-PARTNERS	\N	172.16.41.0/24	255.255.255.0	172.16.41.1	PRODUCCION	CPD Madrid	ACTIVA	DMZ conexiones partners	254	0
9	50	USUARIOS-SEDE	\N	10.0.50.0/23	255.255.255.0	10.0.50.1	PRODUCCION	Sede Central	ACTIVA	Puestos de trabajo sede	510	0
10	51	USUARIOS-SUC	\N	10.0.52.0/22	255.255.255.0	10.0.52.1	PRODUCCION	Sucursales	ACTIVA	Puestos trabajo sucursales	1022	0
11	60	WIFI-CORP	\N	10.0.60.0/24	255.255.255.0	10.0.60.1	PRODUCCION	Todas sedes	ACTIVA	WiFi corporativa	254	0
12	61	WIFI-GUEST	\N	10.0.61.0/24	255.255.255.0	10.0.61.1	PRODUCCION	Todas sedes	ACTIVA	WiFi invitados	254	0
13	70	VOIP	\N	10.0.70.0/24	255.255.255.0	10.0.70.1	PRODUCCION	Todas sedes	ACTIVA	Telefonía IP	254	0
14	80	ATM-RED	\N	10.0.80.0/24	255.255.255.0	10.0.80.1	PRODUCCION	Nacional	ACTIVA	Red de cajeros automáticos	254	0
15	90	SWIFT-CORE	\N	10.0.90.0/28	255.255.255.0	10.0.90.1	PRODUCCION	CPD Madrid	ACTIVA	SWIFT Alliance segmento	14	0
16	100	KUBERNETES-PRO	\N	10.1.0.0/16	255.255.255.0	10.1.0.1	PRODUCCION	CPD Madrid	ACTIVA	Pod network Kubernetes PRO	65534	0
17	101	KUBERNETES-PRE	\N	10.2.0.0/16	255.255.255.0	10.2.0.1	PREPRODUCCION	CPD Madrid	ACTIVA	Pod network Kubernetes PRE	65534	0
18	110	BACKUP-NET	\N	10.0.110.0/24	255.255.255.0	10.0.110.1	PRODUCCION	CPD Madrid	ACTIVA	Red de backup dedicada	254	0
19	120	MONITORING	\N	10.0.120.0/24	255.255.255.0	10.0.120.1	PRODUCCION	CPD Madrid	ACTIVA	Red de monitorización	254	0
20	200	DR-SERVIDORES	\N	10.10.20.0/24	255.255.255.0	10.10.20.1	DR	CPD Barcelona	ACTIVA	DR servidores	254	0
21	201	DR-BBDD	\N	10.10.30.0/24	255.255.255.0	10.10.30.1	DR	CPD Barcelona	ACTIVA	DR bases de datos	254	0
22	250	LAB-SEGURIDAD	\N	192.168.250.0/24	255.255.255.0	192.168.250.1	LAB	SOC Madrid	ACTIVA	Laboratorio ciberseguridad	254	0
23	251	LAB-DESARROLLO	\N	192.168.251.0/24	255.255.255.0	192.168.251.1	LAB	Sede Central	ACTIVA	Laboratorio desarrollo	254	0
\.


ALTER TABLE public.cmdb_vlans ENABLE TRIGGER ALL;

--
-- Name: cmdb_vlans_id_vlan_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cmdb_vlans_id_vlan_seq', 46, true);


--
-- PostgreSQL database dump complete
--

\unrestrict A0QQJbfyyOYUqFbh12uA9KkjsP6CBaeAVqiJHlJ0lFDXmxJaEz9BPWDH646Df20

