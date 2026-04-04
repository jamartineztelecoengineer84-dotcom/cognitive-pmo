--
-- PostgreSQL database dump
--

\restrict mUEsNOTNGNntKEuWniFLTD3FOnsiATSOBDReuiyRsD6DNUYm4o8Kq70pDwXenGe

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
-- Data for Name: build_stakeholders; Type: TABLE DATA; Schema: public; Owner: -
--

SET SESSION AUTHORIZATION DEFAULT;

ALTER TABLE public.build_stakeholders DISABLE TRIGGER ALL;

COPY public.build_stakeholders (id, id_proyecto, nombre, cargo, area, nivel_poder, nivel_interes, estrategia, rol_raci, frecuencia_comunicacion, canal, id_directivo, created_at) FROM stdin;
e252414c-c9fe-42b5-8306-6a428afe8070	RHEL7-RHEL9-MIG-2026	Antonio Vega Serrano	Director de Trading y Mercados	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-051	2026-03-23 12:23:26.853092
986b8756-b3d0-41d6-85ba-d6b1202cdf75	RHEL7-RHEL9-MIG-2026	Patricia Álvarez Soto	Responsable de Cotizaciones y Divisas	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-060	2026-03-23 12:23:26.870631
f8e057b9-5b58-4227-a933-688d8f240525	RHEL7-RHEL9-MIG-2026	Víctor Gallego Ramos	Responsable de Mercado de Capitales	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-082	2026-03-23 12:23:26.887106
39da5116-5978-4819-b2fe-b76d57c2ef4b	RHEL7-RHEL9-MIG-2026	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-23 12:23:26.89317
d730ba13-5cf5-47ba-901c-c83f1c32b72c	RHEL7-RHEL9-MIG-2026	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-23 12:23:26.896311
a3425711-f5dd-49e4-a2be-d401deb07432	RHEL7-RHEL9-MIG-2026	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-052	2026-03-23 12:23:26.901812
ba402794-ccd5-4c7b-894d-bb26d61da9db	RHEL7-RHEL9-MIG-2026	Silvia Herrero Campos	Responsable de Banca Móvil	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-062	2026-03-23 12:23:26.904908
1f9cad2a-bed8-45e6-a93e-4083f799c89e	RHEL7-RHEL9-MIG-2026	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-23 12:23:26.910355
7df7558e-2e1f-4342-a056-d0f2a6b3af36	RHEL7-RHEL9-MIG-2026	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-23 12:23:26.913325
1ad2ea85-9cfa-4d58-a5f9-e59d620080bf	RHEL7-RHEL9-MIG-2026	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-23 12:23:26.915285
b15e8070-e539-458e-ac1c-a1cd629f0c99	RHEL7-RHEL9-MIG-2026	Javier Martín Blanco	Director de Cajeros y Medios de Pago	Medios de Pago	2	4	Mantener informado	C	Quincenal	Email	DIR-057	2026-03-23 12:23:26.925423
6237b620-6058-4cf7-88c2-23da7797be32	RHEL7-RHEL9-MIG-2026	Susana Gil Navarro	Responsable de Cajeros y ATM	Medios de Pago	2	4	Mantener informado	C	Quincenal	Email	DIR-107	2026-03-23 12:23:26.927333
886bc515-cdde-403a-bba5-ca6568176db5	RHEL7-RHEL9-MIG-2026	Elena Marquez Aguirre	CISO - Chief Information Security Officer	Ciberseguridad	2	4	Mantener informado	C	Quincenal	Email	DIR-004	2026-03-23 12:23:26.937638
17c62d19-3cb2-4372-b1bc-bf8583e0431c	OPENSHIFT-2026	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-052	2026-03-23 12:44:50.468468
39d13431-d737-4157-a61f-eb8441ae3c6b	OPENSHIFT-2026	Silvia Herrero Campos	Responsable de Banca Móvil	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-062	2026-03-23 12:44:50.471121
3c38bfe4-e0d2-47ad-92e2-ec8a7db5f730	OPENSHIFT-2026	Antonio Vega Serrano	Director de Trading y Mercados	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-051	2026-03-23 12:44:50.476786
171629ee-859f-48f2-bc79-0a598e02a514	OPENSHIFT-2026	Patricia Álvarez Soto	Responsable de Cotizaciones y Divisas	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-060	2026-03-23 12:44:50.478571
f14951f6-8e46-4195-b21d-9c373fa9d2c8	OPENSHIFT-2026	Víctor Gallego Ramos	Responsable de Mercado de Capitales	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-082	2026-03-23 12:44:50.48152
743dda06-7d43-42b5-9c60-1be519029635	OPENSHIFT-2026	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-23 12:44:50.486364
15b1092f-377b-4b98-ac41-46817c0484d1	OPENSHIFT-2026	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-23 12:44:50.489229
50bd4cdf-821b-4c71-90a9-5c7963ae314e	OPENSHIFT-2026	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-23 12:44:50.493586
1b94b8ee-00aa-48b2-87a0-1ff6fd74891b	OPENSHIFT-2026	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-23 12:44:50.496867
9ebfc338-5de0-4ed9-adf1-90814206b427	OPENSHIFT-2026	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-23 12:44:50.498926
66f112a0-780e-4f5c-9246-aac8f82a6331	OPENSHIFT-2026	María José Fernández Gil	Directora de Riesgos	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-054	2026-03-23 12:44:50.505794
30eaa552-f225-447e-ba80-52f57db09d19	OPENSHIFT-2026	Andrés Navarro Ponce	Responsable de Prevención de Fraude	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-063	2026-03-23 12:44:50.507891
cb771325-02e4-45f2-8d7a-51b3a2ab0ece	OPENSHIFT-2026	Carmen Delgado Ríos	CTO - Chief Technology Officer	Tecnología	2	4	Mantener informado	C	Quincenal	Email	DIR-002	2026-03-23 12:44:50.513675
6a80238b-2dfc-4b02-b3e6-193c6d534ed2	Plataforma de Contenedores OpenShift On-Premise	Antonio Vega Serrano	Director de Trading y Mercados	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-051	2026-03-23 22:46:27.27126
7c89b84e-0810-47bb-9a12-0d9d96cef2bc	Plataforma de Contenedores OpenShift On-Premise	Patricia Álvarez Soto	Responsable de Cotizaciones y Divisas	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-060	2026-03-23 22:46:27.27933
666ffc84-908b-4bb8-ad07-9e2753975c2d	Plataforma de Contenedores OpenShift On-Premise	Víctor Gallego Ramos	Responsable de Mercado de Capitales	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-082	2026-03-23 22:46:27.284307
d29e2d23-7128-4be1-93bf-0c3533754adc	Plataforma de Contenedores OpenShift On-Premise	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-23 22:46:27.29363
e080ab71-617e-4e32-b5bb-0721c7bb62fb	Plataforma de Contenedores OpenShift On-Premise	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-23 22:46:27.297326
bb8fc1a1-097f-4ea5-8e72-ced7008cd745	Plataforma de Contenedores OpenShift On-Premise	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-052	2026-03-23 22:46:27.307025
2bf0cb2b-ce98-43f1-9cd7-32ac9c36c537	Plataforma de Contenedores OpenShift On-Premise	Silvia Herrero Campos	Responsable de Banca Móvil	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-062	2026-03-23 22:46:27.310626
d6e7c4ce-724c-4187-871e-bc918b378194	Plataforma de Contenedores OpenShift On-Premise	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-23 22:46:27.318938
18b3664c-7eb7-4ac3-b7fc-01a502a8fd74	Plataforma de Contenedores OpenShift On-Premise	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-23 22:46:27.322489
1aa9e757-3530-4edd-80e3-c01d84a3ce9d	Plataforma de Contenedores OpenShift On-Premise	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-23 22:46:27.325281
c5ab35d0-ab9b-484a-8b9b-b68b5104175e	Plataforma de Contenedores OpenShift On-Premise	María José Fernández Gil	Directora de Riesgos	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-054	2026-03-23 22:46:27.333972
9492529a-8940-4201-845b-70a565415aa9	Plataforma de Contenedores OpenShift On-Premise	Andrés Navarro Ponce	Responsable de Prevención de Fraude	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-063	2026-03-23 22:46:27.337459
dfa329f5-2b23-4588-a44f-c044339c533f	Plataforma de Contenedores OpenShift On-Premise	Miguel Ángel Torres Ruiz	Director de RRHH	Recursos Humanos	2	4	Mantener informado	C	Quincenal	Email	DIR-059	2026-03-23 22:46:27.344
f675a6fa-d29a-462f-8b16-dbfedc9fe584	Plataforma de Contenedores OpenShift On-Premise	Alberto Fuentes Carrasco	Responsable de Nóminas	Recursos Humanos	2	4	Mantener informado	C	Quincenal	Email	DIR-080	2026-03-23 22:46:27.347252
451cb30d-e908-4291-b664-1eb83c81f10b	PROJ-OpenShift-2026	Antonio Vega Serrano	Director de Trading y Mercados	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-051	2026-03-24 10:03:24.593985
f1f353d0-938f-4da2-9897-f985d05eb04e	PROJ-OpenShift-2026	Patricia Álvarez Soto	Responsable de Cotizaciones y Divisas	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-060	2026-03-24 10:03:24.624767
ed8b0941-5f2c-48b6-8d2e-2e5f70c5fe13	PROJ-OpenShift-2026	Víctor Gallego Ramos	Responsable de Mercado de Capitales	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-082	2026-03-24 10:03:24.639706
02549325-5eba-4399-a66d-9aac70eeba9d	PROJ-OpenShift-2026	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-24 10:03:24.656795
8479d607-a2b5-47ce-b23f-f176adbb506d	PROJ-OpenShift-2026	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-24 10:03:24.660788
693df516-b83a-4bd2-b019-b4c35f750c34	PROJ-OpenShift-2026	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-052	2026-03-24 10:03:24.671692
edf78206-141e-4689-aae7-7c7c26094166	PROJ-OpenShift-2026	Silvia Herrero Campos	Responsable de Banca Móvil	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-062	2026-03-24 10:03:24.674578
4a250a67-6450-42fe-b498-4645f83443d0	PROJ-OpenShift-2026	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-24 10:03:24.684639
aaf34685-4bf6-4e87-ad52-e089a084189d	PROJ-OpenShift-2026	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-24 10:03:24.687239
fea4531b-5cb5-44e3-9f43-2f6fdb836c46	PROJ-OpenShift-2026	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-24 10:03:24.691228
d059882a-ea10-48c0-8c5c-b312b1a64de8	PROJ-OpenShift-2026	Laura Sanz Bermejo	Directora de Desarrollo Backend	Backend Engineering	2	4	Mantener informado	C	Quincenal	Email	DIR-020	2026-03-24 10:03:24.699828
c66f1f57-350e-4367-b9dc-8a21502adc41	PROJ-OpenShift-2026	Marina Nieto Calvo	Jefa de Equipo - Backend	Backend Engineering	2	4	Mantener informado	C	Quincenal	Email	DIR-043	2026-03-24 10:03:24.703581
dc3bea8a-d91c-4a82-9b5e-25dfae031a29	PROJ-OpenShift-2026	Raquel Sánchez Blanco	Jefa de Equipo - Backend Senior	Backend Engineering	2	4	Mantener informado	C	Quincenal	Email	DIR-044	2026-03-24 10:03:24.706098
d829e39d-9ebf-4b47-889e-3139c75fe4fe	Modelo de gestión de secretos	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-24 12:43:18.140038
fa0c94cb-93d8-4916-ad12-2962822104ee	Modelo de gestión de secretos	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-24 12:43:18.147965
a371c73a-82cf-4cae-8814-5ba85b105e64	Modelo de gestión de secretos	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-24 12:43:18.164194
528bc2f4-9f29-4513-be41-54b96fb82431	Modelo de gestión de secretos	María José Fernández Gil	Directora de Riesgos	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-054	2026-03-24 12:43:18.175782
c6857b09-3e7e-4d0a-a979-945eaf7f923e	Modelo de gestión de secretos	Andrés Navarro Ponce	Responsable de Prevención de Fraude	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-063	2026-03-24 12:43:18.180275
cef989a9-f809-497f-9eeb-9b4ce13d6241	Modelo de gestión de secretos	Antonio Vega Serrano	Director de Trading y Mercados	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-051	2026-03-24 12:43:18.191301
67d263bf-0495-4be1-8155-318f56f7eb53	Modelo de gestión de secretos	Patricia Álvarez Soto	Responsable de Cotizaciones y Divisas	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-060	2026-03-24 12:43:18.195889
b736daba-4c02-457c-a270-b36780d7d545	Modelo de gestión de secretos	Víctor Gallego Ramos	Responsable de Mercado de Capitales	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-082	2026-03-24 12:43:18.199273
47f9dda3-b8f3-4708-b16c-34fb658c94c0	Modelo de gestión de secretos	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-24 12:43:18.212101
912d62ea-27a8-4c8e-a6e9-54d6ffacd453	Modelo de gestión de secretos	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-24 12:43:18.215984
d35ef65e-9877-446f-a3d0-bb62bba78240	Modelo de gestión de secretos	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-052	2026-03-24 12:43:18.227639
3e80d189-383d-4132-98dc-dda783e68ed9	Modelo de gestión de secretos	Silvia Herrero Campos	Responsable de Banca Móvil	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-062	2026-03-24 12:43:18.231171
e3259ec4-1525-4d2a-94eb-e56b66932aa2	Modelo de gestión de secretos	Daniel Prieto Gallardo	Gerente de Proyecto - Seguridad	PMO - Seguridad	2	4	Mantener informado	C	Quincenal	Email	DIR-032	2026-03-24 12:43:18.242571
ba963b1b-448c-4a05-91dc-6e53ef477e37	PROY-2026-001	Antonio Vega Serrano	Director de Trading y Mercados	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-051	2026-03-24 17:13:44.051539
331151bc-3e40-4f1c-8c56-4781b7c714c1	PROY-2026-001	Patricia Álvarez Soto	Responsable de Cotizaciones y Divisas	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-060	2026-03-24 17:13:44.081945
af6c1f07-77a9-4d9f-bc82-97b8b017a905	PROY-2026-001	Víctor Gallego Ramos	Responsable de Mercado de Capitales	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-082	2026-03-24 17:13:44.094392
72515008-cd86-4295-8aa2-32023a31d5e8	PROY-2026-001	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-24 17:13:44.099821
7dbb80c6-5def-472b-8a5c-a0a99024c7dc	PROY-2026-001	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-24 17:13:44.103072
bc8333c8-071b-47db-ba92-d48bc40639d7	PROY-2026-001	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-052	2026-03-24 17:13:44.111029
e209e278-9192-4720-9407-a794d1bfc600	PROY-2026-001	Silvia Herrero Campos	Responsable de Banca Móvil	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-062	2026-03-24 17:13:44.113345
1250ced9-28d5-4c42-8df6-70fbe9122389	PROY-2026-001	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-24 17:13:44.119293
2a90e347-ba15-4e47-85c6-8cf80ecfe290	PROY-2026-001	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-24 17:13:44.1212
52ae663f-0eac-4784-8d4a-3af653fc0958	PROY-2026-001	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-24 17:13:44.124061
498395e9-ac68-4278-add5-0b1d6639767d	PROY-2026-001	María José Fernández Gil	Directora de Riesgos	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-054	2026-03-24 17:13:44.1309
7f2cd4f0-15a2-4761-8321-3b76de23c180	PROY-2026-001	Andrés Navarro Ponce	Responsable de Prevención de Fraude	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-063	2026-03-24 17:13:44.133734
dbbe5f7a-3df4-4eef-a754-9263496d4652	PROY-2026-001	Carmen Delgado Ríos	CTO - Chief Technology Officer	Tecnología	2	4	Mantener informado	C	Quincenal	Email	DIR-002	2026-03-24 17:13:44.138236
0b85ead2-c640-468b-ac9e-15db94c278d4	IDQ-PREPROD-2026	Antonio Vega Serrano	Director de Trading y Mercados	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-051	2026-03-24 17:40:09.925833
cc4aea80-e52d-4d25-9587-9694e56880f6	IDQ-PREPROD-2026	Patricia Álvarez Soto	Responsable de Cotizaciones y Divisas	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-060	2026-03-24 17:40:09.958027
057c82cd-6af2-476c-a809-03d595bbc5a0	IDQ-PREPROD-2026	Víctor Gallego Ramos	Responsable de Mercado de Capitales	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-082	2026-03-24 17:40:09.97198
c21fb851-1f48-434d-942c-f776c77a5fea	IDQ-PREPROD-2026	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-24 17:40:09.978117
ae2c1ab1-f44c-4302-8d2d-1cc19c73de16	IDQ-PREPROD-2026	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-24 17:40:09.981772
c6d32799-f685-4899-a210-c4930afabdcc	IDQ-PREPROD-2026	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-24 17:40:09.988629
d81e12f9-cdf2-43cd-9c5f-3ab821e274aa	IDQ-PREPROD-2026	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-24 17:40:09.991915
193d0189-d001-4923-8dda-eb5d2342bb0a	IDQ-PREPROD-2026	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-24 17:40:09.993896
fca9ec2b-fea3-4074-9c68-0edf0b976951	IDQ-PREPROD-2026	María José Fernández Gil	Directora de Riesgos	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-054	2026-03-24 17:40:10.001522
76655134-12c4-4dc6-9d9c-1656219c7f44	IDQ-PREPROD-2026	Andrés Navarro Ponce	Responsable de Prevención de Fraude	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-063	2026-03-24 17:40:10.003442
3880dc40-ce55-4e30-8bb3-b9642c52a5e2	IDQ-PREPROD-2026	Daniel Prieto Gallardo	Gerente de Proyecto - Seguridad	PMO - Seguridad	2	4	Mantener informado	C	Quincenal	Email	DIR-032	2026-03-24 17:40:10.008681
30fc6094-80bd-4610-a538-e9d46233b806	PROJ-2026-001	Antonio Vega Serrano	Director de Trading y Mercados	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-051	2026-03-24 22:01:25.860607
927e180b-18f2-4107-a3c5-d51e3792b780	PROJ-2026-001	Patricia Álvarez Soto	Responsable de Cotizaciones y Divisas	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-060	2026-03-24 22:01:25.869132
dfdd24e6-5db6-4738-81b0-194fac8f8146	PROJ-2026-001	Víctor Gallego Ramos	Responsable de Mercado de Capitales	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-082	2026-03-24 22:01:25.872042
25d0f6f0-18a0-4067-89a4-81f582989d3d	PROJ-2026-001	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-24 22:01:25.881271
c6d626c2-8e75-44d8-92e4-8023b2673ce9	PROJ-2026-001	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-24 22:01:25.884273
83da85f7-af31-4a18-98f2-585538d8e01a	PROJ-2026-001	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-052	2026-03-24 22:01:25.893522
7130aa16-c14d-4ce3-b6f5-714f03843a8c	PROJ-2026-001	Silvia Herrero Campos	Responsable de Banca Móvil	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-062	2026-03-24 22:01:25.896519
8e29ddc5-cf87-40ce-8e79-036048aac519	PROJ-2026-001	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-24 22:01:25.905692
e9418533-9f0b-4cc9-8177-f3faceaba598	PROJ-2026-001	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-24 22:01:25.908547
4278ffad-401b-4502-8bb9-65f06f8e48b8	PROJ-2026-001	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-24 22:01:25.912403
5ffa7894-1207-4e8a-9c0c-27879d4a13c5	PROJ-2026-001	Javier Iglesias Roca	Director de Infraestructura & Redes	Infraestructura	2	4	Mantener informado	C	Quincenal	Email	DIR-023	2026-03-24 22:01:25.920919
b21eefdb-88e1-4526-b993-e372072b0b92	PROJ-2026-001	Pablo Rivas Camacho	Gerente de Proyecto - Infraestructura	PMO - Infraestructura	2	4	Mantener informado	C	Quincenal	Email	DIR-030	2026-03-24 22:01:25.92523
a97dcd67-6e59-4a67-af11-aacddf8a0394	ARES-WEBLOGIC-2026	Javier Martín Blanco	Director de Cajeros y Medios de Pago	Medios de Pago	2	4	Mantener informado	C	Quincenal	Email	DIR-057	2026-03-24 22:16:19.398439
f140f290-ac0c-43ee-8b1b-026dc86fbcb6	ARES-WEBLOGIC-2026	Susana Gil Navarro	Responsable de Cajeros y ATM	Medios de Pago	2	4	Mantener informado	C	Quincenal	Email	DIR-107	2026-03-24 22:16:19.433987
8f5f4775-eda3-4536-be7d-9b5759cef6ed	ARES-WEBLOGIC-2026	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-24 22:16:19.454314
82d46d6f-7fce-467d-8c64-0f068c960665	ARES-WEBLOGIC-2026	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-24 22:16:19.459246
4b08b643-adae-4140-8c31-e44edf1dcfa0	ARES-WEBLOGIC-2026	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-24 22:16:19.469452
c9dcdac3-00d1-49eb-b514-5c702798b54c	ARES-WEBLOGIC-2026	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-24 22:16:19.474625
bad7adba-905c-4d5e-9462-418f3f4b4f62	ARES-WEBLOGIC-2026	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-24 22:16:19.478065
6f3950c4-277a-4e70-bb7d-506419c8526a	ARES-WEBLOGIC-2026	Pablo Rivas Camacho	Gerente de Proyecto - Infraestructura	PMO - Infraestructura	2	4	Mantener informado	C	Quincenal	Email	DIR-030	2026-03-24 22:16:19.49037
7e229829-1c07-463f-b3f2-e9f60b913ac5	ARES-WEBLOGIC-2026	Cristina Vega Salinas	Gerente de Proyecto - Aplicaciones	PMO - Aplicaciones	2	4	Mantener informado	C	Quincenal	Email	DIR-031	2026-03-24 22:16:19.502347
18cbd151-0b91-47d3-91a5-6beda2259be1	NAC-2026-001	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-25 10:58:34.768992
578b8f16-3b07-4937-9ecf-1da7394e03d4	NAC-2026-001	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-25 10:58:34.781054
b6d1d3ea-1bd0-4830-a7d4-9956dfde7ffa	NAC-2026-001	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-25 10:58:34.785271
c47a9150-da18-4439-a9fa-4aa665ec2354	NAC-2026-001	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-25 10:58:34.799022
a32f3713-295a-4a21-990b-adc347351003	NAC-2026-001	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-25 10:58:34.802466
0d369070-de63-448e-a965-9a3cb864a1b4	NAC-2026-001	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-052	2026-03-25 10:58:34.815055
25e4db1e-607f-4bd7-b2fb-bdfa6b8501b5	NAC-2026-001	Silvia Herrero Campos	Responsable de Banca Móvil	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-062	2026-03-25 10:58:34.818401
e7230e0d-cc2c-47a4-a53c-845d366fde38	NAC-2026-001	Lucía Pérez Ortega	Directora de Atención al Cliente	Atención al Cliente	2	4	Mantener informado	C	Quincenal	Email	DIR-058	2026-03-25 10:58:34.835284
194f162f-5d20-4ed4-9f40-60bdffdf5ee2	NAC-2026-001	Daniel Prieto Gallardo	Gerente de Proyecto - Seguridad	PMO - Seguridad	2	4	Mantener informado	C	Quincenal	Email	DIR-032	2026-03-25 10:58:34.848874
db71ea03-eddb-430a-aa4b-2db3a2316a44	PROJ-2026-001	Antonio Vega Serrano	Director de Trading y Mercados	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-051	2026-03-25 11:38:01.239718
e6260a75-f83b-473c-8735-0b8f0566f784	PROJ-2026-001	Patricia Álvarez Soto	Responsable de Cotizaciones y Divisas	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-060	2026-03-25 11:38:01.246342
387fe3da-4d29-4266-a82b-b939c2abddbe	PROJ-2026-001	Víctor Gallego Ramos	Responsable de Mercado de Capitales	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-082	2026-03-25 11:38:01.248579
d34821d4-93f9-4114-8de1-bdb8c5570a93	PROJ-2026-001	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-25 11:38:01.256505
7662c0f1-89bc-4a05-bdaf-d9ca089efab7	PROJ-2026-001	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-25 11:38:01.258912
de492670-bc98-46f0-a9e4-13e039d2dcc0	PROJ-2026-001	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-25 11:38:01.265958
81d348af-43a9-4a0f-a9e8-1de4f46a3013	PROJ-2026-001	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-25 11:38:01.268238
62c004f3-d05f-46c8-924c-d93013fa94d2	PROJ-2026-001	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-25 11:38:01.271599
bcf6b5a5-d49d-449b-9a3d-28eecca67415	PROJ-2026-001	María José Fernández Gil	Directora de Riesgos	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-054	2026-03-25 11:38:01.278358
6129f1dc-6abc-490f-b2b1-50f20dbfae7a	PROJ-2026-001	Andrés Navarro Ponce	Responsable de Prevención de Fraude	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-063	2026-03-25 11:38:01.281668
6af13c0e-cde1-44d8-b2c6-978acd1eaa30	PROJ-2026-001	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-052	2026-03-25 11:38:01.287493
bc762f20-a81a-46b4-9e16-b7aaa20fd427	PROJ-2026-001	Silvia Herrero Campos	Responsable de Banca Móvil	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-062	2026-03-25 11:38:01.290809
b6802bb4-209a-4376-89ae-22269ef3ea60	PROJ-EXADATA-2026	Antonio Vega Serrano	Director de Trading y Mercados	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-051	2026-03-25 12:14:56.930736
e114b5c2-0f8a-47fc-b4d6-18ccfe0cd7b4	PROJ-EXADATA-2026	Patricia Álvarez Soto	Responsable de Cotizaciones y Divisas	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-060	2026-03-25 12:14:56.940198
02a6626d-4757-48b2-b646-7df83e225500	PROJ-EXADATA-2026	Víctor Gallego Ramos	Responsable de Mercado de Capitales	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-082	2026-03-25 12:14:56.944098
8b182722-1e2b-4b65-96c1-0660f61d3424	PROJ-EXADATA-2026	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-25 12:14:56.956067
da7feec1-8858-43cd-b49b-c87cbf76ead5	PROJ-EXADATA-2026	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-25 12:14:56.960809
9cfdc3bb-c91b-4747-bb2e-2dc57aadc098	PROJ-EXADATA-2026	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-25 12:14:56.975884
9eaf0a04-a874-43e4-8064-37517ebd9099	PROJ-EXADATA-2026	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-25 12:14:56.9795
c1e8430e-6ef0-410f-b540-31673a3fe3e6	PROJ-EXADATA-2026	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-25 12:14:56.983829
033848b7-d71d-4fe8-b2f9-dec7cece285e	PROJ-EXADATA-2026	María José Fernández Gil	Directora de Riesgos	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-054	2026-03-25 12:14:56.994978
9dcb8415-68a5-4d20-8155-f6faf67a19af	PROJ-EXADATA-2026	Andrés Navarro Ponce	Responsable de Prevención de Fraude	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-063	2026-03-25 12:14:56.99901
dc5b4de1-e66c-4d92-8e2a-b6a5b21fcbdd	PROJ-EXADATA-2026	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-052	2026-03-25 12:14:57.009159
85b6b920-2d20-4e27-9bac-3dcdb6b21cff	PROJ-EXADATA-2026	Silvia Herrero Campos	Responsable de Banca Móvil	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-062	2026-03-25 12:14:57.012763
a3106517-33be-46b0-acea-50392476c456	CCoE-2026-001	Antonio Vega Serrano	Director de Trading y Mercados	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-051	2026-03-25 20:51:31.232409
e0653e8a-c75e-446d-bb3c-58ece3b94983	CCoE-2026-001	Patricia Álvarez Soto	Responsable de Cotizaciones y Divisas	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-060	2026-03-25 20:51:31.240448
a62a533c-9fba-43bb-8ef3-44c3ff111447	CCoE-2026-001	Víctor Gallego Ramos	Responsable de Mercado de Capitales	Trading y Mercados	2	4	Mantener informado	C	Quincenal	Email	DIR-082	2026-03-25 20:51:31.245479
64223dca-be90-4bcb-8038-28701b1331ae	CCoE-2026-001	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-25 20:51:31.259085
f064c27d-2ad8-4fd0-b5be-764cc7d88028	CCoE-2026-001	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-25 20:51:31.263444
8cde33f5-6705-436c-a68a-e4ae9bf2ec8b	CCoE-2026-001	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-25 20:51:31.274093
ff3a0ff7-7b8a-44e9-89ea-ac027a4ad6be	CCoE-2026-001	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-25 20:51:31.277014
0df0f629-bbce-400d-bf5c-7f1d09608c4e	CCoE-2026-001	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-25 20:51:31.280996
2dcc5ead-f2a6-42fc-a1a0-f6346e18c584	CCoE-2026-001	María José Fernández Gil	Directora de Riesgos	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-054	2026-03-25 20:51:31.289514
dd06746b-47cf-45b1-9c8f-bbb9568311fc	CCoE-2026-001	Andrés Navarro Ponce	Responsable de Prevención de Fraude	Gestión de Riesgos	2	4	Mantener informado	C	Quincenal	Email	DIR-063	2026-03-25 20:51:31.293536
aae14796-f1f7-4bee-a333-b4960c7bf416	CCoE-2026-001	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-052	2026-03-25 20:51:31.301573
972142ce-7f2c-430e-a1d3-fa9d3ce2ba87	CCoE-2026-001	Silvia Herrero Campos	Responsable de Banca Móvil	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-062	2026-03-25 20:51:31.305595
1d4de7bd-2a9c-4289-ba0f-05a198669d65	Nuevo modelo de gestion de Ticketing	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-26 18:53:52.868129
044d4abd-0f70-4082-bb00-655f3ae49c85	Nuevo modelo de gestion de Ticketing	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-26 18:53:52.877227
8ecaa98b-6ba6-487d-967a-2cd92a5a93d8	Nuevo modelo de gestion de Ticketing	Lucía Pérez Ortega	Directora de Atención al Cliente	Atención al Cliente	2	4	Mantener informado	C	Quincenal	Email	DIR-058	2026-03-26 18:53:52.885063
fbcf55f7-f174-4e87-93d6-4b1f94653963	Nuevo modelo de gestion de Ticketing	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-26 18:53:52.893831
e2cb8acb-13ba-468f-90aa-d3e58b04f144	Nuevo modelo de gestion de Ticketing	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-26 18:53:52.897065
83fe75e5-6b00-4493-a945-c72ceca0730b	Nuevo modelo de gestion de Ticketing	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-26 18:53:52.900258
f6bfbf37-e991-4e53-bd29-f07822899b93	Nuevo modelo de gestion de Ticketing	Miguel Ángel Torres Ruiz	Director de RRHH	Recursos Humanos	2	4	Mantener informado	C	Quincenal	Email	DIR-059	2026-03-26 18:53:52.906242
64d1e67c-ea4b-4e6d-a616-ba5ebda67994	Nuevo modelo de gestion de Ticketing	Alberto Fuentes Carrasco	Responsable de Nóminas	Recursos Humanos	2	4	Mantener informado	C	Quincenal	Email	DIR-080	2026-03-26 18:53:52.909527
d4e138b0-bdc5-4924-a4b9-110938c2b968	Nuevo modelo de gestion de Ticketing	Gonzalo Fernández-Vega	VP of PMO	PMO Corporativa	2	4	Mantener informado	C	Quincenal	Email	DIR-012	2026-03-26 18:53:52.915074
904ce175-9aef-4a92-99e2-ede86d2a3a05	Nuevo modelo de gestion de Ticketing	Pablo Rivas Camacho	Gerente de Proyecto - Infraestructura	PMO - Infraestructura	2	4	Mantener informado	C	Quincenal	Email	DIR-030	2026-03-26 18:53:52.918277
7ec0032e-bbdb-4171-a1da-087625dd9267	Nuevo modelo de gestion de Ticketing	Cristina Vega Salinas	Gerente de Proyecto - Aplicaciones	PMO - Aplicaciones	2	4	Mantener informado	C	Quincenal	Email	DIR-031	2026-03-26 18:53:52.920313
e4b722ae-512c-4602-b66d-b99c18ddef03	PS-MN6IK6Y0	Francisco López Navarro	Director de Compliance y Regulación	Compliance	5	5	Gestionar de cerca	A	Semanal	Reunión	\N	2026-03-25 21:00:28.930417
fd0c3af2-2e19-4d7b-b974-af0ebdd81e21	PS-MN6IK6Y0	Daniel Prieto Gallardo	Gerente de Proyecto - Seguridad	PMO - Seguridad	4	5	Gestionar de cerca	R	Semanal	War Room	\N	2026-03-25 21:00:28.932177
025a51de-b1e0-40a2-9c18-f667e7f2ec5c	PS-MN6IK6Y0	Laura Sanz Bermejo	Directora de Desarrollo Backend	Backend Engineering	4	4	Gestionar de cerca	C	Semanal	Reunión	\N	2026-03-25 21:00:28.934724
11a8ccbc-db1f-4596-807b-95f637fc29b6	PS-MN6IK6Y0	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	4	3	Mantener satisfecho	C	Quincenal	Informe	\N	2026-03-25 21:00:28.936413
efe0595b-fdab-4e13-9536-9cc962b2f15f	PS-MN6IK6Y0	María José Fernández Gil	Directora de Riesgos	Gestión de Riesgos	4	3	Mantener satisfecho	C	Quincenal	Informe	\N	2026-03-25 21:00:28.93879
fba0ff4c-7041-4bb9-80d7-1c9d0a5370d6	PS-MN6IK6Y0	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	4	3	Mantener satisfecho	C	Quincenal	Informe	\N	2026-03-25 21:00:28.940215
525005a9-5332-4f48-b670-4a0954ac12ac	PS-MN6IK6Y0	Antonio Vega Serrano	Director de Trading y Mercados	Trading y Mercados	3	2	Mantener satisfecho	I	Mensual	Email	\N	2026-03-25 21:00:28.942633
652f903f-8bf2-410a-9f49-55312d260a82	PS-MN6IK6Y0	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Semanal	Dashboard	\N	2026-03-25 21:00:28.943943
195f1280-f523-4d74-a4a3-ddd27fe05a6d	PS-MN6IK6Y0	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	I	Semanal	Dashboard	\N	2026-03-25 21:00:28.946284
46a12fe4-2ab6-4dcb-a144-c43d27c3fad5	PS-MN6IK6Y0	Andrés Navarro Ponce	Responsable de Prevención de Fraude	Gestión de Riesgos	2	3	Mantener informado	I	Quincenal	Dashboard	\N	2026-03-25 21:00:28.947557
22d8598b-8f7d-491f-a662-ced94d4ada5f	PS-MN6IK6Y0	Silvia Herrero Campos	Responsable de Banca Móvil	Banca Digital	2	3	Mantener informado	I	Quincenal	Email	\N	2026-03-25 21:00:28.949973
91785865-3f12-4711-ba04-5a485767d5e0	PS-MN6IK6Y0	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	2	Monitorizar	I	Mensual	Email	\N	2026-03-25 21:00:28.951346
74cf779e-8c58-4227-a54e-2d1b6cc4da48	PS-MN7E7EQZ	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	4	5	Gestionar de cerca	A	Semanal	Reunión	\N	2026-03-26 18:59:13.817214
26925277-f3de-41b8-a15d-014c2718a887	PS-MN7E7EQZ	Lucía Pérez Ortega	Directora de Atención al Cliente	Atención al Cliente	4	5	Gestionar de cerca	R	Semanal	Reunión	\N	2026-03-26 18:59:13.820892
ff3afe5c-6b65-41d4-9989-ae30a3d860ef	PS-MN7E7EQZ	Francisco López Navarro	Director de Compliance y Regulación	Compliance	4	3	Mantener satisfecho	C	Quincenal	Informe	\N	2026-03-26 18:59:13.824156
de00754b-66a3-4e08-8be2-9b62f8655737	PS-MN7E7EQZ	Miguel Ángel Torres Ruiz	Director de RRHH	Recursos Humanos	3	4	Mantener informado	C	Quincenal	Dashboard	\N	2026-03-26 18:59:13.826435
add3fa4b-9a76-4379-bd53-d429ce365127	PS-MN7E7EQZ	Gonzalo Fernández-Vega	VP of PMO	PMO Corporativa	5	4	Mantener satisfecho	A	Quincenal	Informe	\N	2026-03-26 18:59:13.83026
36d6bf1a-2b37-4a01-88ec-a7c7dc7afa30	PS-MN7E7EQZ	Pablo Rivas Camacho	Gerente de Proyecto - Infraestructura	PMO - Infraestructura	3	5	Mantener informado	C	Semanal	Dashboard	\N	2026-03-26 18:59:13.83252
7f1eb043-9916-4b04-bce9-3c0f6fe1a6f2	PS-MN7E7EQZ	Cristina Vega Salinas	Gerente de Proyecto - Aplicaciones	PMO - Aplicaciones	3	5	Mantener informado	C	Semanal	Dashboard	\N	2026-03-26 18:59:13.835887
8b37e88a-a972-47aa-9bef-9d1963c43c4a	PS-MN7E7EQZ	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	I	Quincenal	Email	\N	2026-03-26 18:59:13.838197
d8099c17-b667-4463-94ef-c19d33bb6b19	PS-MN7E7EQZ	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	3	Monitorizar	I	Mensual	Email	\N	2026-03-26 18:59:13.841393
03534152-2138-4df5-a96b-03f28daed60e	PS-MN7E7EQZ	Alberto Fuentes Carrasco	Responsable de Nóminas	Recursos Humanos	2	3	Monitorizar	I	Mensual	Email	\N	2026-03-26 18:59:13.843445
974dcf5b-af73-48fe-bb13-a47a0f70a85c	CIERRE-ALMERIA-2026	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-050	2026-03-26 11:39:34.507837
fa82d9bc-0e57-435f-b614-d50cabcf1dc5	CIERRE-ALMERIA-2026	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	4	Mantener informado	C	Quincenal	Email	DIR-061	2026-03-26 11:39:34.519174
07fa73ad-f29b-4a36-848a-1f5d90f4ce51	CIERRE-ALMERIA-2026	Francisco López Navarro	Director de Compliance y Regulación	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-053	2026-03-26 11:39:34.530669
f9685962-cfae-42e5-b3f8-f619661a2da8	CIERRE-ALMERIA-2026	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-064	2026-03-26 11:39:34.535941
8d243a3b-111d-439d-9c83-fecdbbb1f198	CIERRE-ALMERIA-2026	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	C	Quincenal	Email	DIR-081	2026-03-26 11:39:34.539378
c322c616-9f85-4d30-899c-75f67c3837d3	CIERRE-ALMERIA-2026	Miguel Ángel Torres Ruiz	Director de RRHH	Recursos Humanos	2	4	Mantener informado	C	Quincenal	Email	DIR-059	2026-03-26 11:39:34.551583
3843b2ad-8e6b-4019-b3f2-9c64c7a96fef	CIERRE-ALMERIA-2026	Alberto Fuentes Carrasco	Responsable de Nóminas	Recursos Humanos	2	4	Mantener informado	C	Quincenal	Email	DIR-080	2026-03-26 11:39:34.555005
2e7e027d-4ff9-40ef-bd75-c2d6bc60e532	CIERRE-ALMERIA-2026	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-052	2026-03-26 11:39:34.56676
94108430-87e5-42d7-a83a-18acf6e01f20	CIERRE-ALMERIA-2026	Silvia Herrero Campos	Responsable de Banca Móvil	Banca Digital	2	4	Mantener informado	C	Quincenal	Email	DIR-062	2026-03-26 11:39:34.569999
f3c0d35c-0313-4e8c-8cf1-e0aae7cc4eeb	PS-TEST-001	Carmen Ruiz Delgado	Directora de Operaciones Bancarias	Operaciones Bancarias	5	5	Gestionar de cerca	A	Semanal	Reunión	\N	2026-03-25 20:04:40.684644
dc4d3734-103d-4c3d-9e59-a929b8d42748	PS-TEST-001	Francisco López Navarro	Director de Compliance y Regulación	Compliance	5	4	Mantener satisfecho	C	Quincenal	Informe	\N	2026-03-25 20:04:40.688593
0faf8d34-cb70-47ed-9d9c-49e0a5eb205e	PS-TEST-001	María José Fernández Gil	Directora de Riesgos	Gestión de Riesgos	4	5	Gestionar de cerca	C	Semanal	Reunión	\N	2026-03-25 20:04:40.690363
6bfba212-8879-4329-affb-d913d9bea60e	PS-TEST-001	Daniel Prieto Gallardo	Gerente de Proyecto - Seguridad	PMO - Seguridad	3	5	Mantener informado	R	Diaria	Dashboard	\N	2026-03-25 20:04:40.693019
67842023-80df-4594-a88d-4703a00955ea	PS-TEST-001	Laura Sanz Bermejo	Directora de Desarrollo Backend	Backend Engineering	3	4	Mantener informado	C	Semanal	Dashboard	\N	2026-03-25 20:04:40.694741
48b8272c-70bd-4950-976f-76379c9c5b19	PS-TEST-001	Antonio Vega Serrano	Director de Trading y Mercados	Trading y Mercados	4	3	Mantener satisfecho	C	Quincenal	Informe	\N	2026-03-25 20:04:40.697441
2564894f-0866-4097-8089-02cc6bad471e	PS-TEST-001	Isabel Moreno Castro	Directora de Banca Digital	Banca Digital	4	4	Gestionar de cerca	C	Semanal	Reunión	\N	2026-03-25 20:04:40.69931
59780582-8c63-4190-abb3-bae0fb5b73b0	PS-TEST-001	Daniel Romero Vidal	Responsable de Pagos Internacionales	Operaciones Bancarias	2	5	Mantener informado	I	Semanal	Email	\N	2026-03-25 20:04:40.702091
9d4ffdbc-fdf9-4875-aa8f-ce12189fb5f3	PS-TEST-001	Rosa Jiménez Lara	Responsable de Auditoría Interna	Compliance	3	3	Mantener informado	I	Mensual	Informe	\N	2026-03-25 20:04:40.703975
5831d3b8-7133-4d48-bb1b-5fe078462585	PS-TEST-001	Nuria Pascual Delgado	Responsable de Reporting Regulatorio	Compliance	2	4	Mantener informado	I	Quincenal	Email	\N	2026-03-25 20:04:40.707118
20633cd7-d828-45c7-8bed-56e62d542a3a	PS-TEST-001	Andrés Navarro Ponce	Responsable de Prevención de Fraude	Gestión de Riesgos	2	3	Monitorizar	I	Mensual	Email	\N	2026-03-25 20:04:40.708861
a7df83f0-53e5-43c3-b109-3bdcfac27f77	PS-TEST-001	Víctor Gallego Ramos	Responsable de Mercado de Capitales	Trading y Mercados	2	3	Monitorizar	I	Mensual	Email	\N	2026-03-25 20:04:40.711954
\.


ALTER TABLE public.build_stakeholders ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

\unrestrict mUEsNOTNGNntKEuWniFLTD3FOnsiATSOBDReuiyRsD6DNUYm4o8Kq70pDwXenGe

