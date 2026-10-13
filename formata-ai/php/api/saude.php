<?php
// GET — estado da ferramenta. Se faltar algum requisito, requisitos.php responde com a explicação.
require dirname(__FILE__) . '/../nucleo/requisitos.php';
require dirname(__FILE__) . '/../nucleo/api.php';
FormataApi\iniciar_rota('GET');
FormataApi\responder(array('status' => 'ok', 'versao' => FormataApi\VERSAO_APP, 'versao_diretrizes' => Formata\VERSAO_DIRETRIZES));
