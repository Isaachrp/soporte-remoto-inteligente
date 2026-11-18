<?php
// Offline preview plus a separate, explicit v7-lab execution contract.
require_once __DIR__ . '/ecmp-contract.php';

function ecmp_v7_lab_artifact(array $p): array {
    validate_ecmp($p);
    if ($p['lineas'] !== 2 || $p['lan'] !== '172.16.0.1' ||
        $p['gw1'] !== '192.168.1.1' || $p['gw2'] !== '192.168.2.1' ||
        $p['ip1'] !== 2 || $p['ip2'] !== 2 || $p['vel1'] !== $p['vel2']) {
        throw new InvalidArgumentException('Vista previa limitada al laboratorio de dos WAN de igual costo');
    }
    $lines = [
        '# BORRADOR: revisar antes de ejecutar; no certificado para RouterOS real.',
        '# Reutiliza direcciones existentes en ether1, ether2, ether3 y ether4.',
        '# No importar dos veces: las instrucciones add no son idempotentes.',
        '/ip firewall nat',
        'add chain=srcnat src-address=172.16.0.0/24 out-interface=ether1 action=masquerade comment="ECMP7-LAB-NAT1"',
        'add chain=srcnat src-address=172.16.0.0/24 out-interface=ether2 action=masquerade comment="ECMP7-LAB-NAT2"',
        '/ip route',
        'add dst-address=0.0.0.0/0 gateway=192.168.1.1 routing-table=main distance=1 check-gateway=ping comment="ECMP7-LAB-WAN1"',
        'add dst-address=0.0.0.0/0 gateway=192.168.2.1 routing-table=main distance=1 check-gateway=ping comment="ECMP7-LAB-WAN2"',
    ];
    if ($p['dhcp']) {
        array_push($lines,
            '/ip pool',
            'add name=ecmp7_lab_pool ranges=172.16.0.50-172.16.0.250',
            '/ip dhcp-server network',
            'add address=172.16.0.0/24 gateway=172.16.0.1 dns-server=1.1.1.1,8.8.8.8 comment="ECMP7-LAB-DHCP"',
            '/ip dhcp-server',
            'add name=ecmp7_lab_dhcp interface=ether3 address-pool=ecmp7_lab_pool lease-time=8h disabled=yes'
        );
    }
    $script = implode("\n", $lines) . "\n";
    return [
        'schema' => 'ecmp-v7-lab-preview/1',
        'generator_version' => 'ECMP-PHP-V7-LAB/0.1.0',
        'procedure' => 'ECMP', 'routeros_family' => 'v7',
        'target_version' => '7.24.5 (stable)', 'target_identity' => 'lab-router',
        'preview_only' => true, 'certified' => false, 'agent_execution_supported' => false,
        'preflight_performed' => false, 'parameters' => $p,
        'load_distribution' => 'equal_cost', 'speed_values_used_for_weighting' => false,
        'required_addresses' => [
            'ether1' => '192.168.1.2/24', 'ether2' => '192.168.2.2/24',
            'ether3' => '172.16.0.1/24', 'ether4' => '10.255.255.1/24',
        ],
        'required_state' => [
            'Solo cuatro rutas conectadas esperadas en main; sin rutas estaticas ni reglas de policy routing.',
            'Sin NAT, mangle, pools, redes ni servidores DHCP existentes.',
            'Puertos de trabajo fuera de bridges; firewall y clientes DHCP revisados antes del ensayo.',
            'Snapshots conservados y administracion ether4 accesible.',
        ],
        'warnings' => [
            'Vista previa offline: no inspecciona ni conecta con un router.',
            'No habilita escrituras ni altera el endpoint v6 existente.',
            'Dos rutas de igual costo; no ponderacion por velocidades ni PCC.',
            'check-gateway solo comprueba el gateway del ISP, no Internet aguas arriba.',
            'Solo trafico saliente del cliente; respuestas a conexiones entrantes por WAN no cubiertas.',
            'DHCP se prepara deshabilitado; requiere una etapa posterior de habilitacion y prueba.',
            'No cambia interfaces, direcciones, certificados, usuarios ni DNS del router.',
            'No instala firewall de produccion; laboratorio aislado exclusivamente.',
        ],
        'script' => $script, 'script_hash' => hash('sha256', $script),
    ];
}

function ecmp_v7_lab_execution_artifact(array $p): array {
    $preview = ecmp_v7_lab_artifact($p);
    $script = str_replace('disabled=yes', 'disabled=no', $preview['script']);
    $script = str_replace('# BORRADOR: revisar antes de ejecutar; no certificado para RouterOS real.',
        '# ENSAYO DE LABORATORIO: requiere prechequeo y aprobacion; no certificado.', $script);
    return [
        'schema' => 'ecmp-v7-lab-execution/1', 'generation_id' => bin2hex(random_bytes(16)),
        'procedure' => 'ECMP', 'generator_version' => 'ECMP-PHP-V7-LAB/0.2.0',
        'routeros_family' => 'v7', 'target_version' => '7.24.5 (stable)', 'target_identity' => 'lab-router',
        'lab_only' => true, 'preview_only' => false, 'certified' => false,
        'agent_execution_supported' => true, 'parameters' => $p,
        'script' => $script, 'script_hash' => hash('sha256', $script),
        'warnings' => [
            'ENSAYO CONTROLADO: no certificacion ni uso productivo.',
            'Conserva cuatro direcciones e interfaces existentes; exige base sin NAT/rutas estaticas/DHCP.',
            'ECMP de igual costo; velocidades iguales no representan ponderacion ni medicion.',
            $p['dhcp'] ? 'DHCP se habilita al final de la aplicacion aprobada.' : 'DHCP omitido.',
            'Verificacion estructural; trafico WAN/LAN, DNS y failover requieren ensayo externo.',
            'Una aplicacion parcial requiere intervencion; no hay rollback automatico ni reintento de escritura.',
        ],
        'generated_at' => gmdate('c'),
    ];
}
