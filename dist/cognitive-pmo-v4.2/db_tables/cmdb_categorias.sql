--
-- PostgreSQL database dump
--

\restrict eDFkC4iP2jYrYKuhvnFT6bueIyuqEpa8hzoxxd2B13PTKve9B0Dsc7CPDrbM44c

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
-- Data for Name: cmdb_categorias; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.cmdb_categorias DISABLE TRIGGER ALL;

COPY public.cmdb_categorias (id_categoria, nombre, capa, icono, color) FROM stdin;
1	Servidor Físico	INFRAESTRUCTURA	server	#3B82F6
2	Servidor Virtual (VM)	INFRAESTRUCTURA	monitor	#60A5FA
3	Contenedor/Pod K8s	INFRAESTRUCTURA	box	#06B6D4
4	Cluster Kubernetes	INFRAESTRUCTURA	layers	#0891B2
5	Storage / SAN	INFRAESTRUCTURA	hard-drive	#8B5CF6
6	Balanceador de Carga	INFRAESTRUCTURA	git-merge	#A855F7
7	Base de Datos	INFRAESTRUCTURA	database	#F59E0B
8	Switch	RED	git-branch	#10B981
9	Router	RED	wifi	#059669
10	Firewall	SEGURIDAD	shield	#EF4444
11	WAF	SEGURIDAD	shield-alert	#DC2626
12	IDS/IPS	SEGURIDAD	alert-triangle	#F97316
13	VPN Gateway	RED	lock	#7C3AED
14	Access Point WiFi	RED	wifi	#34D399
15	Aplicación Web	APLICACION	globe	#2563EB
16	API / Microservicio	APLICACION	code	#3B82F6
17	Middleware / ESB	APLICACION	layers	#6366F1
18	Cola de Mensajería	APLICACION	mail	#8B5CF6
19	Servicio Cloud (SaaS)	APLICACION	cloud	#0EA5E9
20	CDN	RED	zap	#F472B6
21	Certificado SSL/TLS	SEGURIDAD	key	#F59E0B
22	DNS	RED	globe	#10B981
23	Proxy Inverso	RED	shuffle	#6366F1
24	Cabina Backup	INFRAESTRUCTURA	archive	#D97706
25	UPS / SAI	SOPORTE	battery	#EAB308
26	Sistema Monitorización	SOPORTE	activity	#EC4899
27	Licencia Software	NEGOCIO	file-text	#9CA3AF
28	Proyecto PMO	NEGOCIO	briefcase	#2563EB
29	Puesto de Trabajo	SOPORTE	laptop	#64748B
30	Impresora/MFP	SOPORTE	printer	#94A3B8
31	Teléfono IP	SOPORTE	phone	#64748B
32	ATM / Cajero	NEGOCIO	credit-card	#EF4444
\.


ALTER TABLE public.cmdb_categorias ENABLE TRIGGER ALL;

--
-- Name: cmdb_categorias_id_categoria_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cmdb_categorias_id_categoria_seq', 64, true);


--
-- PostgreSQL database dump complete
--

\unrestrict eDFkC4iP2jYrYKuhvnFT6bueIyuqEpa8hzoxxd2B13PTKve9B0Dsc7CPDrbM44c

