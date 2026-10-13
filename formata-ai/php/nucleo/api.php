<?php
/**
 * Funções comuns da página e das rotas da API (versão PHP para o hub).
 *
 * Mesmo contrato da API de referência (docs/API.md): respostas JSON com
 * ok, codigo, mensagem e erros; nenhum documento é gravado em disco ou em log.
 */

declare(strict_types=1);

namespace FormataApi;

require_once __DIR__ . '/formata.php';

const VERSAO_APP = '0.3.0';
const EXTENSOES_ACEITAS = ['.md', '.markdown', '.txt', '.html', '.htm'];
const STATUS_POR_CODIGO = [
    'ok' => 200,
    'documento_vazio' => 400,
    'entrada_invalida' => 400,
    'requisicao_invalida' => 400,
    'modo_invalido' => 400,
    'metodo_nao_permitido' => 405,
    'tamanho_desconhecido' => 411,
    'documento_muito_extenso' => 413,
    'tipo_nao_suportado' => 415,
    'falha_validacao' => 422,
    'erro_interno' => 500,
    'tempo_esgotado' => 504,
];
const CSP = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    . "img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; "
    . "base-uri 'none'; form-action 'self'; frame-ancestors 'none'";

function config(): array
{
    static $config = null;
    if ($config === null) {
        $padrao = [
            'limite_bytes' => 1048576,
            'limite_linhas' => 20000,
            'tempo_limite' => 15,
            'arquivo_autenticacao' => '',
            'registrar_log' => true,
        ];
        $arquivo = dirname(__DIR__) . '/config.php';
        $local = is_file($arquivo) ? require $arquivo : [];
        $config = array_merge($padrao, is_array($local) ? $local : []);
    }
    return $config;
}

function cabecalhos_seguranca(): void
{
    header('X-Content-Type-Options: nosniff');
    header('Referrer-Policy: no-referrer');
    header('X-Frame-Options: DENY');
    header('Permissions-Policy: camera=(), microphone=(), geolocation=()');
    header('Content-Security-Policy: ' . CSP);
}

/**
 * Exige o login do hub quando config.php indica o arquivo de autenticação
 * que as outras ferramentas usam (o próprio arquivo decide redirecionar ou negar).
 */
function exigir_autenticacao(): void
{
    $arquivo = trim((string) config()['arquivo_autenticacao']);
    if ($arquivo === '') {
        return;
    }
    $caminho = $arquivo[0] === '/' ? $arquivo : dirname(__DIR__) . '/' . $arquivo;
    if (!is_file($caminho)) {
        erro('erro_interno', 'Configuração inválida: o arquivo de autenticação do hub não foi encontrado.');
    }
    require_once $caminho;
}

function responder(array $dados, int $status = 200): void
{
    if (!headers_sent()) {
        http_response_code($status);
        header('Content-Type: application/json; charset=utf-8');
        header('Cache-Control: no-store');
        cabecalhos_seguranca();
    }
    echo json_encode($dados, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function erro(string $codigo, string $mensagem, array $erros = []): void
{
    responder(['ok' => false, 'codigo' => $codigo, 'mensagem' => $mensagem, 'erros' => $erros],
        STATUS_POR_CODIGO[$codigo] ?? 400);
}

function mensagem_limite(): string
{
    return 'O documento passa do limite de ' . intdiv((int) config()['limite_bytes'], 1024) . ' KB.';
}

/** Início comum das rotas: cabeçalhos, autenticação, método e tamanho do corpo. */
function iniciar_rota(string $metodo): void
{
    exigir_autenticacao();
    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== $metodo) {
        header('Allow: ' . $metodo);
        erro('metodo_nao_permitido', "Use o método $metodo.");
    }
    if ($metodo === 'POST') {
        $tamanho = $_SERVER['CONTENT_LENGTH'] ?? $_SERVER['HTTP_CONTENT_LENGTH'] ?? null;
        if ($tamanho === null || $tamanho === '') {
            erro('tamanho_desconhecido', 'Envie o cabeçalho Content-Length.');
        }
        if (!ctype_digit((string) $tamanho) || (int) $tamanho > 2 * (int) config()['limite_bytes'] + 65536) {
            erro('documento_muito_extenso', mensagem_limite());
        }
    }
}

function vigiar_tempo_e_memoria(string $id, string $origem, int $bytes, float $inicio): void
{
    $limite = (int) config()['tempo_limite'];
    if ($limite > 0) {
        set_time_limit($limite);
    }
    register_shutdown_function(function () use ($id, $origem, $bytes, $inicio, $limite) {
        $e = error_get_last();
        if ($e === null || !in_array($e['type'], [E_ERROR, E_CORE_ERROR, E_COMPILE_ERROR], true)) {
            return;
        }
        $tempo = strpos($e['message'], 'Maximum execution time') !== false;
        registrar($id, $origem, $bytes, $tempo ? 'tempo_esgotado' : 'erro_interno', $inicio);
        if (headers_sent()) {
            return;
        }
        while (ob_get_level()) {
            ob_end_clean();
        }
        $codigo = $tempo ? 'tempo_esgotado' : 'erro_interno';
        $mensagem = $tempo
            ? "O processamento passou de {$limite} s e foi interrompido. Tente novamente."
            : 'Falha técnica no processamento. Tente novamente.';
        http_response_code(STATUS_POR_CODIGO[$codigo]);
        header('Content-Type: application/json; charset=utf-8');
        header('Cache-Control: no-store');
        echo json_encode(['ok' => false, 'codigo' => $codigo, 'mensagem' => $mensagem, 'erros' => []], JSON_UNESCAPED_UNICODE);
    });
}

/** Formata e responde. Nunca grava o conteúdo; o log técnico só tem tamanho, código e duração. */
function processar(string $texto, string $modo, string $origem): void
{
    if (!in_array($modo, ['auto', 'markdown', 'html'], true)) {
        erro('modo_invalido', 'Modo deve ser auto, markdown ou html.');
    }
    if (!mb_check_encoding($texto, 'UTF-8')) {
        erro('entrada_invalida', 'O texto não está em UTF-8. Salve-o como UTF-8 e envie de novo; nenhum caractere foi convertido.');
    }
    $bytes = strlen($texto);
    if ($bytes > (int) config()['limite_bytes']) {
        erro('documento_muito_extenso', mensagem_limite());
    }
    $id = bin2hex(random_bytes(6));
    $inicio = microtime(true);
    vigiar_tempo_e_memoria($id, $origem, $bytes, $inicio);
    @ini_set('pcre.backtrack_limit', '10000000');

    try {
        $resultado = \Formata\formatar($texto, $modo, (int) config()['limite_bytes'], (int) config()['limite_linhas']);
    } catch (\Throwable $e) {
        registrar($id, $origem, $bytes, 'erro_interno', $inicio, null, get_class($e));
        erro('erro_interno', 'Falha técnica no processamento. Tente novamente.');
        return;
    }
    registrar($id, $origem, $bytes, $resultado['codigo'], $inicio, $resultado);
    responder($resultado, STATUS_POR_CODIGO[$resultado['codigo']] ?? 400);
}

function registrar(string $id, string $origem, int $bytes, string $codigo, float $inicio, ?array $resultado = null, string $falha = ''): void
{
    if (!config()['registrar_log']) {
        return;
    }
    $extra = '';
    if ($resultado && !empty($resultado['itens'])) {
        $extra = ' blocos=' . count($resultado['itens']) . ' paginas=' . $resultado['total_paginas_texto'];
    }
    if ($falha !== '') {
        $extra .= ' falha=' . $falha;
    }
    error_log(sprintf('formata.api req=%s origem=%s bytes=%d codigo=%s ms=%d%s',
        $id, $origem, $bytes, $codigo, (int) ((microtime(true) - $inicio) * 1000), $extra));
}

/** Converte valores do php.ini como "8M" em bytes. */
function bytes_ini(string $valor): int
{
    $valor = trim($valor);
    if ($valor === '') {
        return 0;
    }
    $n = (int) $valor;
    switch (strtolower(substr($valor, -1))) {
        case 'g':
            return $n * 1024 ** 3;
        case 'm':
            return $n * 1024 ** 2;
        case 'k':
            return $n * 1024;
    }
    return $n;
}

/** Mesma validação de arquivo da API de referência: extensão, Word/ZIP, tamanho, binário e UTF-8. */
function ler_arquivo_enviado(): string
{
    if (!isset($_FILES['arquivo'])) {
        $post_max = bytes_ini((string) ini_get('post_max_size'));
        if ($post_max > 0 && (int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > $post_max) {
            erro('documento_muito_extenso', mensagem_limite());
        }
        erro('requisicao_invalida', "Envie o arquivo no campo 'arquivo'.");
    }
    $arq = $_FILES['arquivo'];
    if (is_array($arq['error'])) {
        erro('requisicao_invalida', 'Envie um único arquivo.');
    }
    if ($arq['error'] === UPLOAD_ERR_INI_SIZE || $arq['error'] === UPLOAD_ERR_FORM_SIZE) {
        erro('documento_muito_extenso', mensagem_limite());
    }
    if ($arq['error'] !== UPLOAD_ERR_OK || !is_uploaded_file($arq['tmp_name'])) {
        erro('requisicao_invalida', 'O arquivo não chegou completo. Tente enviar de novo.');
    }
    $nome = (string) $arq['name'];
    $ponto = strrpos($nome, '.');
    $extensao = $ponto === false ? '' : strtolower(substr($nome, $ponto));
    $limite = (int) config()['limite_bytes'];
    $conteudo = (string) file_get_contents($arq['tmp_name'], false, null, 0, $limite + 1);
    @unlink($arq['tmp_name']); // o arquivo temporário sai logo: nada fica no servidor

    if ($extensao === '.docx' || strncmp($conteudo, "PK\x03\x04", 4) === 0) {
        erro('tipo_nao_suportado', 'Arquivos do Word ainda não são aceitos. Exporte o documento como .md ou .txt, ou cole o conteúdo.');
    }
    if (!in_array($extensao, EXTENSOES_ACEITAS, true)) {
        erro('tipo_nao_suportado', 'Formato não aceito. Envie um destes: ' . implode(', ', EXTENSOES_ACEITAS) . '.');
    }
    if (strlen($conteudo) > $limite) {
        erro('documento_muito_extenso', mensagem_limite());
    }
    if (strpos($conteudo, "\0") !== false) {
        erro('entrada_invalida', 'O arquivo parece ser binário, não texto.');
    }
    if (!mb_check_encoding($conteudo, 'UTF-8')) {
        erro('entrada_invalida', 'O arquivo não está em UTF-8. Salve-o como UTF-8 e envie de novo; nenhum caractere foi convertido.');
    }
    return $conteudo;
}

function ler_pedido_json(): array
{
    $limite = 2 * (int) config()['limite_bytes'] + 65536;
    $corpo = (string) file_get_contents('php://input', false, null, 0, $limite + 1);
    if (strlen($corpo) > $limite) {
        erro('documento_muito_extenso', mensagem_limite());
    }
    $pedido = json_decode($corpo, true);
    if (!is_array($pedido) || array_keys($pedido) === range(0, count($pedido) - 1) && $pedido !== []) {
        erro('requisicao_invalida', 'O corpo da requisição não é um JSON válido.');
    }
    $erros = [];
    if (!isset($pedido['texto']) || !is_string($pedido['texto'])) {
        $erros[] = 'Campo inválido: texto';
    }
    if (isset($pedido['modo']) && !in_array($pedido['modo'], ['auto', 'markdown', 'html'], true)) {
        $erros[] = 'Campo inválido: modo';
    }
    if ($erros) {
        erro('requisicao_invalida', 'Requisição inválida.', $erros);
    }
    return $pedido;
}
