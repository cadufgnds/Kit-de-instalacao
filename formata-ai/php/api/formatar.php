<?php
// POST {"texto": "...", "modo": "auto"} — formata o texto enviado em JSON.
declare(strict_types=1);
require __DIR__ . '/../nucleo/api.php';
FormataApi\iniciar_rota('POST');
$pedido = FormataApi\ler_pedido_json();
FormataApi\processar($pedido['texto'], $pedido['modo'] ?? 'auto', 'texto');
