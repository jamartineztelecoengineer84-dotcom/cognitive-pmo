--
-- PostgreSQL database dump
--

\restrict fAxE6MSF6r1uQNSthUANV6fXNbzXNI1NG24XoiWboDczs5letnfKcN2yL4ymLU1

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
-- Data for Name: cartera_build; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.cartera_build DISABLE TRIGGER ALL;

COPY public.cartera_build (id_proyecto, nombre_proyecto, prioridad_estrategica, horas_estimadas, skills_requeridas, horas_por_skill, estado, perfil_requerido, responsable_asignado, horas_base, fecha_creacion, fecha_ultima_modificacion, motivo_pausa, historial_estados) FROM stdin;
PRJ0005 - [PRE2022]	Aplicar control de acceso a la red (NAC) en oficinas comerciales	Alta	80	Redes: Port Security, VPN: Configurar Cliente, Seguridad: Bloqueo IP Firew	30, 20, 30	en revision	Redes: Port Security, VPN: Configurar Cliente, Seguridad: Bloqueo IP Firew	\N	80	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0006 - [PRE2022]	Implantar Exadata servidor Mission Critical para BD Oracle	Media	120	Linux: Navegaci�n, SQL: Select Simple, SQL: Create Table	20, 40, 60	en ejecucion	Linux: Navegaci�n, SQL: Select Simple, SQL: Create Table	\N	120	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0012 - [PRE2023]	Renovar infraestructura servidores de ETL	Alta	55	Linux: Tareas (Crontab), SQL: Inner Join, SQL: Insert Into	15, 20, 20	pendiente	Linux: Tareas (Crontab), SQL: Inner Join, SQL: Insert Into	\N	55	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0015 - -	Actualizar Erwin Mart Server	Baja	40	SQL: Create Table, Windows: Gesti�n Servicios	25, 15	En analisis	SQL: Create Table, Windows: Gesti�n Servicios	\N	40	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0016 - -	Actualizar plataforma de copias de seguridad corporativa	Media	60	SQL: Backup DB, SQL: Restore DB, Linux: Tareas (Crontab)	20, 25, 15	en ejecucion	SQL: Backup DB, SQL: Restore DB, Linux: Tareas (Crontab)	\N	60	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0018 - -	Aislar weblogic de Pagos de ARES	Media	55	Linux: Procesos, API: Auth JWT, Cloud: Security Groups	15, 20, 20	en cierre	Linux: Procesos, API: Auth JWT, Cloud: Security Groups	\N	55	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0022 - -	Ampliar capacidad del servicio batch de ARES	Alta	45	Linux: Tareas (Crontab), Backend: Logging errores	25, 20	En analisis	Linux: Tareas (Crontab), Backend: Logging errores	\N	45	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0023 - -	ApiManager to Control-M	Media	65	API: C�digos HTTP, API: Testing con Postman, Backend: Crear Endpoint REST	15, 20, 30	Standby	API: C�digos HTTP, API: Testing con Postman, Backend: Crear Endpoint REST	\N	65	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0026 - -	Control automático del Ciclo de Vida del dato	Alta	55	SQL: Delete, Linux: Tareas (Crontab), SQL: Left Join	20, 15, 20	en cierre	SQL: Delete, Linux: Tareas (Crontab), SQL: Left Join	\N	55	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0001 - [9470-2023]	Centralizar la gestión de identidades	Media	60	AD: Crear Usuario, AD: Grupos Seguridad, Seguridad: Configurar MFA	20, 30, 10	en ejecucion	AD: Crear Usuario, AD: Grupos Seguridad, Seguridad: Configurar MFA	\N	60	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0003 - [9470-2023]	Modelo de gestión de secretos	Alta	50	Seguridad: Permisos Carpeta, API: Auth JWT, Linux: Permisos	15, 25, 10	pendiente	Seguridad: Permisos Carpeta, API: Auth JWT, Linux: Permisos	\N	50	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0002 - [9470-2023]	Implementación de arquitectura para SIEM integrada en cloud	Alta	45	Cloud: VM Start/Stop, Cloud: Security Groups, Seguridad: Revisar Logs Acce	10, 15, 20	En analisis	Cloud: VM Start/Stop, Cloud: Security Groups, Seguridad: Revisar Logs Acce	\N	45	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0008 - [PRE2022]	Montar entorno de preproducción servicios calidad datos IDQ	Media	35	Linux: Navegaci�n, SQL: Inner Join, Linux: Tareas (Crontab)	10, 15, 10	En analisis	Linux: Navegaci�n, SQL: Inner Join, Linux: Tareas (Crontab)	\N	35	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0011 - [PRE2023]	Migrar sistemas Linux Red Hat 7 a versión actual	Alta	50	Linux: Procesos, Linux: B�squeda (grep), Linux: SSH Keys	20, 15, 15	en ejecucion	Linux: Procesos, Linux: B�squeda (grep), Linux: SSH Keys	\N	50	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0024 - -	Aplicación Web para el control de Entradas Manuales	Media	110	HTML: Sem�ntica b�sica, CSS: Flexbox, JS: Manipulaci�n DOM, Backend: Crear Endpoint REST	20, 20, 30, 40	en ejecucion	HTML: Sem�ntica b�sica, CSS: Flexbox, JS: Manipulaci�n DOM, Backend: Crear Endpoint REST	\N	110	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0025 - -	Cierre tecnológico de edificios singulares de Almeróa	Baja	40	Hardware: Inventario Activos, Hardware: Limpieza Interna	25, 15	cerrado	Hardware: Inventario Activos, Hardware: Limpieza Interna	\N	40	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0029 - -	Desmantelamiento sistema legado	Baja	75	SQL: Backup DB, Windows: Gesti�n Servicios, Hardware: Inventario Activos	30, 20, 25	En analisis	SQL: Backup DB, Windows: Gesti�n Servicios, Hardware: Inventario Activos	\N	75	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0032 - -	Firma Digital	Alta	60	Seguridad: Phishing ID, Seguridad: Permisos Carpeta	30, 30	cerrado	Seguridad: Phishing ID, Seguridad: Permisos Carpeta	\N	60	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0034 - -	Infraestructura de red para el centro financiero BCC	Alta	85	Redes: Crimpar RJ45, Redes: VLAN Config Switch, Redes: Port Security	20, 40, 25	pendiente	Redes: Crimpar RJ45, Redes: VLAN Config Switch, Redes: Port Security	\N	85	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0035 - -	Mejora resiliencia arquitectura de entornos clave	Media	65	SQL: Backup DB, Cloud: Security Groups	35, 30	en ejecucion	SQL: Backup DB, Cloud: Security Groups	\N	65	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0036 - -	Mejorar seguridad de acceso de usuarios a servicios	Alta	55	Seguridad: Configurar MFA, AD: Grupos Seguridad	30, 25	en revision	Seguridad: Configurar MFA, AD: Grupos Seguridad	\N	55	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0037 - -	Microsoft Fabric Nuevo Entorno	Media	65	Cloud: Crear Bucket, SQL: Select Simple	35, 30	En analisis	Cloud: Crear Bucket, SQL: Select Simple	\N	65	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0039 - -	Nueva plataforma Swift CBPR+	Media	55	Redes: IP/Gateway, Redes: IP Est�tica Config	25, 30	cerrado	Redes: IP/Gateway, Redes: IP Est�tica Config	\N	55	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0040 - -	Nuevo modelo de gestion de Ticketing	Media	80	Ticket: Registro Incidencia, Ticket: Priorizaci�n, Ticket: Escalado Nivel	30, 25, 25	en ejecucion	Ticket: Registro Incidencia, Ticket: Priorizaci�n, Ticket: Escalado Nivel	\N	80	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0041 - -	Plan de sistemas inteligentes	Media	70	Doc: Escribir Documentaci�n, Cloud: VM Start/Stop	45, 25	en cierre	Doc: Escribir Documentaci�n, Cloud: VM Start/Stop	\N	70	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0004 - [9470-2023]	Renovación de hardware de CyberArk	Media	25	Hardware: Instalar RAM, Hardware: Cambiar Disco, Hardware: Inventario Activos	5, 10, 10	cerrado	Hardware: Instalar RAM, Hardware: Cambiar Disco, Hardware: Inventario Activos	\N	25	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0007 - [PRE2022]	Migración Simep entorno linux	Media	45	Linux: Gesti�n Archivos, Linux: SSH Conexi�n, Linux: Edici�n (Nano/Vim)	15, 10, 20	Standby	Linux: Gesti�n Archivos, Linux: SSH Conexi�n, Linux: Edici�n (Nano/Vim)	\N	45	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0043 - -	Renovar plataforma de autenticación de administradores	Media	50	AD: Grupos Seguridad, Seguridad: Configurar MFA	25, 25	en revision	AD: Grupos Seguridad, Seguridad: Configurar MFA	\N	50	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0045 - -	Sistema Apertura remota Racks-Cajetín	Baja	35	Redes: Crimpar RJ45, Hardware: Diagn�stico Fuent	15, 20	cerrado	Redes: Crimpar RJ45, Hardware: Diagn�stico Fuent	\N	35	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0046 - -	Uso de tecnologías para contenerizaciín de aplicaciones	Media	90	Docker: Run Container, Docker: Logs, Docker: Exec	40, 25, 25	en ejecucion	Docker: Run Container, Docker: Logs, Docker: Exec	\N	90	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0009 - [PRE2022]	Rearquitectura de la red de los Data Centers	Media	150	Redes: Netstat, Redes: VLAN Config Switch, Redes: Tracert	40, 80, 30	en cierre	Redes: Netstat, Redes: VLAN Config Switch, Redes: Tracert	\N	150	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0010 - [PRE2023]	Migración Infraestructura y Swift Alliance 7,7	Media	65	Windows: Unir a Dominio, Redes: IP/Gateway, Redes: IP Est�tica Config	15, 20, 30	cerrado	Windows: Unir a Dominio, Redes: IP/Gateway, Redes: IP Est�tica Config	\N	65	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0013 - [PRE2024]	Reestructuración de la redes de chasis Synergy	Media	90	Redes: VLAN Config Switch, Hardware: Diagn�stico Fuent, Redes: IP Est�tica Config	40, 30, 20	en revision	Redes: VLAN Config Switch, Hardware: Diagn�stico Fuent, Redes: IP Est�tica Config	\N	90	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0014 - -	Actualización VerisecUP	Alta	30	Windows: Gesti�n Servicios, Windows: Visor Eventos	15, 15	Standby	Windows: Gesti�n Servicios, Windows: Visor Eventos	\N	30	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0017 - -	Adopción e implantación plataforma datos analóticos IA	Media	85	Cloud: Crear Bucket, Cloud: Subir Archivos, SQL: Select Simple	30, 20, 35	cerrado	Cloud: Crear Bucket, Cloud: Subir Archivos, SQL: Select Simple	\N	85	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0019 - -	Ampliación de la capacidad de sistemas de copia en cinta	Alta	25	Hardware: Cambiar Disco, Hardware: Impresora en Red	15, 10	pendiente	Hardware: Cambiar Disco, Hardware: Impresora en Red	\N	25	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0020 - -	Ampliación infraestructura Plataforma Contenedores	Media	70	Docker: Run Container, Docker: Listar, Docker: Prune	30, 15, 25	en revision	Docker: Run Container, Docker: Listar, Docker: Prune	\N	70	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0021 - -	Ampliación Infraestructura QLik	Media	35	Windows: Gesti�n Servicios, Hardware: Instalar RAM	20, 15	en ejecucion	Windows: Gesti�n Servicios, Hardware: Instalar RAM	\N	35	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0027 - -	Definición e implantación mapa herramientas	Baja	60	Doc: Escribir Documentaci�n, Hardware: Inventario Activos	40, 20	pendiente	Doc: Escribir Documentaci�n, Hardware: Inventario Activos	\N	60	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0028 - -	Definición e implementación de CCoE	Media	95	Agile: Daily Standup, Cloud: VM Start/Stop, Cloud: Security Groups	25, 30, 40	en revision	Agile: Daily Standup, Cloud: VM Start/Stop, Cloud: Security Groups	\N	95	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0030 - -	Evolución del puesto de trabajo - Modern Workplace	Media	50	Windows: Unir a Dominio, Windows: PowerShell B�sico, Hardware: Instalar RAM	15, 25, 10	en ejecucion	Windows: Unir a Dominio, Windows: PowerShell B�sico, Hardware: Instalar RAM	\N	50	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0031 - -	Evolución del puesto de trabajo (Clóster SQL Server)	Media	85	Windows: Gesti�n Servicios, SQL: Select Simple, SQL: Create Table	20, 25, 40	Standby	Windows: Gesti�n Servicios, SQL: Select Simple, SQL: Create Table	\N	85	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0038 - -	Migración Servidor Financiero entorno Linux	Alta	45	Linux: Gesti�n Archivos, Linux: SSH Conexi�n	25, 20	Standby	Linux: Gesti�n Archivos, Linux: SSH Conexi�n	\N	45	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0042 - -	Renovación infraestructura Clearpass NAC	Alta	75	Redes: Port Security, API: Auth JWT	40, 35	pendiente	Redes: Port Security, API: Auth JWT	\N	75	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0044 - -	Segmentación activos de red (Fase 2)	Media	85	Redes: VLAN Config Switch, Redes: DNS Registros	50, 35	En analisis	Redes: VLAN Config Switch, Redes: DNS Registros	\N	85	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
PRJ0033 - -	Gestion cartera de Proyectos y Anólisis nueva demanda	Media	70	Agile: Estimaci�n Tareas, Ticket: Priorizaci�n	40, 30	en cierre	Agile: Estimaci�n Tareas, Ticket: Priorizaci�n	\N	70	2026-03-19 21:44:12.462592	2026-03-19 21:44:12.462592	\N	[]
\.


ALTER TABLE public.cartera_build ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

\unrestrict fAxE6MSF6r1uQNSthUANV6fXNbzXNI1NG24XoiWboDczs5letnfKcN2yL4ymLU1

