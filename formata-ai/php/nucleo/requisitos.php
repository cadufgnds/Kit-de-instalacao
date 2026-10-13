<?php
/**
 * Verificação de requisitos e erros fatais do Formata.AI.
 *
 * Escrito de propósito em sintaxe antiga (roda até em PHP 5.3): é o primeiro
 * arquivo carregado pela página e pelas rotas da API. Em vez de uma página em
 * branco com "HTTP ERROR 500", mostra o que falta no servidor ou qual erro
 * ocorreu, sem expor caminhos completos de pastas.
 */

if (!defined('FORMATA_REQUISITOS')) {
    define('FORMATA_REQUISITOS', 1);
    define('FORMATA_PHP_MINIMO', '5.6.0');

    // O PHP não imprime mais o erro cru na página (com caminhos de pastas e, depois disso,
    // sem como trocar o código HTTP). O erro continua no log do servidor, e a mensagem
    // legível sai pela função de encerramento abaixo.
    @ini_set('display_errors', '0');
    @ini_set('log_errors', '1');

    function formata_eh_api()
    {
        $script = isset($_SERVER['SCRIPT_NAME']) ? $_SERVER['SCRIPT_NAME'] : '';
        return strpos(str_replace('\\', '/', $script), '/api/') !== false;
    }

    function formata_sem_caminhos($texto)
    {
        $pastas = array(dirname(dirname(__FILE__)));
        if (!empty($_SERVER['DOCUMENT_ROOT'])) {
            $pastas[] = $_SERVER['DOCUMENT_ROOT'];
        }
        foreach ($pastas as $pasta) {
            $texto = str_replace(array($pasta, str_replace('\\', '/', $pasta)), '...', $texto);
        }
        return $texto;
    }

    function formata_falha($titulo, $detalhe)
    {
        if (formata_eh_api()) {
            if (!headers_sent()) {
                header('Content-Type: application/json; charset=utf-8', true, 500);
            }
            $dados = array('ok' => false, 'codigo' => 'erro_servidor', 'mensagem' => $titulo . ' ' . $detalhe, 'erros' => array());
            echo function_exists('json_encode') ? json_encode($dados) : '{"ok":false,"codigo":"erro_servidor"}';
            exit;
        }
        if (!headers_sent()) {
            header('Content-Type: text/html; charset=utf-8', true, 500);
        }
        $t = htmlspecialchars($titulo, ENT_QUOTES, 'UTF-8');
        $d = htmlspecialchars($detalhe, ENT_QUOTES, 'UTF-8');
        echo '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            . '<meta name="viewport" content="width=device-width, initial-scale=1"><title>Formata.AI — erro no servidor</title></head>'
            . '<body style="font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:720px;margin:48px auto;padding:0 16px;color:#1c1424">'
            . '<h1 style="color:#660099">Formata.AI</h1>'
            . '<p style="font-size:1.15rem"><strong>' . $t . '</strong></p>'
            . '<p style="background:#fdecea;border:1px solid #a4221a;border-radius:8px;padding:12px 16px;color:#a4221a">' . $d . '</p>'
            . '<p>Envie uma foto desta tela ao responsável pela ferramenta. A página '
            . '<a href="diagnostico.php">diagnostico.php</a> mostra o que o servidor tem e o que falta.</p>'
            . '</body></html>';
        exit;
    }

    $formata_falta = array();
    if (version_compare(PHP_VERSION, FORMATA_PHP_MINIMO, '<')) {
        $formata_falta[] = 'PHP ' . FORMATA_PHP_MINIMO . ' ou superior (o servidor tem ' . PHP_VERSION . ')';
    }
    if (!function_exists('mb_strlen')) {
        $formata_falta[] = 'extensão mbstring do PHP';
    }
    if (!function_exists('json_encode')) {
        $formata_falta[] = 'extensão json do PHP';
    }
    if (!@preg_match('/^.$/u', "\xC3\xA1")) {
        $formata_falta[] = 'expressões regulares com suporte a UTF-8 (PCRE)';
    }
    if ($formata_falta) {
        formata_falha('O servidor não atende aos requisitos da ferramenta.', 'Falta: ' . implode('; ', $formata_falta) . '.');
    }

    // Erro fatal em qualquer arquivo carregado depois (inclusive o login do hub): mensagem legível.
    register_shutdown_function(function () {
        if (!empty($GLOBALS['formata_vigiando'])) {
            return; // durante a formatação, a API responde com o próprio código (ex.: tempo_esgotado)
        }
        $e = error_get_last();
        $fatais = array(E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR, E_USER_ERROR, E_RECOVERABLE_ERROR);
        if ($e === null || !in_array($e['type'], $fatais, true) || headers_sent()) {
            return;
        }
        while (ob_get_level()) {
            ob_end_clean();
        }
        $onde = basename($e['file']) . ', linha ' . $e['line'];
        $mensagem = formata_sem_caminhos(substr($e['message'], 0, 400));
        formata_falha('O servidor encontrou um erro ao abrir a ferramenta.', $onde . ': ' . $mensagem);
    });
}
