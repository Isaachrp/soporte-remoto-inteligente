<?php
// Simple PHP form to collect OpenVPN parameters and generate MikroTik commands + .ovpn template
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $client = $_POST['client'] ?? '';
    $password = $_POST['password'] ?? '';
    $ip = $_POST['ip'] ?? '';
    $export_pass = $_POST['export_pass'] ?? '';

    $client_safe = preg_replace('/[^A-Za-z0-9_\-]/', '', $client);

    $mikrotik_cmds = <<<EOT
# === Crear certificado del cliente ===
/certificate add name={$client_safe}-template common-name={$client_safe}
/certificate sign {$client_safe}-template ca=ca name={$client_safe}

# === Exportar como .p12 ===
/certificate export-certificate {$client_safe} export-passphrase="{$export_pass}"

# === Crear usuario PPP ===
/ppp secret add name={$client_safe} password={$password} service=ovpn profile=default-encryption
EOT;

    $ovpn_template = <<<EOT
client
dev tun
proto tcp-client
remote {$ip} 1194
auth SHA1
cipher AES-256-CBC
setenv CLIENT_CERT 1
nobind
persist-key
persist-tun
verb 3

<ca>
# Pegar contenido de ca.crt aquí
</ca>

<cert>
# Pegar contenido del certificado cliente .crt aquí
</cert>

<key>
# Pegar contenido del cliente .key aquí
</key>
EOT;
}
?>
<!DOCTYPE html>
<html>
<head>
<title>Generador de Scripts OpenVPN MikroTik</title>
<style>
body { font-family: Arial, sans-serif; margin: 20px; }
textarea { width: 100%; height: 200px; }
input { padding: 6px; width: 300px; }
label { display: block; margin-top: 10px; font-weight: bold; }
button { padding: 10px 20px; margin-top: 15px; }
</style>
</head>
<body>
<h2>Generador de Script para OpenVPN MikroTik</h2>
<form method="post">
    <label>Nombre del cliente (ej: JosePC1)</label>
    <input type="text" name="client" required>

    <label>Contraseña del usuario OVPN</label>
    <input type="text" name="password" required>

    <label>IP pública del servidor</label>
    <input type="text" name="ip" required>

    <label>Passphrase para exportar .p12</label>
    <input type="text" name="export_pass" value="1234" required>

    <button type="submit">Generar</button>
</form>

<?php if (!empty($mikrotik_cmds)): ?>
<h3>Comandos MikroTik generados</h3>
<textarea readonly><?= htmlspecialchars($mikrotik_cmds) ?></textarea>

<h3>Plantilla .ovpn</h3>
<textarea readonly><?= htmlspecialchars($ovpn_template) ?></textarea>
<?php endif; ?>

</body>
</html>
