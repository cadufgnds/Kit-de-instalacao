<?php
// POST multipart/form-data: arquivo (.md, .markdown, .txt, .html, .htm em UTF-8) e modo opcional.
require dirname(__FILE__) . '/../../nucleo/requisitos.php';
require dirname(__FILE__) . '/../../nucleo/api.php';
FormataApi\iniciar_rota('POST');
$modo = isset($_POST['modo']) && is_string($_POST['modo']) && $_POST['modo'] !== '' ? $_POST['modo'] : 'auto';
if (!in_array($modo, array('auto', 'markdown', 'html'), true)) {
    FormataApi\erro('modo_invalido', 'Modo deve ser auto, markdown ou html.');
}
FormataApi\processar(FormataApi\ler_arquivo_enviado(), $modo, 'arquivo');
