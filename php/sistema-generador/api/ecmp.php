<?php
// Structured integration, independent from the legacy login/database.
require_once __DIR__ . '/../lib/ecmp-contract.php';
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
$key = getenv('ECMP_GENERATOR_TOKEN');
if (!$key || strlen($key) < 32 || !hash_equals('Bearer '.$key, $_SERVER['HTTP_AUTHORIZATION'] ?? '')) {
    http_response_code(401); echo json_encode(['error'=>'unauthorized']); exit;
}
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405); echo json_encode(['error'=>'method']); exit;
}
try {
    $raw = file_get_contents('php://input', false, null, 0, 16385);
    if (strlen($raw) > 16384) throw new InvalidArgumentException();
    $body = json_decode($raw, true, 32, JSON_THROW_ON_ERROR);
    if (!is_array($body) || array_diff(array_keys($body), ['parameters','routeros_family'])) throw new InvalidArgumentException();
    echo json_encode(ecmp_artifact($body['parameters'], $body['routeros_family']), JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES);
} catch (Throwable $e) {
    http_response_code(422); echo json_encode(['error'=>'invalid_ecmp_parameters_or_variant']);
}
