<?php
// CLI adapter owned by the central server; the PHP generator is read-only.
ini_set('display_errors', '0');
error_reporting(E_ERROR | E_PARSE);
$input = json_decode(stream_get_contents(STDIN), true, 32, JSON_THROW_ON_ERROR);
$root = realpath(__DIR__ . '/../php/sistema-generador');
chdir($root);
$_SERVER['REQUEST_METHOD'] = 'POST';
$_POST = $input['parameters'];
$_POST['tipo'] = $input['procedure'];
$_POST['aceptar'] = true;
$_POST['lineas'] = $_POST['lineas'] ?? 2;
// Checkbox semantics in the original generator depend on presence.
foreach ($_POST as $key => $value) {
    if ($value === false) unset($_POST[$key]);
}
if ($_POST['tipo'] === 'PCC-DYNAMIC' && !empty($_POST['dhcp'])) $_POST['dhcpdinamico'] = true;
session_start(['save_path' => $input['session_directory'], 'use_cookies' => false]);
$_SESSION = ['codigo' => 'central-local'];
ob_start();
try {
    if ($input['procedure'] === 'OpenVPN') {
        include $root . '/openvpn.php';
        $source = $mikrotik_cmds;
        $attachment = $ovpn_template;
    } else {
        include $root . '/aplicar.php';
        $source = $input['procedure'] === 'PCC-DYNAMIC' ? $script_pcc_dynamic :
                  ($input['procedure'] === 'Firewall' ? $script_firewall : $script_ecmp);
        $attachment = '';
    }
    ob_end_clean();
    session_destroy();
    // Only presentation line breaks are decoded; commands remain PHP-owned.
    $source = preg_replace('/<br\s*\/?\s*>/i', "\n", $source);
    echo json_encode(['script' => $source, 'attachment' => $attachment], JSON_THROW_ON_ERROR);
} catch (Throwable $e) {
    ob_end_clean();
    session_destroy();
    fwrite(STDERR, 'El generador PHP no pudo completar esta configuración.');
    exit(1);
}
