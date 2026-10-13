<?php
// POST multipart/form-data: arquivo (.md, .markdown, .txt, .html, .htm em UTF-8) e modo opcional.
declare(strict_types=1);
require __DIR__ . '/../../nucleo/api.php';
FormataApi\iniciar_rota('POST');
$modo = isset($_POST['modo']) && is_string($_POST['modo']) && $_POST['modo'] !== '' ? $_POST['modo'] : 'auto';
if (!in_array($modo, ['auto', 'markdown', 'html'], true)) {
    FormataApi\erro('modo_invalido', 'Modo deve ser auto, markdown ou html.');
}
FormataApi\processar(FormataApi\ler_arquivo_enviado(), $modo, 'arquivo');
