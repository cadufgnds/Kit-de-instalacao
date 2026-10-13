<?php
// POST {"texto": "...", "modo": "auto"} — formata o texto enviado em JSON.
require dirname(__FILE__) . '/../nucleo/requisitos.php';
require dirname(__FILE__) . '/../nucleo/api.php';
FormataApi\iniciar_rota('POST');
$pedido = FormataApi\ler_pedido_json();
FormataApi\processar($pedido['texto'], isset($pedido['modo']) ? $pedido['modo'] : 'auto', 'texto');
