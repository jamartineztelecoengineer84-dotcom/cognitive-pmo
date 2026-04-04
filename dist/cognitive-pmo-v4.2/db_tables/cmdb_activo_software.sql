--
-- PostgreSQL database dump
--

\restrict wqPLjG3Gbe5SLHi6MAIGOR9GdCskvHyb4uoJBLXeuRea1D9pA1yPBRElLOWwF7o

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
-- Data for Name: cmdb_activo_software; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.cmdb_activo_software DISABLE TRIGGER ALL;

COPY public.cmdb_activo_software (id_activo, id_software, version_instalada, fecha_instalacion) FROM stdin;
\.


ALTER TABLE public.cmdb_activo_software ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

\unrestrict wqPLjG3Gbe5SLHi6MAIGOR9GdCskvHyb4uoJBLXeuRea1D9pA1yPBRElLOWwF7o

