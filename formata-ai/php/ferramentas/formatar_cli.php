<?php
/**
 * Linha de comando: php formatar_cli.php < pedido.json
 * Pedido: {"texto": "...", "modo": "auto", "limites": {"limite_caracteres": N, "limite_linhas": N}}
 * Saída: o resultado em JSON (o mesmo da API). Usado pelos testes de equivalência com o motor Python.
 */
declare(strict_types=1);

require __DIR__ . '/../nucleo/formata.php';

ini_set('pcre.backtrack_limit', '10000000');
function atender(array $pedido): array
{
    $limites = $pedido['limites'] ?? [];
    return \Formata\formatar(
        $pedido['texto'],
        $pedido['modo'] ?? 'auto',
        $limites['limite_caracteres'] ?? \Formata\R::LIMITE_CARACTERES_PADRAO,
        $limites['limite_linhas'] ?? \Formata\R::LIMITE_LINHAS_PADRAO
    );
}

$pedido = json_decode(stream_get_contents(STDIN), true, 512, JSON_THROW_ON_ERROR);
// Uma lista de pedidos devolve uma lista de resultados (modo lote, usado nos testes).
$saida = array_is_list_compat($pedido) ? array_map('atender', $pedido) : atender($pedido);
echo json_encode($saida, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);

function array_is_list_compat(array $a): bool
{
    return $a === [] || array_keys($a) === range(0, count($a) - 1);
}
