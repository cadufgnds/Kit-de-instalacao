<?php
// GET — estado da ferramenta e conferência dos requisitos do servidor.
declare(strict_types=1);
if (!function_exists('mb_strlen') || PHP_VERSION_ID < 70400) {
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode([
        'ok' => false,
        'codigo' => 'requisito_ausente',
        'mensagem' => 'O servidor precisa de PHP 7.4 ou superior com a extensão mbstring. Versão atual: ' . PHP_VERSION
            . (function_exists('mb_strlen') ? '.' : '; mbstring ausente.'),
        'erros' => [],
    ]);
    exit;
}
require __DIR__ . '/../nucleo/api.php';
FormataApi\iniciar_rota('GET');
FormataApi\responder(['status' => 'ok', 'versao' => FormataApi\VERSAO_APP, 'versao_diretrizes' => Formata\VERSAO_DIRETRIZES]);
