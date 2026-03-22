-- ============================================================
-- CMDB: REGISTRO MASIVO DE IPs + VINCULACIÓN PROYECTOS-ACTIVOS
-- ============================================================

-- ═══ VLAN 10: MGMT-CORE (10.0.10.0/24) ═══
INSERT INTO cmdb_ips (direccion_ip,id_vlan,id_activo,hostname,tipo,estado,mac_address,notas) VALUES
('10.0.10.1',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-SW-001'),'sw-core-01.mgmt','ESTATICA','ASIGNADA','00:1A:2B:3C:4D:01','Switch Core Nexus - MGMT'),
('10.0.10.2',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-SW-002'),'sw-core-02.mgmt','ESTATICA','ASIGNADA','00:1A:2B:3C:4D:02','Switch Core Redundante'),
('10.0.10.3',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-FW-001'),'fw-norte.mgmt','ESTATICA','ASIGNADA','00:1A:2B:3C:4D:03','Firewall Perimetral Norte'),
('10.0.10.4',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-FW-002'),'fw-sur.mgmt','ESTATICA','ASIGNADA','00:1A:2B:3C:4D:04','Firewall Perimetral Sur'),
('10.0.10.5',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-FW-003'),'fw-interno.mgmt','ESTATICA','ASIGNADA','00:1A:2B:3C:4D:05','Firewall Interno Fortinet'),
('10.0.10.6',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-LB-001'),'lb-f5.mgmt','ESTATICA','ASIGNADA','00:1A:2B:3C:4D:06','Balanceador F5'),
('10.0.10.7',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-WAF-001'),'waf-f5.mgmt','ESTATICA','ASIGNADA','00:1A:2B:3C:4D:07','WAF F5 BIG-IP ASM'),
('10.0.10.8',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-SW-006'),'sw-fc-01.mgmt','ESTATICA','ASIGNADA','00:1A:2B:3C:4D:08','Switch FC Storage'),
('10.0.10.9',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-SW-007'),'sw-fc-02.mgmt','ESTATICA','ASIGNADA','00:1A:2B:3C:4D:09','Switch FC Storage Redundante'),
('10.0.10.10',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-RT-001'),'rt-wan-01.mgmt','ESTATICA','ASIGNADA','00:1A:2B:3C:4D:0A','Router WAN Principal'),
('10.0.10.11',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-RT-002'),'rt-wan-02.mgmt','ESTATICA','ASIGNADA','00:1A:2B:3C:4D:0B','Router WAN Backup'),
('10.0.10.12',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-AP-004'),'wlc-01.mgmt','ESTATICA','ASIGNADA','00:1A:2B:3C:4D:0C','WiFi Controller'),
('10.0.10.20',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),(SELECT id_activo FROM cmdb_activos WHERE codigo='UPS-001'),'ups-cpd-mad.mgmt','ESTATICA','ASIGNADA','00:1A:2B:3C:4D:14','SAI Principal SNMP'),
('10.0.10.30',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),NULL,'spare-mgmt-30','ESTATICA','LIBRE',NULL,'Reserva MGMT'),
('10.0.10.31',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=10),NULL,'spare-mgmt-31','ESTATICA','LIBRE',NULL,'Reserva MGMT')
ON CONFLICT (direccion_ip) DO NOTHING;

-- ═══ VLAN 20: SERVIDORES-PRO (10.0.20.0/24) ═══
INSERT INTO cmdb_ips (direccion_ip,id_vlan,id_activo,hostname,tipo,estado,mac_address,notas) VALUES
('10.0.20.10',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='SRV-PRO-001'),'srv-core-01.pro','ESTATICA','ASIGNADA','AA:BB:CC:01:01:01','Core Banking Principal'),
('10.0.20.11',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='SRV-PRO-002'),'srv-core-02.pro','ESTATICA','ASIGNADA','AA:BB:CC:01:01:02','Core Banking Secundario'),
('10.0.20.12',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='SRV-PRO-004'),'srv-pagos.pro','ESTATICA','ASIGNADA','AA:BB:CC:01:01:04','Pasarela de Pagos'),
('10.0.20.13',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='SRV-PRO-005'),'dc1.bank.local','ESTATICA','ASIGNADA','AA:BB:CC:01:01:05','Active Directory DC1'),
('10.0.20.14',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='SRV-PRO-006'),'dc2.bank.local','ESTATICA','ASIGNADA','AA:BB:CC:01:01:06','Active Directory DC2'),
('10.0.20.15',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='SRV-PRO-007'),'exchange-hybrid.pro','ESTATICA','ASIGNADA','AA:BB:CC:01:01:07','Exchange Hybrid'),
('10.0.20.16',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='SRV-PRO-008'),'fileserver.pro','ESTATICA','ASIGNADA','AA:BB:CC:01:01:08','File Server'),
('10.0.20.20',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-001'),'vm-contabilidad.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:01:01','VM Contabilidad'),
('10.0.20.21',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-002'),'vm-rrhh.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:01:02','VM RRHH'),
('10.0.20.22',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-003'),'vm-print.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:01:03','VM Print Server'),
('10.0.20.23',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-004'),'vm-proxy.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:01:04','VM Proxy Squid'),
('10.0.20.30',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-005'),'gitlab.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:02:01','GitLab Server'),
('10.0.20.31',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-006'),'jenkins.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:02:02','Jenkins CI/CD'),
('10.0.20.32',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-007'),'sonarqube.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:02:03','SonarQube'),
('10.0.20.33',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-008'),'nexus.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:02:04','Nexus Repository'),
('10.0.20.34',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-009'),'wsus.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:02:05','WSUS Server'),
('10.0.20.35',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-010'),'sccm.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:02:06','SCCM Server'),
('10.0.20.36',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-011'),'ansible.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:02:07','Ansible Tower'),
('10.0.20.37',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-012'),'vault.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:02:08','HashiCorp Vault'),
('10.0.20.38',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-013'),'ntp.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:02:09','NTP Server'),
('10.0.20.39',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-014'),'radius.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:02:0A','Radius Server'),
('10.0.20.40',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='VM-PRO-015'),'terraform.pro','ESTATICA','ASIGNADA','AA:BB:CC:02:02:0B','Terraform State'),
('10.0.20.50',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='PT-VDI-001'),'vdi-farm.pro','ESTATICA','ASIGNADA','AA:BB:CC:03:01:01','VDI Citrix Farm'),
('10.0.20.60',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),(SELECT id_activo FROM cmdb_activos WHERE codigo='K8S-PRO-001'),'k8s-master-01.pro','ESTATICA','ASIGNADA','AA:BB:CC:04:01:01','K8s Master 1'),
('10.0.20.61',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),NULL,'k8s-master-02.pro','ESTATICA','ASIGNADA','AA:BB:CC:04:01:02','K8s Master 2'),
('10.0.20.62',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=20),NULL,'k8s-master-03.pro','ESTATICA','ASIGNADA','AA:BB:CC:04:01:03','K8s Master 3')
ON CONFLICT (direccion_ip) DO NOTHING;

-- ═══ VLAN 30: BBDD-PRO (10.0.30.0/24) ═══
INSERT INTO cmdb_ips (direccion_ip,id_vlan,id_activo,hostname,tipo,estado,mac_address,notas) VALUES
('10.0.30.10',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-001'),'ora-rac-01.db','ESTATICA','ASIGNADA','DD:BB:01:01:01:01','Oracle RAC Nodo 1'),
('10.0.30.11',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-001'),'ora-rac-02.db','ESTATICA','ASIGNADA','DD:BB:01:01:01:02','Oracle RAC Nodo 2'),
('10.0.30.12',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-001'),'ora-rac-vip.db','VIP','ASIGNADA',NULL,'Oracle RAC VIP'),
('10.0.30.13',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-001'),'ora-rac-scan.db','VIP','ASIGNADA',NULL,'Oracle SCAN Listener'),
('10.0.30.20',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-002'),'pg-master.db','ESTATICA','ASIGNADA','DD:BB:02:01:01:01','PostgreSQL Master'),
('10.0.30.21',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-002'),'pg-replica.db','ESTATICA','ASIGNADA','DD:BB:02:01:01:02','PostgreSQL Replica'),
('10.0.30.30',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-003'),'mongo-01.db','ESTATICA','ASIGNADA','DD:BB:03:01:01:01','MongoDB Shard 1'),
('10.0.30.31',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-003'),'mongo-02.db','ESTATICA','ASIGNADA','DD:BB:03:01:01:02','MongoDB Shard 2'),
('10.0.30.32',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-003'),'mongo-03.db','ESTATICA','ASIGNADA','DD:BB:03:01:01:03','MongoDB Shard 3'),
('10.0.30.40',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-004'),'redis-01.db','ESTATICA','ASIGNADA','DD:BB:04:01:01:01','Redis Cluster Node 1'),
('10.0.30.41',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-004'),'redis-02.db','ESTATICA','ASIGNADA','DD:BB:04:01:01:02','Redis Cluster Node 2'),
('10.0.30.42',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-004'),'redis-03.db','ESTATICA','ASIGNADA','DD:BB:04:01:01:03','Redis Cluster Node 3'),
('10.0.30.50',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-005'),'elastic-01.db','ESTATICA','ASIGNADA','DD:BB:05:01:01:01','Elasticsearch Node 1'),
('10.0.30.51',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-005'),'elastic-02.db','ESTATICA','ASIGNADA','DD:BB:05:01:01:02','Elasticsearch Node 2'),
('10.0.30.60',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-006'),'mysql-rrhh.db','ESTATICA','ASIGNADA','DD:BB:06:01:01:01','MySQL RRHH'),
('10.0.30.61',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-007'),'pg-pmo.db','ESTATICA','ASIGNADA','DD:BB:07:01:01:01','PostgreSQL PMO'),
('10.0.30.62',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-008'),'mssql-conta.db','ESTATICA','ASIGNADA','DD:BB:08:01:01:01','SQL Server Contabilidad'),
('10.0.30.63',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=30),(SELECT id_activo FROM cmdb_activos WHERE codigo='DB-PRO-010'),'mariadb-cms.db','ESTATICA','ASIGNADA','DD:BB:10:01:01:01','MariaDB CMS')
ON CONFLICT (direccion_ip) DO NOTHING;

-- ═══ VLAN 40: DMZ-PUBLICA (172.16.40.0/24) ═══
INSERT INTO cmdb_ips (direccion_ip,id_vlan,id_activo,hostname,tipo,estado,mac_address,notas) VALUES
('172.16.40.10',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=40),(SELECT id_activo FROM cmdb_activos WHERE codigo='APP-PRO-002'),'banca-online.dmz','VIP','ASIGNADA',NULL,'VIP Banca Online Web'),
('172.16.40.11',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=40),(SELECT id_activo FROM cmdb_activos WHERE codigo='APP-PRO-003'),'app-mobile.dmz','VIP','ASIGNADA',NULL,'VIP App Móvil API'),
('172.16.40.12',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=40),(SELECT id_activo FROM cmdb_activos WHERE codigo='APP-PRO-004'),'api-gw.dmz','VIP','ASIGNADA',NULL,'VIP API Gateway'),
('172.16.40.13',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=40),(SELECT id_activo FROM cmdb_activos WHERE codigo='APP-PRO-021'),'openbanking.dmz','VIP','ASIGNADA',NULL,'VIP Open Banking PSD2'),
('172.16.40.14',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=40),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-PRX-001'),'haproxy.dmz','ESTATICA','ASIGNADA','EE:FF:01:01:01:01','HAProxy Reverse Proxy'),
('172.16.40.20',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=40),NULL,'spare-dmz-20','ESTATICA','LIBRE',NULL,'Reserva DMZ'),
('172.16.40.21',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=40),NULL,'spare-dmz-21','ESTATICA','LIBRE',NULL,'Reserva DMZ')
ON CONFLICT (direccion_ip) DO NOTHING;

-- ═══ VLAN 90: SWIFT-CORE (10.0.90.0/28) ═══
INSERT INTO cmdb_ips (direccion_ip,id_vlan,id_activo,hostname,tipo,estado,mac_address,notas) VALUES
('10.0.90.2',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=90),(SELECT id_activo FROM cmdb_activos WHERE codigo='SRV-PRO-003'),'swift-gw.swift','ESTATICA','ASIGNADA','FF:AA:01:01:01:01','SWIFT Alliance Gateway'),
('10.0.90.3',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=90),(SELECT id_activo FROM cmdb_activos WHERE codigo='APP-PRO-007'),'swift-app.swift','ESTATICA','ASIGNADA','FF:AA:01:01:01:02','SWIFT Alliance App'),
('10.0.90.4',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=90),NULL,'swift-hsm.swift','ESTATICA','ASIGNADA','FF:AA:01:01:01:03','SWIFT HSM Módulo'),
('10.0.90.5',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=90),NULL,'swift-spare.swift','ESTATICA','LIBRE',NULL,'Reserva SWIFT')
ON CONFLICT (direccion_ip) DO NOTHING;

-- ═══ VLAN 110: BACKUP-NET (10.0.110.0/24) ═══
INSERT INTO cmdb_ips (direccion_ip,id_vlan,id_activo,hostname,tipo,estado,mac_address,notas) VALUES
('10.0.110.10',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=110),(SELECT id_activo FROM cmdb_activos WHERE codigo='STO-PRO-001'),'san-netapp.bak','ESTATICA','ASIGNADA','BB:AA:01:01:01:01','SAN NetApp iSCSI'),
('10.0.110.11',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=110),(SELECT id_activo FROM cmdb_activos WHERE codigo='STO-PRO-001'),'san-netapp-mgmt.bak','ESTATICA','ASIGNADA','BB:AA:01:01:01:02','SAN NetApp Management'),
('10.0.110.20',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=110),(SELECT id_activo FROM cmdb_activos WHERE codigo='STO-PRO-002'),'veeam-proxy.bak','ESTATICA','ASIGNADA','BB:AA:02:01:01:01','Veeam Backup Proxy'),
('10.0.110.21',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=110),(SELECT id_activo FROM cmdb_activos WHERE codigo='STO-PRO-002'),'veeam-repo.bak','ESTATICA','ASIGNADA','BB:AA:02:01:01:02','Veeam Repository'),
('10.0.110.30',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=110),(SELECT id_activo FROM cmdb_activos WHERE codigo='BAK-001'),'commvault.bak','ESTATICA','ASIGNADA','BB:AA:03:01:01:01','Commvault Server')
ON CONFLICT (direccion_ip) DO NOTHING;

-- ═══ VLAN 120: MONITORING (10.0.120.0/24) ═══
INSERT INTO cmdb_ips (direccion_ip,id_vlan,id_activo,hostname,tipo,estado,mac_address,notas) VALUES
('10.0.120.10',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=120),(SELECT id_activo FROM cmdb_activos WHERE codigo='MON-PRO-002'),'zabbix.mon','ESTATICA','ASIGNADA','CC:DD:01:01:01:01','Zabbix Server'),
('10.0.120.11',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=120),(SELECT id_activo FROM cmdb_activos WHERE codigo='SEC-SIEM-001'),'splunk-idx-01.mon','ESTATICA','ASIGNADA','CC:DD:02:01:01:01','Splunk Indexer 1'),
('10.0.120.12',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=120),(SELECT id_activo FROM cmdb_activos WHERE codigo='SEC-SIEM-001'),'splunk-idx-02.mon','ESTATICA','ASIGNADA','CC:DD:02:01:01:02','Splunk Indexer 2'),
('10.0.120.13',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=120),(SELECT id_activo FROM cmdb_activos WHERE codigo='SEC-SIEM-001'),'splunk-sh.mon','ESTATICA','ASIGNADA','CC:DD:02:01:01:03','Splunk Search Head'),
('10.0.120.20',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=120),(SELECT id_activo FROM cmdb_activos WHERE codigo='SEC-NAC-001'),'ise-01.mon','ESTATICA','ASIGNADA','CC:DD:03:01:01:01','Cisco ISE Primary'),
('10.0.120.21',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=120),(SELECT id_activo FROM cmdb_activos WHERE codigo='SEC-NAC-001'),'ise-02.mon','ESTATICA','ASIGNADA','CC:DD:03:01:01:02','Cisco ISE Secondary'),
('10.0.120.30',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=120),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-DNS-001'),'dns-pri.mon','ESTATICA','ASIGNADA','CC:DD:04:01:01:01','DNS Primario'),
('10.0.120.40',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=120),(SELECT id_activo FROM cmdb_activos WHERE codigo='SEC-PAM-001'),'cyberark.mon','ESTATICA','ASIGNADA','CC:DD:05:01:01:01','CyberArk Vault'),
('10.0.120.41',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=120),(SELECT id_activo FROM cmdb_activos WHERE codigo='SEC-HSM-001'),'hsm.mon','ESTATICA','ASIGNADA','CC:DD:06:01:01:01','HSM Thales Luna')
ON CONFLICT (direccion_ip) DO NOTHING;

-- ═══ VLAN 200/201: DR Barcelona ═══
INSERT INTO cmdb_ips (direccion_ip,id_vlan,id_activo,hostname,tipo,estado,mac_address,notas) VALUES
('10.10.20.10',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=200),(SELECT id_activo FROM cmdb_activos WHERE codigo='DR-SRV-001'),'dr-core-01.bcn','ESTATICA','ASIGNADA','FF:01:01:01:01:01','DR Core Banking'),
('10.10.20.11',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=200),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-SW-010'),'dr-sw-core.bcn','ESTATICA','ASIGNADA','FF:01:02:01:01:01','DR Switch Core BCN'),
('10.10.20.12',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=200),(SELECT id_activo FROM cmdb_activos WHERE codigo='BAK-002'),'dr-zerto.bcn','ESTATICA','ASIGNADA','FF:01:03:01:01:01','DR Zerto Replication'),
('10.10.30.10',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=201),(SELECT id_activo FROM cmdb_activos WHERE codigo='DR-DB-001'),'dr-ora-01.bcn','ESTATICA','ASIGNADA','FF:02:01:01:01:01','DR Oracle Data Guard'),
('10.10.30.11',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=201),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-DNS-002'),'dns-sec.bcn','ESTATICA','ASIGNADA','FF:02:02:01:01:01','DNS Secundario BCN')
ON CONFLICT (direccion_ip) DO NOTHING;

-- ═══ VLAN 70: VOIP (10.0.70.0/24) - IPs de ejemplo ═══
INSERT INTO cmdb_ips (direccion_ip,id_vlan,id_activo,hostname,tipo,estado,notas) VALUES
('10.0.70.10',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=70),(SELECT id_activo FROM cmdb_activos WHERE codigo='TEL-003'),'cucm.voip','ESTATICA','ASIGNADA','Cisco UCM Contact Center'),
('10.0.70.11',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=70),(SELECT id_activo FROM cmdb_activos WHERE codigo='TEL-001'),'cucm-pub.voip','ESTATICA','ASIGNADA','CUCM Publisher Sede'),
('10.0.70.100',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=70),NULL,'phone-p1-001.voip','DHCP','ASIGNADA','Teléfono Planta 1'),
('10.0.70.101',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=70),NULL,'phone-p1-002.voip','DHCP','ASIGNADA','Teléfono Planta 1'),
('10.0.70.102',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=70),NULL,'phone-p1-003.voip','DHCP','ASIGNADA','Teléfono Planta 1')
ON CONFLICT (direccion_ip) DO NOTHING;

-- ═══ VLAN 80: ATM (10.0.80.0/24) ═══
INSERT INTO cmdb_ips (direccion_ip,id_vlan,id_activo,hostname,tipo,estado,notas) VALUES
('10.0.80.10',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=80),(SELECT id_activo FROM cmdb_activos WHERE codigo='ATM-NET-001'),'atm-ctrl-norte.atm','ESTATICA','ASIGNADA','Controller ATM Zona Norte'),
('10.0.80.11',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=80),(SELECT id_activo FROM cmdb_activos WHERE codigo='ATM-NET-002'),'atm-ctrl-sur.atm','ESTATICA','ASIGNADA','Controller ATM Zona Sur'),
('10.0.80.12',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=80),(SELECT id_activo FROM cmdb_activos WHERE codigo='ATM-NET-003'),'atm-ctrl-este.atm','ESTATICA','ASIGNADA','Controller ATM Zona Este'),
('10.0.80.13',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=80),(SELECT id_activo FROM cmdb_activos WHERE codigo='ATM-NET-004'),'atm-ctrl-oeste.atm','ESTATICA','ASIGNADA','Controller ATM Zona Oeste'),
('10.0.80.14',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=80),(SELECT id_activo FROM cmdb_activos WHERE codigo='ATM-NET-005'),'atm-ctrl-cc.atm','ESTATICA','ASIGNADA','Controller ATM CC'),
('10.0.80.20',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=80),(SELECT id_activo FROM cmdb_activos WHERE codigo='TPV-001'),'tpv-gateway.atm','ESTATICA','ASIGNADA','Gateway Red TPVs')
ON CONFLICT (direccion_ip) DO NOTHING;

-- ═══ VLAN 50: USUARIOS SEDE (10.0.50.0/23) - muestra ═══
INSERT INTO cmdb_ips (direccion_ip,id_vlan,id_activo,hostname,tipo,estado,notas) VALUES
('10.0.50.10',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=50),(SELECT id_activo FROM cmdb_activos WHERE codigo='IMP-001'),'imp-p1-color.user','ESTATICA','ASIGNADA','Impresora Color P1'),
('10.0.50.11',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=50),(SELECT id_activo FROM cmdb_activos WHERE codigo='IMP-001'),'imp-p2-color.user','ESTATICA','ASIGNADA','Impresora Color P2'),
('10.0.50.12',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=50),(SELECT id_activo FROM cmdb_activos WHERE codigo='IMP-001'),'imp-p3-color.user','ESTATICA','ASIGNADA','Impresora Color P3'),
('10.0.50.100',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=50),NULL,'pc-user-001.user','DHCP','ASIGNADA','Puesto usuario sede'),
('10.0.50.101',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=50),NULL,'pc-user-002.user','DHCP','ASIGNADA','Puesto usuario sede'),
('10.0.50.102',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=50),NULL,'pc-user-003.user','DHCP','ASIGNADA','Puesto usuario sede'),
('10.0.50.103',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=50),NULL,'pc-user-004.user','DHCP','ASIGNADA','Puesto usuario sede'),
('10.0.50.104',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=50),NULL,'pc-user-005.user','DHCP','ASIGNADA','Puesto usuario sede')
ON CONFLICT (direccion_ip) DO NOTHING;

-- ═══ VLAN 60: WIFI (10.0.60.0/24) ═══
INSERT INTO cmdb_ips (direccion_ip,id_vlan,id_activo,hostname,tipo,estado,notas) VALUES
('10.0.60.10',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=60),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-AP-001'),'ap-p1.wifi','ESTATICA','ASIGNADA','AP Planta 1'),
('10.0.60.11',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=60),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-AP-002'),'ap-p2.wifi','ESTATICA','ASIGNADA','AP Planta 2'),
('10.0.60.12',(SELECT id_vlan FROM cmdb_vlans WHERE vlan_id=60),(SELECT id_activo FROM cmdb_activos WHERE codigo='NET-AP-003'),'ap-p3.wifi','ESTATICA','ASIGNADA','AP Planta 3')
ON CONFLICT (direccion_ip) DO NOTHING;

-- ============================================================
-- VINCULAR ACTIVOS A PROYECTOS (coherente con cartera_build)
-- ============================================================
UPDATE cmdb_activos SET id_proyecto='PRJ0001 - [9470-2023]' WHERE codigo IN ('SRV-PRO-005','SRV-PRO-006','SEC-PAM-001','VM-PRO-012','SEC-NAC-001');
UPDATE cmdb_activos SET id_proyecto='PRJ0002 - [9470-2023]' WHERE codigo IN ('SEC-SIEM-001','SEC-SOAR-001','SEC-IDS-001');
UPDATE cmdb_activos SET id_proyecto='PRJ0003 - [9470-2023]' WHERE codigo IN ('VM-PRO-012','SEC-HSM-001','SEC-PKI-001');
UPDATE cmdb_activos SET id_proyecto='PRJ0004 - [9470-2023]' WHERE codigo IN ('SEC-PAM-001');
UPDATE cmdb_activos SET id_proyecto='PRJ0005 - [PRE2022]' WHERE codigo IN ('SEC-NAC-001','NET-SW-003','NET-SW-004','NET-SW-005');
UPDATE cmdb_activos SET id_proyecto='PRJ0006 - [PRE2022]' WHERE codigo IN ('DB-PRO-001','SRV-PRO-001','SRV-PRO-002');
UPDATE cmdb_activos SET id_proyecto='PRJ0009 - [PRE2022]' WHERE codigo IN ('NET-SW-001','NET-SW-002','NET-RT-001','NET-RT-002','NET-SW-006','NET-SW-007');
UPDATE cmdb_activos SET id_proyecto='PRJ0010 - [PRE2023]' WHERE codigo IN ('SRV-PRO-003','APP-PRO-007');
UPDATE cmdb_activos SET id_proyecto='PRJ0011 - [PRE2023]' WHERE codigo IN ('VM-PRO-001','VM-PRO-004','VM-PRO-005','VM-PRO-006');
UPDATE cmdb_activos SET id_proyecto='PRJ0012 - [PRE2023]' WHERE codigo IN ('APP-PRO-023');
UPDATE cmdb_activos SET id_proyecto='PRJ0016 - -' WHERE codigo IN ('STO-PRO-002','BAK-001');
UPDATE cmdb_activos SET id_proyecto='PRJ0017 - -' WHERE codigo IN ('APP-PRO-006','APP-PRO-020','APP-PRO-025','DB-PRO-003');
UPDATE cmdb_activos SET id_proyecto='PRJ0020 - -' WHERE codigo IN ('K8S-PRO-001','K8S-PRE-001');
