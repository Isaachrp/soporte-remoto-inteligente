<?php
require_once __DIR__ . '/ecmp-legacy.php';

function validate_ecmp(array $p): array {
    $n = $p['lineas'] ?? null;
    if (($p['tipo'] ?? '') !== 'ECMP' || !is_int($n) || $n < 2 || $n > 12 || !is_bool($p['dhcp'] ?? null)) {
        throw new InvalidArgumentException('Parametros ECMP invalidos');
    }
    $keys = ['tipo','lineas','lan','dhcp'];
    $speeds = array_merge(['256k','512k'], array_map(fn($v) => $v.'M', array_merge(range(1,10), [15,20,30,40,50,60,70,80,90,100,150,200], range(250,1000,50))));
    if (!preg_match('/^172\.16\.(0|[1-9][0-9]{0,2})\.1$/D', $p['lan'] ?? '', $m) || (int)$m[1] > 254) {
        throw new InvalidArgumentException('LAN invalida');
    }
    $networks = [];
    for ($i=1; $i<=$n; $i++) {
        array_push($keys, 'vel'.$i, 'gw'.$i, 'ip'.$i);
        if (!in_array($p['vel'.$i] ?? null, $speeds, true) ||
            !preg_match('/^192\.168\.(0|[1-9][0-9]{0,2})\.(1|254)$/D', $p['gw'.$i] ?? '', $m) || (int)$m[1] > 254 ||
            !is_int($p['ip'.$i] ?? null) || $p['ip'.$i] < 2 || $p['ip'.$i] > 253 || isset($networks[$m[1]])) {
            throw new InvalidArgumentException('WAN invalida o superpuesta');
        }
        $networks[$m[1]] = true;
    }
    if (array_diff(array_keys($p), $keys) || array_diff($keys, array_keys($p))) {
        throw new InvalidArgumentException('Campos desconocidos o faltantes');
    }
    return $p;
}

function ecmp_artifact(array $p, string $family): array {
    validate_ecmp($p);
    if ($family !== 'v6') {
        throw new InvalidArgumentException('Variante v7 pendiente de implementacion y laboratorio');
    }
    $script = str_replace(["\r\n", "\r"], "\n", ecmp_text($p));
    $script = trim(implode("\n", array_map('rtrim', explode("\n", $script)))) . "\n";
    return [
        'generation_id' => bin2hex(random_bytes(16)), 'procedure' => 'ECMP',
        'generator_version' => 'ECMP-PHP-001/1.0.0', 'routeros_family' => $family,
        'parameters' => $p, 'script' => $script, 'script_hash' => hash('sha256', $script),
        'warnings' => ['NO CERTIFICADO: solo simulacion', 'Renombra puertos; modifica DNS y opcionalmente DHCP', 'Sintaxis legacy: broadcast, routing-mark y ponderacion pendientes de laboratorio'],
        'generated_at' => gmdate('c'),
    ];
}
