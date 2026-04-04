--
-- PostgreSQL database dump
--

\restrict 6viyNIEWGoOgS7UJYXfEsAymR2eCIerCnOKHe1eapiTGHVeKZZr40clUVV8uelV

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
-- Data for Name: rbac_audit_log; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.rbac_audit_log DISABLE TRIGGER ALL;

COPY public.rbac_audit_log (id_log, id_usuario, email, accion, modulo, recurso, detalle, ip_address, resultado, "timestamp") FROM stdin;
1	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	192.168.1.49	OK	2026-03-20 13:23:50.406795
2	3	carmen.delgado@cognitivepmo.com	LOGIN_OK	auth	\N	{"role": "CTO"}	192.168.1.49	OK	2026-03-20 13:24:00.298128
3	\N	jorge.sánchez@cognitivepmo.com	LOGIN_FALLIDO	\N	\N	{"reason": "credenciales_invalidas"}	192.168.1.49	DENEGADO	2026-03-20 13:24:00.338076
4	171	jorge.sanchez@cognitivepmo.com	LOGIN_OK	auth	\N	{"role": "TECH_JUNIOR"}	192.168.1.49	OK	2026-03-20 13:24:40.095263
5	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	192.168.1.49	OK	2026-03-20 13:24:51.334556
6	171	jorge.sanchez@cognitivepmo.com	LOGIN_OK	auth	\N	{"role": "TECH_JUNIOR"}	192.168.1.49	OK	2026-03-20 13:25:01.761084
7	171	jorge.sanchez@cognitivepmo.com	ACCESO_DENEGADO	rbac	/rbac/dashboard	{"missing_permisos": ["rbac.ver"]}	192.168.1.49	DENEGADO	2026-03-20 13:25:01.806286
8	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	192.168.1.49	OK	2026-03-20 15:21:58.555258
9	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 15:22:25.438663
10	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 15:23:11.703759
11	1	admin	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-20 15:23:41.979024
12	171	jorge.sanchez@cognitivepmo.com	LOGIN_OK	auth	\N	{"role": "TECH_JUNIOR"}	172.27.0.3	OK	2026-03-20 15:24:01.718815
13	171	jorge.sanchez@cognitivepmo.com	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-20 15:24:47.134536
14	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 15:24:52.360585
15	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 15:33:20.912902
16	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 15:34:12.359664
17	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 15:38:43.723868
18	1	admin	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-20 15:39:48.83598
19	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 15:39:54.664513
20	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 15:42:29.310553
21	1	admin	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-20 15:52:14.616175
22	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 16:03:36.541784
23	1	admin	CAMBIO_PERMISOS_ROL	rbac	SUPERADMIN	{"role_id": 1, "permisos_count": 75}	\N	OK	2026-03-20 16:10:03.474983
24	1	admin	CAMBIO_PERMISOS_ROL	rbac	TEAM_LEAD	{"role_id": 16, "permisos_count": 27}	\N	OK	2026-03-20 16:10:13.912808
25	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 16:14:46.286392
26	1	admin	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-20 16:15:54.449162
27	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 16:22:52.719454
28	1	admin	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-20 16:25:24.43796
29	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 16:27:43.2294
30	1	admin	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-20 16:27:56.346288
31	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 16:33:19.243296
32	1	admin	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-20 16:50:10.19825
33	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 16:50:31.117216
34	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 16:54:11.723293
35	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 16:54:18.892054
36	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 17:12:30.897497
37	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 17:24:22.24556
38	1	admin	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-20 17:33:40.725488
39	\N	ADMIN	LOGIN_FALLIDO	\N	\N	{"reason": "credenciales_invalidas"}	172.27.0.3	DENEGADO	2026-03-20 17:34:11.931605
40	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 17:34:18.089273
41	1	admin	CAMBIO_PERMISOS_ROL	rbac	SUPERADMIN	{"role_id": 1, "permisos_count": 75}	\N	OK	2026-03-20 17:44:29.473526
42	1	admin	CAMBIO_PERMISOS_ROL	rbac	SUPERADMIN	{"role_id": 1, "permisos_count": 87}	\N	OK	2026-03-20 17:44:37.38836
43	1	admin	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-20 22:07:06.53019
44	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 22:07:23.350218
45	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-20 22:57:10.8313
46	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-21 00:03:59.956617
47	1	admin	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-21 10:16:20.105083
48	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-21 10:18:03.043409
49	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-21 12:42:19.473053
50	1	admin	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-21 19:20:21.619017
51	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-21 19:22:23.226004
52	1	admin	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-21 19:40:50.933814
53	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-21 19:46:53.760729
54	1	admin	LOGOUT	auth	\N	{}	172.27.0.3	OK	2026-03-21 22:08:16.139133
55	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-21 22:08:31.340882
56	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-22 22:10:37.711634
57	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-23 22:21:55.040046
58	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-24 22:42:19.592629
59	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-25 22:48:23.705001
60	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-27 17:01:42.321279
61	1	admin	LOGIN_OK	auth	\N	{"role": "SUPERADMIN"}	172.27.0.3	OK	2026-03-30 18:35:47.518525
\.


ALTER TABLE public.rbac_audit_log ENABLE TRIGGER ALL;

--
-- Name: rbac_audit_log_id_log_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rbac_audit_log_id_log_seq', 61, true);


--
-- PostgreSQL database dump complete
--

\unrestrict 6viyNIEWGoOgS7UJYXfEsAymR2eCIerCnOKHe1eapiTGHVeKZZr40clUVV8uelV

