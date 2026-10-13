<?php
/**
 * Diagnóstico do Formata.AI: mostra, em linguagem simples, o que o servidor tem
 * e o que falta. Escrito em sintaxe antiga (roda até em PHP 5.3) para funcionar
 * justamente quando a ferramenta não abre.
 *
 * Para desativar depois de resolvido: em config.php, 'diagnostico_ativo' => false.
 */

$formata_raiz = dirname(__FILE__);
$formata_config = array();
if (is_file($formata_raiz . '/config.php')) {
    $formata_lido = @include $formata_raiz . '/config.php';
    if (is_array($formata_lido)) {
        $formata_config = $formata_lido;
    }
}
if (isset($formata_config['diagnostico_ativo']) && !$formata_config['diagnostico_ativo']) {
    header('HTTP/1.1 404 Not Found');
    exit;
}

header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store');

$linhas = array();

function diag_item(&$linhas, $situacao, $item, $detalhe)
{
    $linhas[] = array($situacao, $item, $detalhe);
}

function diag_bytes($valor)
{
    $valor = trim((string) $valor);
    if ($valor === '' || $valor === '-1') {
        return -1;
    }
    $n = (float) $valor;
    $u = strtolower(substr($valor, -1));
    if ($u === 'g') { $n *= 1073741824; }
    if ($u === 'm') { $n *= 1048576; }
    if ($u === 'k') { $n *= 1024; }
    return (int) $n;
}

// 1. PHP e extensões
$ok_php = version_compare(PHP_VERSION, '5.6.0', '>=');
diag_item($linhas, $ok_php ? 'ok' : 'falha', 'Versão do PHP', PHP_VERSION . ($ok_php ? '' : ' — a ferramenta precisa de 5.6 ou superior'));
$ok_mb = function_exists('mb_strlen');
diag_item($linhas, $ok_mb ? 'ok' : 'falha', 'Extensão mbstring', $ok_mb ? 'ativa' : 'ausente — peça para ativar no PHP do servidor');
$ok_json = function_exists('json_encode');
diag_item($linhas, $ok_json ? 'ok' : 'falha', 'Extensão json', $ok_json ? 'ativa' : 'ausente — peça para ativar no PHP do servidor');
$ok_pcre = (bool) @preg_match('/^.$/u', "\xC3\xA1");
diag_item($linhas, $ok_pcre ? 'ok' : 'falha', 'Expressões regulares com UTF-8', $ok_pcre ? 'funcionam' : 'sem suporte a UTF-8 no PCRE');

// 2. Limites do PHP
$limite_doc = isset($formata_config['limite_bytes']) ? (int) $formata_config['limite_bytes'] : 1048576;
$memoria = diag_bytes(ini_get('memory_limit'));
diag_item($linhas, ($memoria === -1 || $memoria >= 64 * 1048576) ? 'ok' : 'atencao', 'Memória (memory_limit)',
    ini_get('memory_limit') . (($memoria === -1 || $memoria >= 64 * 1048576) ? '' : ' — recomendado 128M'));
$post = diag_bytes(ini_get('post_max_size'));
diag_item($linhas, ($post <= 0 || $post >= 2 * $limite_doc) ? 'ok' : 'atencao', 'Tamanho máximo de envio (post_max_size)',
    ini_get('post_max_size') . (($post <= 0 || $post >= 2 * $limite_doc) ? '' : ' — documentos grandes colados no campo podem ser recusados'));
$upload = diag_bytes(ini_get('upload_max_filesize'));
$uploads_ligados = (bool) ini_get('file_uploads');
diag_item($linhas, ($uploads_ligados && ($upload <= 0 || $upload >= $limite_doc)) ? 'ok' : 'atencao', 'Envio de arquivos',
    ($uploads_ligados ? 'permitido, até ' . ini_get('upload_max_filesize') : 'desativado (file_uploads) — use a opção de colar o texto'));
$desativadas = array_map('trim', explode(',', (string) ini_get('disable_functions')));
diag_item($linhas, in_array('set_time_limit', $desativadas, true) ? 'atencao' : 'ok', 'Tempo-limite configurável',
    in_array('set_time_limit', $desativadas, true) ? 'set_time_limit desativada; vale o limite do servidor (' . ini_get('max_execution_time') . ' s)' : 'sim');

// 3. Arquivos da ferramenta
$arquivos = array('index.php', 'config.php', 'nucleo/requisitos.php', 'nucleo/api.php', 'nucleo/formata.php',
    'api/saude.php', 'api/configuracao.php', 'api/formatar.php', 'api/formatar/arquivo.php',
    'js/app.js', 'css/app.css', 'marca/marca.css');
$faltando = array();
foreach ($arquivos as $a) {
    if (!is_file($formata_raiz . '/' . $a) || !is_readable($formata_raiz . '/' . $a)) {
        $faltando[] = $a;
    }
}
diag_item($linhas, $faltando ? 'falha' : 'ok', 'Arquivos da ferramenta',
    $faltando ? 'faltando ou sem permissão de leitura: ' . implode(', ', $faltando) . ' — copie a pasta inteira de novo' : 'todos presentes');

// 4. Configuração e login do hub
$auth = isset($formata_config['arquivo_autenticacao']) ? trim((string) $formata_config['arquivo_autenticacao']) : '';
if ($auth === '') {
    diag_item($linhas, 'info', 'Login', 'não exigido (arquivo_autenticacao vazio em config.php)');
} else {
    $caminho = $auth[0] === '/' ? $auth : $formata_raiz . '/' . $auth;
    diag_item($linhas, is_file($caminho) ? 'ok' : 'falha', 'Login do hub',
        is_file($caminho) ? 'arquivo ' . $auth . ' encontrado' : 'arquivo ' . $auth . ' NÃO encontrado — confira o caminho em config.php');
}

// 5. Teste do motor (só se o básico estiver presente)
$ok_basico = $ok_php && $ok_mb && $ok_json && $ok_pcre && !in_array('nucleo/formata.php', $faltando, true);
if ($ok_basico) {
    $GLOBALS['diag_testando_motor'] = true;
    register_shutdown_function(function () {
        if (empty($GLOBALS['diag_testando_motor'])) {
            return;
        }
        $e = error_get_last();
        if ($e !== null) {
            echo '<p style="color:#a4221a"><strong>O motor parou com erro:</strong> '
                . htmlspecialchars(basename($e['file']) . ', linha ' . $e['line'] . ': ' . $e['message'], ENT_QUOTES, 'UTF-8') . '</p>';
        }
    });
    ob_start();
    require_once $formata_raiz . '/nucleo/formata.php';
    $r = Formata\formatar("# Teste\nTexto com **negrito**.\n[Imagem 1]");
    ob_end_clean();
    $GLOBALS['diag_testando_motor'] = false;
    $esperado = "<p><strong># Teste</strong></p>\n<p>Texto com <strong>**negrito**</strong>.</p>\n"
        . '<p class="quebra-pagina" style="page-break-before: always;"><strong>[INSERIR IMAGENS]</strong></p>' . "\n<p>[Imagem 1]</p>";
    diag_item($linhas, ($r['ok'] && $r['html'] === $esperado) ? 'ok' : 'falha', 'Teste de formatação',
        ($r['ok'] && $r['html'] === $esperado) ? 'documento de teste formatado corretamente' : 'resultado inesperado: ' . $r['codigo']);
} else {
    diag_item($linhas, 'falha', 'Teste de formatação', 'não executado: corrija primeiro os itens marcados como falha');
}

$servidor = isset($_SERVER['SERVER_SOFTWARE']) ? $_SERVER['SERVER_SOFTWARE'] : 'desconhecido';
$simbolos = array('ok' => array('&#10004;', '#0b6b3a', 'OK'), 'atencao' => array('!', '#7a4f00', 'Atenção'),
    'falha' => array('&#10006;', '#a4221a', 'Falha'), 'info' => array('i', '#5b5266', 'Informação'));
$falhas = 0;
foreach ($linhas as $l) {
    if ($l[0] === 'falha') { $falhas++; }
}
?><!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Formata.AI — diagnóstico do servidor</title>
<style>
body{font-family:system-ui,"Segoe UI",Arial,sans-serif;max-width:860px;margin:32px auto;padding:0 16px;color:#1c1424}
h1{color:#660099;margin-bottom:4px}
.resumo{padding:14px 18px;border-radius:10px;font-weight:700;margin:20px 0}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid #e4dcea;vertical-align:top}
th{background:#f7f4f9;font-size:.85rem;text-transform:uppercase;letter-spacing:.04em}
.s{font-weight:800;white-space:nowrap}
</style>
</head>
<body>
<h1>Formata.AI — diagnóstico do servidor</h1>
<p>Servidor: <?php echo htmlspecialchars($servidor . ' · PHP ' . PHP_VERSION . ' (' . PHP_SAPI . ')', ENT_QUOTES, 'UTF-8'); ?></p>
<?php if ($falhas): ?>
<p class="resumo" style="background:#fdecea;color:#a4221a">Há <?php echo $falhas; ?> item(ns) com falha. Envie uma foto desta página ao responsável pela ferramenta.</p>
<?php else: ?>
<p class="resumo" style="background:#e5f4ec;color:#0b6b3a">Tudo certo: a ferramenta pode funcionar neste servidor. <a href="./">Abrir o Formata.AI</a></p>
<?php endif; ?>
<table>
<thead><tr><th scope="col">Situação</th><th scope="col">Item</th><th scope="col">Detalhe</th></tr></thead>
<tbody>
<?php foreach ($linhas as $l): $s = $simbolos[$l[0]]; ?>
<tr>
<td class="s" style="color:<?php echo $s[1]; ?>"><span aria-hidden="true"><?php echo $s[0]; ?></span> <?php echo $s[2]; ?></td>
<td><?php echo htmlspecialchars($l[1], ENT_QUOTES, 'UTF-8'); ?></td>
<td><?php echo htmlspecialchars($l[2], ENT_QUOTES, 'UTF-8'); ?></td>
</tr>
<?php endforeach; ?>
</tbody>
</table>
<p style="color:#5b5266;font-size:.9rem">Depois de resolver, esta página pode ser desativada em config.php ('diagnostico_ativo' =&gt; false).</p>
</body>
</html>
