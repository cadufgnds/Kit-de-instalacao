<?php
require dirname(__FILE__) . '/../nucleo/requisitos.php';
require dirname(__FILE__) . '/../nucleo/api.php';
FormataApi\iniciar_rota('GET');
$c = FormataApi\config();
FormataApi\responder(array(
    'limite_bytes' => (int) $c['limite_bytes'],
    'limite_linhas' => (int) $c['limite_linhas'],
    'tempo_limite_segundos' => (float) $c['tempo_limite'],
    'extensoes_aceitas' => FormataApi\EXTENSOES_ACEITAS,
    'modos' => array('auto', 'markdown', 'html'),
    'versao_diretrizes' => Formata\VERSAO_DIRETRIZES,
));
