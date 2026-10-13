<?php
/**
 * Formata.AI — motor determinístico de paginação e marcação HTML (Diretrizes v2.6).
 *
 * Tradução fiel do motor de referência em Python (backend/formata). As duas
 * implementações são comparadas automaticamente pelos testes
 * (backend/tests/test_php.py): para a mesma entrada, o resultado tem de ser
 * idêntico, caractere por caractere.
 *
 * Compatível com PHP 5.6 ou superior, com as extensões mbstring e pcre (sintaxe
 * mantida no subconjunto do 5.6: sem tipos escalares, sem ?? e sem <=>).
 * Posições internas são em bytes (UTF-8); contagens de caracteres usam mb_strlen.
 */

namespace Formata;

const VERSAO_DIRETRIZES = '2.6';

final class R
{
    // Seção 5.2 — Medida
    const LIMITE_PAGINA_1 = 34;
    const LIMITE_DEMAIS_PAGINAS = 40;
    const CARACTERES_POR_LINHA = 85;
    // Seção 5.3 — Decisão
    const RESTANTE_MINIMO_SEGUE = 8;
    const FICA = 'FICA';
    const QUEBRA = 'QUEBRA';
    const SEGUE = 'SEGUE';
    // Seções 5.5 e 5.6 — Marcação
    const ATRIBUTOS_QUEBRA = 'class="quebra-pagina" style="page-break-before: always;"';
    const P_ABRE = '<p>';
    const P_ABRE_QUEBRA = '<p class="quebra-pagina" style="page-break-before: always;">';
    const P_FECHA = '</p>';
    const STRONG_ABRE = '<strong>';
    const STRONG_FECHA = '</strong>';
    const TEXTO_LINHA_IMAGENS = '[INSERIR IMAGENS]';
    const LINHA_IMAGENS = self::P_ABRE_QUEBRA . self::STRONG_ABRE . self::TEXTO_LINHA_IMAGENS . self::STRONG_FECHA . self::P_FECHA;
    // Seção 7
    const MENSAGEM_DOCUMENTO_VAZIO = 'Envie o documento a ser formatado.';
    // Seção 5.1
    const NIVEL_MAXIMO_BLOCO = 3;
    // Decisões de interpretação (docs/REGRAS.md)
    const NEGRITO_EM_CODIGO = false; // D4
    const COLAGEM_SOMENTE_ADJACENTES = true; // D3 (validada)
    // Seção 4 — Rodapé
    const RODAPE_JANELA = 3;
    const RODAPE_TAMANHO_MAXIMO = 300;
    // Limites
    const LIMITE_CARACTERES_PADRAO = 1000000;
    const LIMITE_LINHAS_PADRAO = 20000;

    /** Espaços em branco exatamente como o str.isspace() do Python (referência). */
    const ESP = '\t\n\x0b\x0c\r\x1c-\x20\x{85}\x{a0}\x{1680}\x{2000}-\x{200a}\x{2028}\x{2029}\x{202f}\x{205f}\x{3000}';

    const RE_TITULO = '/^(#{1,4})[ \t]+[^' . self::ESP . ']/u';
    const RE_NEGRITO = '/\*\*([^\n]+?)\*\*/u';
    const RE_STRONG_TAG = '/<\/?strong[' . self::ESP . ']*>/iu';
    const RE_P_ABERTURA = '/<p([' . self::ESP . '][^<>]{0,2000})?>/iu';
    const RE_P_FECHAMENTO = '/<\/p[' . self::ESP . ']{0,20}>/iu';
    const RE_SEM_TEXTO = '/&nbsp;|&#160;|&#x0*a0;|<br[' . self::ESP . ']*\/?>/iu';
    const RE_TAG_QUALQUER = '/<\/?[A-Za-z][^<>]{0,2000}>/u';
    const RE_CERCA = '/^ {0,3}(`{3,}|~{3,})/u';
    const RE_CODIGO_INLINE = '/(?<!`)(`+)(?!`)([^\n]+?)(?<!`)\1(?!`)/u';

    const MARCADOR = '!\[[^\[\]\n]{0,500}\]\([^()\n]{0,2000}\)'
        . '|<img\b[^<>]{0,2000}>'
        . '|\[[ \t]{0,10}(?:imagem|imagens|images?|img|figuras?|fig\.?|prints?|capturas? de tela'
        . '|screenshots?|fotos?|ilustra[çc](?:ão|ões|ao|oes))\b[^\[\]\n]{0,300}\]';
    const RE_MARCADOR_IMAGEM = '/' . self::MARCADOR . '/iu';
    const RE_LINHA_SO_MARCADORES = '/^[' . self::ESP . ']*(?:(?:' . self::MARCADOR . ')[' . self::ESP . ']*)+\z/iu';

    const RE_RODAPE_CONFIABILIDADE = '/confiabilidade|confi[áa]vel|validade|v[áa]lid[oa]s?\b|vig[êe]ncia|vigente'
        . '|desatualizad|n[ãa]o[' . self::ESP . ']+controlad|c[óo]pia[' . self::ESP . ']+controlada|obsolet/iu';
    const RE_RODAPE_DOCUMENTO = '/documento|material|conte[úu]do|c[óo]pia|vers[ãa]o|impress[oa]|impress[ãa]o|publica[çc][ãa]o/iu';
    const RE_RODAPE_PROCEDIMENTO = '/\b(?:clientes?|titular|cpf|rg|cnh|fatura|oferta|plano|pedido|protocolo|contrato'
        . '|clique|acesse|selecione|digite|informe|registre|preencha|solicite|oriente|abra)\b/iu';
    const RE_PASSO_NUMERADO = '/^\d+[.)][' . self::ESP . ']/u';
}

const MODO_MARKDOWN = 'markdown';
const MODO_HTML = 'html';
const MOTIVO_BRANCO = 'linha_em_branco';
const MOTIVO_SEM_TEXTO = 'paragrafo_sem_texto';
const MOTIVO_RODAPE = 'rodape_confiabilidade';
const MOTIVO_IMAGENS_ANTERIOR = 'linha_imagens_anterior';

// ---------------------------------------------------------------- utilidades

function comprimento($s)
{
    return mb_strlen($s, 'UTF-8');
}

function aparar($s)
{
    return preg_replace('/^[' . R::ESP . ']+|[' . R::ESP . ']+\z/u', '', $s);
}

function aparar_direita($s)
{
    return preg_replace('/[' . R::ESP . ']+\z/u', '', $s);
}

function vazio_apos_aparar($s)
{
    return aparar($s) === '';
}

/**
 * Percorre as ocorrências de uma expressão uma a uma (sem montar a lista inteira,
 * o que estouraria a memória em linhas com centenas de milhares de ocorrências).
 * Nenhuma expressão do motor casa com texto vazio.
 */
function ocorrencias($re, $s)
{
    $pos = 0;
    while (preg_match($re, $s, $m, PREG_OFFSET_CAPTURE, $pos)) {
        yield $m;
        $pos = $m[0][1] + max(1, strlen($m[0][0]));
    }
}

function numero($n)
{
    return $n < 0 ? "\xE2\x88\x92" . abs($n) : (string) $n;
}

// ------------------------------------------------------------------ entrada

final class EntradaInvalida extends \RuntimeException
{
    public $codigo;
    public $mensagem;

    public function __construct($codigo, $mensagem)
    {
        parent::__construct($mensagem);
        $this->codigo = $codigo;
        $this->mensagem = $mensagem;
    }
}

final class Linha
{
    public $numero;
    public $bruto;
    public $texto;
    public $em_codigo = false;
    public $nivel_titulo = 0;

    public function __construct($numero, $bruto)
    {
        $this->numero = $numero;
        $this->bruto = $bruto;
        $this->texto = preg_replace(R::RE_STRONG_TAG, '', $bruto);
    }
}

final class Entrada
{
    public $modo;
    /** @var Linha[] */ public $tokenizadas;
    /** @var Linha[] */ public $linhas;
    /** @var Linha[] */ public $marcadores_finais;
    /** @var array[] */ public $removidas;
    public $tem_imagens;
    /** @var string[] */ public $avisos;
}

function remocao($numero, $motivo, $texto)
{
    return ['numero' => $numero, 'motivo' => $motivo, 'texto' => $texto];
}

function detectar_modo($texto)
{
    return preg_match(R::RE_P_ABERTURA, $texto) ? MODO_HTML : MODO_MARKDOWN;
}

function normalizar_quebras_de_linha($texto)
{
    if (strncmp($texto, "\xEF\xBB\xBF", 3) === 0) {
        $texto = substr($texto, 3);
    }
    return str_replace(["\r\n", "\r"], "\n", $texto);
}

/** @return array{0: Linha[], 1: string[]} */
function tokenizar($texto, $modo)
{
    if ($modo === MODO_MARKDOWN) {
        $linhas = [];
        foreach (explode("\n", $texto) as $i => $l) {
            $linhas[] = new Linha($i + 1, $l);
        }
        return [$linhas, []];
    }
    return tokenizar_html($texto);
}

/** Seção 7: em documento que já chega com <p>, cada <p>...</p> é uma linha. */
function tokenizar_html($texto)
{
    $linhas = [];
    $avisos = [];
    $fora_de_p = $quebras_antigas = $outros_atributos = $multilinha = 0;

    $adicionar_solto = function ($trecho) use (&$linhas, &$fora_de_p) {
        foreach (explode("\n", $trecho) as $parte) {
            if (!vazio_apos_aparar($parte)) {
                $fora_de_p++;
                $linhas[] = new Linha(count($linhas) + 1, $parte);
            }
        }
    };

    $pos = 0;
    while (preg_match(R::RE_P_ABERTURA, $texto, $m, PREG_OFFSET_CAPTURE, $pos)) {
        $fim_abertura = $m[0][1] + strlen($m[0][0]);
        if (!preg_match(R::RE_P_FECHAMENTO, $texto, $f, PREG_OFFSET_CAPTURE, $fim_abertura)) {
            break; // <p> sem fechamento: o resto é texto solto
        }
        $adicionar_solto((string) substr($texto, $pos, $m[0][1] - $pos));
        $atributos = (isset($m[1]) && $m[1][1] >= 0) ? aparar($m[1][0]) : '';
        if ($atributos !== '') {
            if (strpos($atributos, 'quebra-pagina') !== false || strpos($atributos, 'page-break') !== false) {
                $quebras_antigas++;
            } else {
                $outros_atributos++;
            }
        }
        $conteudo = (string) substr($texto, $fim_abertura, $f[0][1] - $fim_abertura);
        if (strpos($conteudo, "\n") !== false) {
            $multilinha++;
        }
        $linhas[] = new Linha(count($linhas) + 1, $conteudo);
        $pos = $f[0][1] + strlen($f[0][0]);
    }
    $adicionar_solto((string) substr($texto, $pos));

    if ($quebras_antigas) {
        $avisos[] = "$quebras_antigas quebra(s) de página antiga(s) descartada(s); as quebras foram recalculadas.";
    }
    if ($outros_atributos) {
        $avisos[] = "$outros_atributos parágrafo(s) com atributos não permitidos; os atributos foram descartados.";
    }
    if ($fora_de_p) {
        $avisos[] = "$fora_de_p linha(s) com texto fora de <p> tratadas como linhas comuns.";
    }
    if ($multilinha) {
        $avisos[] = "$multilinha parágrafo(s) com quebra de linha interna mantidos como uma linha só.";
    }
    return [$linhas, $avisos];
}

function eh_sem_texto($texto)
{
    return vazio_apos_aparar(preg_replace(R::RE_SEM_TEXTO, '', $texto));
}

function nivel_titulo($texto)
{
    return preg_match(R::RE_TITULO, $texto, $m) ? strlen($m[1]) : 0;
}

/** Marca blocos de código cercados e títulos ATX. Devolve avisos. @param Linha[] $linhas */
function classificar(array $linhas)
{
    $cerca = null;
    foreach ($linhas as $linha) {
        $tem = preg_match(R::RE_CERCA, $linha->texto, $m, PREG_OFFSET_CAPTURE);
        if ($cerca === null) {
            if ($tem) {
                $cerca = [$m[1][0][0], strlen($m[1][0])];
                $linha->em_codigo = true;
            } else {
                $linha->nivel_titulo = nivel_titulo($linha->texto);
            }
            continue;
        }
        $linha->em_codigo = true;
        if ($tem && $m[1][0][0] === $cerca[0] && strlen($m[1][0]) >= $cerca[1]
            && vazio_apos_aparar((string) substr($linha->texto, $m[0][1] + strlen($m[0][0])))) {
            $cerca = null;
        }
    }
    if ($cerca !== null) {
        return ['Bloco de código aberto sem fechamento: o restante do documento foi tratado como código.'];
    }
    return [];
}

function eh_marcador_so(Linha $linha)
{
    return !$linha->em_codigo && (bool) preg_match(R::RE_LINHA_SO_MARCADORES, $linha->texto);
}

/** Seção 4: refere-se à confiabilidade ou validade do documento e não é procedimento. */
function eh_rodape(Linha $linha)
{
    $t = aparar($linha->texto);
    if ($linha->em_codigo || $linha->nivel_titulo || ($t !== '' && ($t[0] === '#' || $t[0] === '|')) || eh_marcador_so($linha)) {
        return false;
    }
    if (preg_match(R::RE_PASSO_NUMERADO, $t) || comprimento($t) > R::RODAPE_TAMANHO_MAXIMO) {
        return false;
    }
    return preg_match(R::RE_RODAPE_CONFIABILIDADE, $t)
        && preg_match(R::RE_RODAPE_DOCUMENTO, $t)
        && !preg_match(R::RE_RODAPE_PROCEDIMENTO, $t);
}

function preparar(
    $texto,
    $modo = 'auto',
    $limite_caracteres = R::LIMITE_CARACTERES_PADRAO,
    $limite_linhas = R::LIMITE_LINHAS_PADRAO
) {
    if (!mb_check_encoding($texto, 'UTF-8')) {
        throw new EntradaInvalida('entrada_invalida', 'O conteúdo enviado não é texto em UTF-8.');
    }
    if (strpos($texto, "\0") !== false) {
        throw new EntradaInvalida('entrada_invalida', 'O conteúdo enviado parece ser um arquivo binário.');
    }
    $n = comprimento($texto);
    if ($n > $limite_caracteres) {
        throw new EntradaInvalida('documento_muito_extenso', "O documento tem $n caracteres; o limite é $limite_caracteres.");
    }

    $texto = normalizar_quebras_de_linha($texto);
    if ($modo === 'auto') {
        $modo = detectar_modo($texto);
    }
    if ($modo !== MODO_MARKDOWN && $modo !== MODO_HTML) {
        throw new EntradaInvalida('modo_invalido', "Modo desconhecido: $modo.");
    }

    list($tokenizadas, $avisos) = tokenizar($texto, $modo);
    if (count($tokenizadas) > $limite_linhas) {
        $q = count($tokenizadas);
        throw new EntradaInvalida('documento_muito_extenso', "O documento tem $q linhas; o limite é $limite_linhas.");
    }

    $removidas = [];
    // Seção 4: linha em branco é descartada, em qualquer posição.
    $linhas = [];
    foreach ($tokenizadas as $linha) {
        if (eh_sem_texto($linha->texto)) {
            $motivo = vazio_apos_aparar($linha->texto) ? MOTIVO_BRANCO : MOTIVO_SEM_TEXTO;
            if ($modo === MODO_HTML && vazio_apos_aparar($linha->bruto)) {
                $motivo = MOTIVO_SEM_TEXTO;
            }
            $removidas[] = remocao($linha->numero, $motivo, $linha->bruto);
        } else {
            $linhas[] = $linha;
        }
    }
    if (!$linhas) {
        throw new EntradaInvalida('documento_vazio', R::MENSAGEM_DOCUMENTO_VAZIO);
    }

    $avisos = array_merge($avisos, classificar($linhas));

    // Seção 5.6: a linha de imagens de uma formatação anterior sai e é recolocada.
    $tem_imagens = false;
    $mantidas = [];
    foreach ($linhas as $linha) {
        if (aparar($linha->texto) === R::TEXTO_LINHA_IMAGENS) {
            $tem_imagens = true;
            $removidas[] = remocao($linha->numero, MOTIVO_IMAGENS_ANTERIOR, $linha->bruto);
        } else {
            $mantidas[] = $linha;
        }
    }
    $linhas = $mantidas;
    if (!$linhas) {
        throw new EntradaInvalida('documento_vazio', R::MENSAGEM_DOCUMENTO_VAZIO);
    }

    // Seção 4: rodapé de confiabilidade entre as três últimas linhas.
    $janela = array_slice($linhas, -R::RODAPE_JANELA);
    $rodapes = [];
    foreach ($janela as $linha) {
        if (eh_rodape($linha)) {
            $rodapes[$linha->numero] = $linha;
        }
    }
    if ($rodapes && count($rodapes) === count($linhas)) {
        $avisos[] = 'O documento só contém linha(s) com cara de rodapé; nada foi removido.';
        $rodapes = [];
    }
    foreach ($janela as $linha) {
        if (!isset($rodapes[$linha->numero]) && !$linha->em_codigo && preg_match(R::RE_RODAPE_CONFIABILIDADE, $linha->texto)) {
            $avisos[] = "Linha {$linha->numero} cita validade ou confiabilidade, mas não cumpre os critérios "
                . 'de rodapé da seção 4 e foi mantida.';
        }
    }
    foreach ($rodapes as $linha) {
        $removidas[] = remocao($linha->numero, MOTIVO_RODAPE, $linha->bruto);
    }
    $linhas = array_values(array_filter($linhas, function (Linha $l) use ($rodapes) {
        return !isset($rodapes[$l->numero]);
    }));

    // Seção 5.6: documento com imagem ou marcador de imagem.
    if (!$tem_imagens) {
        foreach ($linhas as $l) {
            if (!$l->em_codigo && preg_match(R::RE_MARCADOR_IMAGEM, $l->texto)) {
                $tem_imagens = true;
                break;
            }
        }
    }

    // Marcadores que já vêm no fim ficam depois da linha de imagens, fora da conta.
    $fim = count($linhas);
    while ($fim > 0 && eh_marcador_so($linhas[$fim - 1])) {
        $fim--;
    }
    if ($fim === 0) {
        $avisos[] = 'O documento só contém marcadores de imagem; eles foram tratados como texto.';
        $fim = count($linhas);
    }

    usort($removidas, function (array $a, array $b) {
        return $a['numero'] < $b['numero'] ? -1 : ($a['numero'] > $b['numero'] ? 1 : 0);
    });

    $entrada = new Entrada();
    $entrada->modo = $modo;
    $entrada->tokenizadas = $tokenizadas;
    $entrada->linhas = array_slice($linhas, 0, $fim);
    $entrada->marcadores_finais = array_slice($linhas, $fim);
    $entrada->removidas = $removidas;
    $entrada->tem_imagens = $tem_imagens;
    $entrada->avisos = $avisos;
    return $entrada;
}

// ------------------------------------------------------------------- blocos

function custo_linha($texto)
{
    return max(1, (int) floor((comprimento($texto) + R::CARACTERES_POR_LINHA - 1) / R::CARACTERES_POR_LINHA));
}

final class Bloco
{
    public $indice;
    public $inicio;
    /** @var Linha[] */ public $linhas;

    public function __construct($indice, $inicio, array $linhas)
    {
        $this->indice = $indice;
        $this->inicio = $inicio;
        $this->linhas = $linhas;
    }

    public function tam()
    {
        $t = 0;
        foreach ($this->linhas as $l) {
            $t += custo_linha($l->texto);
        }
        return $t;
    }

    public function rotulo()
    {
        foreach ($this->linhas as $l) {
            if (abre_bloco($l)) {
                return $l->texto;
            }
        }
        $texto = aparar($this->linhas[0]->texto);
        if (comprimento($texto) > 60) {
            $texto = aparar_direita(mb_substr($texto, 0, 60, 'UTF-8')) . "\xE2\x80\xA6";
        }
        return $texto;
    }
}

function abre_bloco(Linha $linha)
{
    return !$linha->em_codigo && $linha->nivel_titulo >= 1 && $linha->nivel_titulo <= R::NIVEL_MAXIMO_BLOCO;
}

/** Seção 5.1. @param Linha[] $linhas @return Bloco[] */
function delimitar_blocos(array $linhas)
{
    if (!$linhas) {
        return [];
    }
    $inicios = [0];
    $anterior = null;
    foreach ($linhas as $i => $linha) {
        if (!abre_bloco($linha)) {
            continue;
        }
        $nivel = $linha->nivel_titulo;
        if ($anterior !== null) {
            $cola = $nivel > $anterior[0];
            if (R::COLAGEM_SOMENTE_ADJACENTES) {
                $cola = $cola && $i === $anterior[1] + 1;
            }
            if (!$cola) {
                $inicios[] = $i;
            }
        }
        $anterior = [$nivel, $i];
    }
    $blocos = [];
    $total = count($linhas);
    foreach ($inicios as $k => $ini) {
        $fim = isset($inicios[$k + 1]) ? $inicios[$k + 1] : $total;
        $blocos[] = new Bloco($k + 1, $ini, array_slice($linhas, $ini, $fim - $ini));
    }
    return $blocos;
}

// ---------------------------------------------------------------- paginação

/** Seção 5.3. @param array<int, array{0: string, 1: int}> $blocos @return array[] */
function paginar(array $blocos)
{
    $itens = [];
    $pagina = 1;
    $restante = R::LIMITE_PAGINA_1;
    $cheia = R::LIMITE_DEMAIS_PAGINAS;
    foreach ($blocos as $k => $par) {
        list($rotulo, $tam) = $par;
        $indice = $k + 1;
        if ($tam < 1) {
            throw new \InvalidArgumentException("Bloco $indice com Tam $tam: todo bloco tem ao menos uma linha.");
        }
        $anterior = $restante;
        $inicio = $pagina;
        $regra4 = false;
        if ($tam <= $restante) {
            $resultado = R::FICA;
            $novo = $restante - $tam;
            $conta = "$restante \xE2\x88\x92 $tam = " . numero($novo);
        } elseif ($indice === 1) {
            $resultado = R::SEGUE;
            $base = $restante + $cheia;
            $novo = $base - $tam;
            $pagina++;
            $conta = "$tam > $restante; $base \xE2\x88\x92 $tam";
            $regra4 = true;
        } elseif ($tam <= $cheia) {
            $resultado = R::QUEBRA;
            $novo = $cheia - $tam;
            $pagina++;
            $inicio = $pagina;
            $conta = "$tam > $restante; $cheia \xE2\x88\x92 $tam = " . numero($novo);
        } elseif ($restante >= R::RESTANTE_MINIMO_SEGUE && $tam <= $restante + $cheia) {
            $resultado = R::SEGUE;
            $base = $restante + $cheia;
            $novo = $base - $tam;
            $pagina++;
            $conta = "$restante \xE2\x89\xA5 " . R::RESTANTE_MINIMO_SEGUE . " e $tam \xE2\x89\xA4 $base; $base \xE2\x88\x92 $tam = " . numero($novo);
        } else {
            $resultado = R::QUEBRA;
            $base = 2 * $cheia;
            $novo = $base - $tam;
            $inicio = $pagina + 1;
            $pagina += 2;
            $conta = "$tam > $restante; $base \xE2\x88\x92 $tam";
            $regra4 = true;
        }
        if ($regra4) {
            $avancos = 0;
            while ($novo < 0) {
                $novo += $cheia;
                $pagina++;
                $avancos++;
            }
            if ($avancos) {
                $conta .= ' + ' . ($avancos * $cheia);
            }
            $conta .= ' = ' . numero($novo);
        }
        $restante = $novo;
        $itens[] = [
            'bloco' => $indice,
            'rotulo' => $rotulo,
            'tam' => $tam,
            'restante_anterior' => $anterior,
            'restante_novo' => $novo,
            'pagina_inicio' => $inicio,
            'pagina' => $pagina,
            'resultado' => $resultado,
            'conta' => $conta,
        ];
    }
    return $itens;
}

function texto_lista(array $itens, $tem_imagens)
{
    $linhas = ['Paginação:'];
    foreach ($itens as $it) {
        $linhas[] = "- Pág {$it['pagina']} | `{$it['rotulo']}` | Tam {$it['tam']} | {$it['conta']} | {$it['resultado']}";
    }
    if ($tem_imagens) {
        $linhas[] = '- `' . R::TEXTO_LINHA_IMAGENS . '` | ' . R::QUEBRA;
    }
    return implode("\n", $linhas);
}

// ----------------------------------------------------------------- marcação

/** Separa as tags <strong> do texto; null se desbalanceadas. Tokens: [tipo, valor]. */
function tokenizar_strong($bruto)
{
    $tokens = [];
    $prof = 0;
    $pos = 0;
    foreach (ocorrencias(R::RE_STRONG_TAG, $bruto) as $m) {
        list($tag, $ini) = $m[0];
        if ($ini > $pos) {
            $tokens[] = ['texto', (string) substr($bruto, $pos, $ini - $pos)];
        }
        $fecha = $tag[1] === '/';
        $prof += $fecha ? -1 : 1;
        if ($prof < 0) {
            return null;
        }
        $tokens[] = [$fecha ? 'fecha' : 'abre', $tag];
        $pos = $ini + strlen($tag);
    }
    if ($pos < strlen($bruto)) {
        $tokens[] = ['texto', (string) substr($bruto, $pos)];
    }
    return $prof === 0 ? $tokens : null;
}

/** Remove <strong> internos a outro <strong>; o texto não muda. */
function achatar_strong(array $tokens)
{
    $saida = [];
    $prof = 0;
    $achatou = false;
    foreach ($tokens as $t) {
        if ($t[0] === 'abre') {
            $prof++;
            if ($prof > 1) {
                $achatou = true;
                continue;
            }
        } elseif ($t[0] === 'fecha') {
            $prof--;
            if ($prof >= 1) {
                continue;
            }
        }
        $saida[] = $t;
    }
    return [$saida, $achatou];
}

function mascarar_codigo_inline($texto)
{
    return preg_replace_callback(R::RE_CODIGO_INLINE, function ($m) {
        return str_repeat("\0", strlen($m[0]));
    }, $texto);
}

/** Posições [início, fim) em bytes de cada **texto** a envolver. */
function trechos_negrito($texto, $em_codigo)
{
    if ($em_codigo && !R::NEGRITO_EM_CODIGO) {
        return [];
    }
    $alvo = R::NEGRITO_EM_CODIGO ? $texto : mascarar_codigo_inline($texto);
    $saida = [];
    foreach (ocorrencias(R::RE_NEGRITO, $alvo) as $m) {
        $saida[] = [$m[0][1], $m[0][1] + strlen($m[0][0])];
    }
    return $saida;
}

function marcar_conteudo(Linha $linha, array &$avisos)
{
    $texto = $linha->texto;
    if ($linha->nivel_titulo && !$linha->em_codigo) {
        if ($linha->bruto !== $texto && $linha->bruto !== R::STRONG_ABRE . $texto . R::STRONG_FECHA) {
            $avisos[] = "Linha {$linha->numero}: <strong> interno do título substituído pelo <strong> da linha inteira.";
        }
        return R::STRONG_ABRE . $texto . R::STRONG_FECHA;
    }

    $tokens = tokenizar_strong($linha->bruto);
    if ($tokens === null) {
        $avisos[] = "Linha {$linha->numero}: tags <strong> desbalanceadas foram descartadas e o negrito foi reaplicado.";
        $tokens = [['texto', $texto]];
    }
    list($tokens, $achatou) = achatar_strong($tokens);
    if ($achatou) {
        $avisos[] = "Linha {$linha->numero}: <strong> aninhado na entrada; mantido só o mais externo.";
    }

    // Máscara por byte do texto: "1" onde já há <strong>.
    $mascara = '';
    $prof = 0;
    foreach ($tokens as $t) {
        if ($t[0] === 'abre') {
            $prof++;
        } elseif ($t[0] === 'fecha') {
            $prof--;
        } else {
            $mascara .= str_repeat($prof > 0 ? '1' : '0', strlen($t[1]));
        }
    }

    $aberturas = [];
    $fechamentos = [];
    foreach (trechos_negrito($texto, $linha->em_codigo) as list($ini, $fim)) {
        $trecho = (string) substr($mascara, $ini, $fim - $ini);
        if (strspn($trecho, '1') === strlen($trecho)) {
            continue; // já está em negrito
        }
        if (strpos($trecho, '1') !== false) {
            $aviso = "Linha {$linha->numero}: negrito sobreposto a <strong> existente; mantido como recebido.";
            if (!$avisos || end($avisos) !== $aviso) {
                $avisos[] = $aviso;
            }
            continue;
        }
        $aberturas[] = $ini;
        $fechamentos[] = $fim;
    }
    return renderizar($tokens, $aberturas, $fechamentos);
}

/**
 * Reconstrói o conteúdo com os <strong> novos: a abertura entra logo antes do
 * byte de início e o fechamento logo depois do último byte do trecho, na mesma
 * ordem que a implementação de referência.
 */
function renderizar(array $tokens, array $aberturas, array $fechamentos)
{
    $saida = '';
    $a = 0; // ponteiro em $aberturas
    $f = 0; // ponteiro em $fechamentos
    $pos = 0; // posição no texto (sem tags)
    foreach ($tokens as $t) {
        if ($t[0] !== 'texto') {
            $saida .= $t[1];
            continue;
        }
        $ini = $pos;
        $fim = $pos + strlen($t[1]);
        $cursor = $ini;
        while (true) {
            $prox_f = ($f < count($fechamentos) && $fechamentos[$f] > $ini && $fechamentos[$f] <= $fim) ? $fechamentos[$f] : null;
            $prox_a = ($a < count($aberturas) && $aberturas[$a] >= $ini && $aberturas[$a] < $fim) ? $aberturas[$a] : null;
            if ($prox_f === null && $prox_a === null) {
                break;
            }
            // No mesmo ponto, o fechamento do trecho anterior vem antes da abertura do seguinte.
            if ($prox_f !== null && ($prox_a === null || $prox_f <= $prox_a)) {
                $saida .= substr($t[1], $cursor - $ini, $prox_f - $cursor) . R::STRONG_FECHA;
                $cursor = $prox_f;
                $f++;
            } else {
                $saida .= substr($t[1], $cursor - $ini, $prox_a - $cursor) . R::STRONG_ABRE;
                $cursor = $prox_a;
                $a++;
            }
        }
        $saida .= substr($t[1], $cursor - $ini);
        $pos = $fim;
    }
    return $saida;
}

function paragrafo($conteudo, $quebra)
{
    return ($quebra ? R::P_ABRE_QUEBRA : R::P_ABRE) . $conteudo . R::P_FECHA;
}

function gerar_html(array $linhas, array $inicios_quebra, array $marcadores_finais, $tem_imagens, array &$avisos)
{
    $saida = [];
    foreach ($linhas as $i => $l) {
        $saida[] = paragrafo(marcar_conteudo($l, $avisos), isset($inicios_quebra[$i]));
    }
    if ($tem_imagens) {
        $saida[] = R::LINHA_IMAGENS;
    }
    foreach ($marcadores_finais as $l) {
        $saida[] = paragrafo(marcar_conteudo($l, $avisos), false);
    }
    return implode("\n", $saida);
}

// ---------------------------------------------------------------- validação

const RE_STRONG_QUALQUER = '/<(\/?)strong\b[^>]*>/iu';

final class FormatoInvalido extends \RuntimeException
{
}

function posicao_caracteres($s, $bytes)
{
    return comprimento((string) substr($s, 0, $bytes));
}

/** Lê o HTML de saída como sequência de <p>, um por linha. @return array<int, array{0: bool, 1: string}> */
function separar_paragrafos($html)
{
    $paragrafos = [];
    $pos = 0;
    $n = strlen($html);
    while ($pos < $n) {
        if (substr_compare($html, R::P_ABRE_QUEBRA, $pos, strlen(R::P_ABRE_QUEBRA)) === 0) {
            $quebra = true;
            $inicio = $pos + strlen(R::P_ABRE_QUEBRA);
        } elseif (substr_compare($html, R::P_ABRE, $pos, strlen(R::P_ABRE)) === 0) {
            $quebra = false;
            $inicio = $pos + strlen(R::P_ABRE);
        } else {
            throw new FormatoInvalido('Conteúdo fora de <p> ou abertura não permitida na posição ' . posicao_caracteres($html, $pos) . '.');
        }
        $busca = $inicio;
        while (true) {
            $fim = strpos($html, R::P_FECHA, $busca);
            if ($fim === false) {
                throw new FormatoInvalido('Parágrafo sem </p> a partir da posição ' . posicao_caracteres($html, $pos) . '.');
            }
            $depois = $fim + strlen(R::P_FECHA);
            if ($depois === $n || $html[$depois] === "\n") {
                break;
            }
            $busca = $fim + 1;
        }
        $paragrafos[] = [$quebra, (string) substr($html, $inicio, $fim - $inicio)];
        $pos = $depois + 1;
        if ($depois < $n && $pos === $n) {
            throw new FormatoInvalido('Linha vazia no fim da saída.');
        }
    }
    return $paragrafos;
}

/** Intervalos (em bytes do texto sem tags) dentro de <strong>, profundidade máxima e problema. */
function spans_strong($conteudo)
{
    $spans = [];
    $prof = $maxima = 0;
    $pos_texto = 0;
    $abertura = 0;
    $pos = 0;
    foreach (ocorrencias(RE_STRONG_QUALQUER, $conteudo) as $m) {
        $pos_texto += $m[0][1] - $pos;
        $pos = $m[0][1] + strlen($m[0][0]);
        if ($m[1][0] !== '') {
            $prof--;
            if ($prof < 0) {
                return [$spans, $maxima, '</strong> sem abertura'];
            }
            if ($prof === 0) {
                $spans[] = [$abertura, $pos_texto];
            }
        } else {
            if ($prof === 0) {
                $abertura = $pos_texto;
            }
            $prof++;
            $maxima = max($maxima, $prof);
        }
    }
    if ($prof) {
        return [$spans, $maxima, '<strong> sem fechamento'];
    }
    return [$spans, $maxima, null];
}

function outras_tags($conteudo)
{
    preg_match_all(R::RE_TAG_QUALQUER, $conteudo, $ms);
    return array_values(array_filter($ms[0], function ($t) {
        return !preg_match('/\A<(\/?)strong\b[^>]*>\z/iu', $t);
    }));
}

function verificar(Entrada $entrada, array $blocos, array $itens, $html, array $avisos_marcacao)
{
    $erros = verificar_remocoes($entrada);
    try {
        $paragrafos = separar_paragrafos($html);
    } catch (FormatoInvalido $e) {
        $erros[] = 'HTML fora do formato permitido: ' . $e->getMessage();
        return $erros;
    }

    $mantidas = array_merge($entrada->linhas, $entrada->marcadores_finais);
    $removidas = [];
    foreach ($entrada->removidas as $r) {
        $removidas[$r['numero']] = true;
    }
    $sequencia = [];
    foreach ($entrada->tokenizadas as $l) {
        if (!isset($removidas[$l->numero])) {
            $sequencia[] = $l->numero;
        }
    }
    if ($sequencia !== array_map(function (Linha $l) {
        return $l->numero;
    }, $mantidas)) {
        $erros[] = 'Integridade: a sequência de linhas mantidas não corresponde à entrada menos as remoções autorizadas.';
    }

    $pos_imagens = $entrada->tem_imagens ? count($entrada->linhas) : null;
    $esperado = count($mantidas) + ($entrada->tem_imagens ? 1 : 0);
    if (count($paragrafos) !== $esperado) {
        $erros[] = 'Integridade: ' . count($paragrafos) . " parágrafos na saída; esperados $esperado.";
        return $erros;
    }

    $sobrepostas = [];
    foreach ($avisos_marcacao as $a) {
        if (preg_match('/^Linha (\d+): negrito sobreposto/u', $a, $m)) {
            $sobrepostas[(int) $m[1]] = true;
        }
    }
    $conteudo_saida = [];
    $k = 0;
    foreach ($paragrafos as $i => list($quebra, $conteudo)) {
        if ($i === $pos_imagens) {
            if (R::P_ABRE_QUEBRA . $conteudo . R::P_FECHA !== R::LINHA_IMAGENS) {
                $erros[] = 'Imagens: a linha de abertura da página de imagens está diferente do padrão.';
            }
            continue;
        }
        $linha = $mantidas[$k++];
        $erros = array_merge($erros, verificar_paragrafo($i + 1, $linha, $conteudo, $sobrepostas));
        $conteudo_saida[] = $conteudo;
    }

    $erros = array_merge($erros, verificar_quebras($blocos, $itens, $paragrafos, $pos_imagens));
    $erros = array_merge($erros, verificar_lista($itens));
    $erros = array_merge($erros, verificar_lista_contra_html($itens, array_slice($conteudo_saida, 0, count($entrada->linhas))));
    return $erros;
}

function verificar_remocoes(Entrada $entrada)
{
    $erros = [];
    $por_numero = [];
    foreach ($entrada->tokenizadas as $l) {
        $por_numero[$l->numero] = $l;
    }
    $antes_rodape = [];
    foreach ($entrada->removidas as $r) {
        if ($r['motivo'] !== MOTIVO_RODAPE) {
            $antes_rodape[$r['numero']] = true;
        }
    }
    $candidatas = [];
    foreach ($entrada->tokenizadas as $l) {
        if (!isset($antes_rodape[$l->numero])) {
            $candidatas[] = $l->numero;
        }
    }
    $janela = array_flip(array_slice($candidatas, -R::RODAPE_JANELA));
    foreach ($entrada->removidas as $r) {
        $linha = isset($por_numero[$r['numero']]) ? $por_numero[$r['numero']] : null;
        $n = $r['numero'];
        if ($linha === null || $linha->bruto !== $r['texto']) {
            $erros[] = "Remoção da linha $n não corresponde à entrada.";
        } elseif ($r['motivo'] === MOTIVO_BRANCO || $r['motivo'] === MOTIVO_SEM_TEXTO) {
            if (!eh_sem_texto($linha->texto)) {
                $erros[] = "Linha $n removida como vazia, mas tem texto.";
            }
        } elseif ($r['motivo'] === MOTIVO_RODAPE) {
            if (!isset($janela[$n]) || !eh_rodape($linha)) {
                $erros[] = "Linha $n removida como rodapé sem cumprir os critérios da seção 4.";
            }
        } elseif ($r['motivo'] === MOTIVO_IMAGENS_ANTERIOR) {
            if (aparar($linha->texto) !== R::TEXTO_LINHA_IMAGENS) {
                $erros[] = "Linha $n removida como linha de imagens anterior, mas o texto é outro.";
            }
        } else {
            $erros[] = "Linha $n removida por motivo não autorizado: {$r['motivo']}.";
        }
    }
    return $erros;
}

function verificar_paragrafo($n, Linha $linha, $conteudo, array $sobrepostas)
{
    $erros = [];
    $texto_saida = preg_replace(RE_STRONG_QUALQUER, '', $conteudo);
    $texto_origem = preg_replace(RE_STRONG_QUALQUER, '', $linha->bruto);
    if ($texto_saida !== $texto_origem) {
        $erros[] = "Integridade: o texto do parágrafo $n difere da linha {$linha->numero} da entrada.";
        return $erros;
    }
    if (eh_sem_texto($texto_saida)) {
        $erros[] = "Parágrafo $n sem texto.";
    }
    if (outras_tags($conteudo) !== outras_tags($linha->bruto)) {
        $erros[] = "Parágrafo $n: tag além de <p> e <strong> introduzida.";
    }
    list($spans, $maxima, $problema) = spans_strong($conteudo);
    if ($problema !== null) {
        $erros[] = "Parágrafo $n: $problema.";
        return $erros;
    }
    if ($maxima > 1) {
        $erros[] = "Parágrafo $n: <strong> dentro de <strong>.";
    }
    if ($linha->nivel_titulo && !$linha->em_codigo) {
        if ($conteudo !== R::STRONG_ABRE . $linha->texto . R::STRONG_FECHA) {
            $erros[] = "Parágrafo $n: título sem um <strong> único na linha inteira.";
        }
        return $erros;
    }
    $permitidos = [];
    foreach (spans_strong($linha->bruto)[0] as $s) {
        $permitidos[$s[0] . ':' . $s[1]] = true;
    }
    $negritos = trechos_negrito($linha->texto, $linha->em_codigo);
    $sobreposto = isset($sobrepostas[$linha->numero]);
    $k = 0;
    $total = count($spans);
    foreach ($negritos as list($ini, $fim)) {
        while ($k < $total && $spans[$k][1] < $fim) {
            $k++;
        }
        $dentro = $k < $total && $spans[$k][0] <= $ini && $fim <= $spans[$k][1];
        if (!$dentro && !$sobreposto) {
            $erros[] = "Parágrafo $n: `**` sem <strong> na posição " . posicao_caracteres($linha->texto, $ini) . '.';
            break;
        }
    }
    foreach ($negritos as list($ini, $fim)) {
        $permitidos[$ini . ':' . $fim] = true;
    }
    foreach ($spans as $s) {
        if (!isset($permitidos[$s[0] . ':' . $s[1]])) {
            $erros[] = "Parágrafo $n: <strong> acrescentado fora de título ou negrito.";
            break;
        }
    }
    return $erros;
}

function verificar_quebras(array $blocos, array $itens, array $paragrafos, $pos_imagens)
{
    $erros = [];
    $esperadas = [];
    foreach ($blocos as $k => $b) {
        if ($itens[$k]['resultado'] === R::QUEBRA) {
            $esperadas[$b->inicio] = true;
        }
    }
    if ($pos_imagens !== null) {
        $esperadas[$pos_imagens] = true;
    }
    $marcadas = [];
    foreach ($paragrafos as $i => list($quebra)) {
        if ($quebra) {
            $marcadas[$i] = true;
        }
    }
    $indevidas = array_keys(array_diff_key($marcadas, $esperadas));
    sort($indevidas);
    foreach ($indevidas as $i) {
        $erros[] = 'Quebra indevida no parágrafo ' . ($i + 1) . '.';
    }
    $faltando = array_keys(array_diff_key($esperadas, $marcadas));
    sort($faltando);
    foreach ($faltando as $i) {
        $erros[] = 'Falta a quebra no parágrafo ' . ($i + 1) . ', primeira linha de bloco QUEBRA.';
    }
    $n_quebras = ($pos_imagens !== null ? 1 : 0);
    foreach ($itens as $it) {
        if ($it['resultado'] === R::QUEBRA) {
            $n_quebras++;
        }
    }
    if (count($marcadas) !== $n_quebras) {
        $erros[] = count($marcadas) . " quebras no HTML para $n_quebras itens QUEBRA na lista.";
    }
    return $erros;
}

/** Conferência da seção 5.4 mais uma simulação física das páginas. */
function verificar_lista(array $itens)
{
    $erros = [];
    $restante = R::LIMITE_PAGINA_1;
    $pagina_anterior = 1;
    $pagina = 1;
    $usado = 0;
    $capacidade = function ($p) {
        return $p === 1 ? R::LIMITE_PAGINA_1 : R::LIMITE_DEMAIS_PAGINAS;
    };
    foreach ($itens as $i => $it) {
        $k = $i + 1;
        $rot = "Item $k (`{$it['rotulo']}`)";
        if ($it['bloco'] !== $k) {
            $erros[] = "$rot: fora de ordem.";
        }
        if ($it['restante_anterior'] !== $restante) {
            $erros[] = "$rot: Restante anterior {$it['restante_anterior']}, esperado $restante.";
        }
        if ($it['restante_novo'] < 0) {
            $erros[] = "$rot: resultado negativo.";
        }
        $T = $it['tam'];
        $Ra = $it['restante_anterior'];
        $cheia = R::LIMITE_DEMAIS_PAGINAS;
        if ($it['resultado'] === R::FICA) {
            if ($T > $Ra) {
                $erros[] = "$rot: FICA sem caber no Restante ($T > $Ra).";
            }
            if ($it['pagina'] !== $pagina_anterior) {
                $erros[] = "$rot: Pág mudou em bloco FICA.";
            }
        } elseif ($it['resultado'] === R::QUEBRA) {
            if ($k === 1) {
                $erros[] = "$rot: o primeiro bloco nunca leva quebra.";
            }
            if ($T <= $Ra) {
                $erros[] = "$rot: quebra com espaço sobrando ($T \xE2\x89\xA4 $Ra).";
            }
            if ($T > $cheia && $Ra >= R::RESTANTE_MINIMO_SEGUE && $T <= $Ra + $cheia) {
                $erros[] = "$rot: QUEBRA onde a regra pede SEGUE.";
            }
        } elseif ($it['resultado'] === R::SEGUE) {
            $primeiro = $k === 1 && $T > $Ra;
            $normal = $Ra >= R::RESTANTE_MINIMO_SEGUE && $cheia < $T && $T <= $Ra + $cheia;
            if (!($primeiro || $normal)) {
                $erros[] = "$rot: SEGUE sem cumprir Restante \xE2\x89\xA5 8 e Tam \xE2\x89\xA4 Restante + 40.";
            }
        } else {
            $erros[] = "$rot: resultado desconhecido {$it['resultado']}.";
        }
        $sufixo = '= ' . numero($it['restante_novo']);
        if (substr($it['conta'], -strlen($sufixo)) !== $sufixo) {
            $erros[] = "$rot: a conta escrita não termina no novo Restante.";
        }

        if ($it['resultado'] === R::QUEBRA) {
            $pagina++;
            $usado = 0;
        }
        if ($it['pagina_inicio'] !== $pagina) {
            $erros[] = "$rot: começa na página {$it['pagina_inicio']}; simulação indica $pagina.";
        }
        $faltam = $T;
        while ($faltam) {
            $livre = $capacidade($pagina) - $usado;
            if ($livre === 0) {
                $pagina++;
                $usado = 0;
                continue;
            }
            $ocupa = min($livre, $faltam);
            $usado += $ocupa;
            $faltam -= $ocupa;
        }
        $sobra = $capacidade($pagina) - $usado;
        if ($it['pagina'] !== $pagina || $it['restante_novo'] !== $sobra) {
            $erros[] = "$rot: lista indica Pág {$it['pagina']} e Restante {$it['restante_novo']}; "
                . "simulação indica Pág $pagina e Restante $sobra.";
        }
        $restante = $it['restante_novo'];
        $pagina_anterior = $it['pagina'];
    }
    return $erros;
}

/** Refaz os blocos a partir do próprio HTML e compara com a lista. */
function verificar_lista_contra_html(array $itens, array $conteudos)
{
    $linhas = [];
    foreach ($conteudos as $i => $c) {
        $linhas[] = new Linha($i + 1, $c);
    }
    classificar($linhas);
    $blocos = delimitar_blocos($linhas);
    if (count($blocos) !== count($itens)) {
        return ['A lista tem ' . count($itens) . ' itens, mas o HTML tem ' . count($blocos) . ' blocos.'];
    }
    $erros = [];
    foreach ($blocos as $k => $b) {
        $it = $itens[$k];
        $tam = $b->tam();
        if ($b->rotulo() !== $it['rotulo'] || $tam !== $it['tam']) {
            $erros[] = "Item {$it['bloco']}: lista diz `{$it['rotulo']}` Tam {$it['tam']}; HTML tem `{$b->rotulo()}` Tam $tam.";
        }
    }
    return $erros;
}

// -------------------------------------------------------------------- motor

function bloco_de_codigo($html)
{
    $maior = 0;
    if (preg_match_all('/`{3,}/', $html, $ms)) {
        foreach ($ms[0] as $m) {
            $maior = max($maior, strlen($m));
        }
    }
    $cerca = str_repeat('`', max(3, $maior + 1));
    return "$cerca\n$html\n$cerca";
}

function resultado_base($ok, $codigo, $mensagem)
{
    return [
        'ok' => $ok,
        'codigo' => $codigo,
        'mensagem' => $mensagem,
        'modo' => '',
        'lista_paginacao' => '',
        'itens' => [],
        'html' => '',
        'resposta' => '',
        'total_paginas_texto' => 0,
        'tem_imagens' => false,
        'removidas' => [],
        'avisos' => [],
        'erros' => [],
        'versao_diretrizes' => VERSAO_DIRETRIZES,
    ];
}

/**
 * Formata o documento. Devolve o mesmo dicionário da implementação de
 * referência (campos ok, codigo, mensagem, lista_paginacao, itens, html, ...).
 */
function formatar(
    $texto,
    $modo = 'auto',
    $limite_caracteres = R::LIMITE_CARACTERES_PADRAO,
    $limite_linhas = R::LIMITE_LINHAS_PADRAO
) {
    try {
        $entrada = preparar($texto, $modo, $limite_caracteres, $limite_linhas);
    } catch (EntradaInvalida $e) {
        return resultado_base(false, $e->codigo, $e->mensagem);
    }

    $blocos = delimitar_blocos($entrada->linhas);
    $itens = paginar(array_map(function (Bloco $b) {
        return [$b->rotulo(), $b->tam()];
    }, $blocos));
    $inicios_quebra = [];
    foreach ($blocos as $k => $b) {
        if ($itens[$k]['resultado'] === R::QUEBRA) {
            $inicios_quebra[$b->inicio] = true;
        }
    }

    $avisos_marcacao = [];
    $html = gerar_html($entrada->linhas, $inicios_quebra, $entrada->marcadores_finais, $entrada->tem_imagens, $avisos_marcacao);
    $avisos = array_merge($entrada->avisos, $avisos_marcacao);

    $outras = [];
    foreach ($entrada->linhas as $l) {
        if (preg_match_all(R::RE_TAG_QUALQUER, $l->texto, $ms)) {
            foreach ($ms[0] as $t) {
                $partes = preg_split('/[' . R::ESP . ']+/u', $t, -1, PREG_SPLIT_NO_EMPTY);
                $outras[mb_strtolower(trim($partes[0], '<>/'), 'UTF-8')] = true;
            }
        }
    }
    if ($outras) {
        $nomes = array_map('strval', array_keys($outras));
        sort($nomes, SORT_STRING);
        $avisos[] = 'O documento já contém tags além de <p> e <strong> (' . implode(', ', $nomes)
            . '); foram mantidas como conteúdo, sem alteração.';
    }

    $lista = texto_lista($itens, $entrada->tem_imagens);
    $erros = verificar($entrada, $blocos, $itens, $html, $avisos_marcacao);

    $r = resultado_base(!$erros, $erros ? 'falha_validacao' : 'ok',
        $erros ? 'O resultado não passou nas verificações e não foi entregue.' : 'Documento formatado.');
    $r['modo'] = $entrada->modo;
    $r['lista_paginacao'] = $lista;
    $r['itens'] = $itens;
    $r['total_paginas_texto'] = $itens ? $itens[count($itens) - 1]['pagina'] : 0;
    $r['tem_imagens'] = $entrada->tem_imagens;
    $r['removidas'] = $entrada->removidas;
    $r['avisos'] = $avisos;
    if ($erros) {
        $r['erros'] = $erros;
    } else {
        $r['html'] = $html;
        $r['resposta'] = $lista . "\n\n" . bloco_de_codigo($html);
    }
    return $r;
}
