<?php
/**
 * Configuração do Formata.AI no hub. Edite só os valores à direita.
 */
return [
    // Tamanho máximo do documento, em bytes (1048576 = 1 MB).
    'limite_bytes' => 1048576,

    // Linhas (ou parágrafos <p>) por documento.
    'limite_linhas' => 20000,

    // Segundos por formatação; ao passar disso, a requisição é interrompida.
    'tempo_limite' => 15,

    // Login do hub: caminho, a partir desta pasta, do arquivo PHP que as outras
    // ferramentas do hub incluem para exigir login (por exemplo '../includes/verifica-login.php').
    // Vazio = sem verificação de login (use só em rede interna).
    'arquivo_autenticacao' => '',

    // Registro técnico no log de erros do PHP (sem o conteúdo dos documentos).
    'registrar_log' => true,

    // Página diagnostico.php (mostra versão do PHP e o que falta no servidor).
    // Depois que tudo estiver funcionando, pode trocar para false.
    'diagnostico_ativo' => true,
];
