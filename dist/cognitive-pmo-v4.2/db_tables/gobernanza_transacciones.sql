--
-- PostgreSQL database dump
--

\restrict MpAMBeFojoDwPzKiSYkL7O8L8KkgxsRZ9k3J9sA6f10ge8iI6vCiUNDQ9pqjBj8

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
-- Data for Name: gobernanza_transacciones; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.gobernanza_transacciones DISABLE TRIGGER ALL;

COPY public.gobernanza_transacciones (id_transaccion, tipo_accion, id_proyecto, fte_afectado, estado_anterior, estado_nuevo, motivo, agente_origen, datos_contexto, timestamp_ejecucion, usuario_db, pending_sync, depth, correlation_id, retry_count, sync_status) FROM stdin;
\.


ALTER TABLE public.gobernanza_transacciones ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

\unrestrict MpAMBeFojoDwPzKiSYkL7O8L8KkgxsRZ9k3J9sA6f10ge8iI6vCiUNDQ9pqjBj8

