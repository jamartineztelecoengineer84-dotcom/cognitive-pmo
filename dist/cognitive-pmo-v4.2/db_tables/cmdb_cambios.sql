--
-- PostgreSQL database dump
--

\restrict DovN5f5fDY5FmHoTp9aFQrLA3hXAJAHx560xb4GoVX43SpHtfVOfkST9heRdnpV

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
-- Data for Name: cmdb_cambios; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.cmdb_cambios DISABLE TRIGGER ALL;

COPY public.cmdb_cambios (id_cambio, id_activo, tipo_cambio, descripcion, realizado_por, fecha, datos_antes, datos_despues) FROM stdin;
\.


ALTER TABLE public.cmdb_cambios ENABLE TRIGGER ALL;

--
-- Name: cmdb_cambios_id_cambio_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cmdb_cambios_id_cambio_seq', 1, false);


--
-- PostgreSQL database dump complete
--

\unrestrict DovN5f5fDY5FmHoTp9aFQrLA3hXAJAHx560xb4GoVX43SpHtfVOfkST9heRdnpV

