<?php
declare(strict_types=1);
require __DIR__ . '/../nucleo/api.php';
FormataApi\iniciar_rota('GET');
$c = FormataApi\config();
FormataApi\responder([
    'limite_bytes' => (int) $c['limite_bytes'],
    'limite_linhas' => (int) $c['limite_linhas'],
    'tempo_limite_segundos' => (float) $c['tempo_limite'],
    'extensoes_aceitas' => FormataApi\EXTENSOES_ACEITAS,
    'modos' => ['auto', 'markdown', 'html'],
    'versao_diretrizes' => Formata\VERSAO_DIRETRIZES,
]);
