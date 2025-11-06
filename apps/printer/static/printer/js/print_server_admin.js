(function($) {
    'use strict';
    
    // Espera o DOM carregar
    $(document).ready(function() {
        
        // Pega os elementos
        const testBtn = $('#test-connection-btn');
        const fetchBtn = $('#fetch-printers-btn');
        const printerList = $('#printer-list');
        const statusMsg = $('#printer-status-message');
        
        // Pega os campos do formulário
        const printerNameField = $('#id_nome_impressora_padrao');
        
        // Pega as URLs dos dados do script tag
        const dataScript = $('#print-server-data');
        if (!dataScript.length) return; // Sai se não estiver na página correta

        const testUrl = dataScript.data('test-url');
        const fetchUrl = dataScript.data('fetch-url');
        
        // Pega o token CSRF para os requests
        const csrftoken = $('input[name="csrfmiddlewaretoken"]').val();

        /**
         * Trava os botões e mostra uma mensagem de "Carregando"
         */
        function setLoading(message) {
            statusMsg.text(message).removeClass('success error').addClass('loading').show();
            testBtn.prop('disabled', true);
            fetchBtn.prop('disabled', true);
        }

        /**
         * Destrava os botões e mostra uma mensagem final
         */
        function setStatus(message, isError = false) {
            statusMsg.text(message)
                .removeClass('loading')
                .toggleClass('success', !isError)
                .toggleClass('error', isError)
                .show();
            testBtn.prop('disabled', false);
            fetchBtn.prop('disabled', false);
        }

        // --- Ação 1: Testar Conexão ---
        testBtn.on('click', function() {
            setLoading('Testando conexão...');
            
            $.ajax({
                url: testUrl,
                type: 'GET',
                headers: {'X-CSRFToken': csrftoken},
                success: function(response) {
                    setStatus(response.mensagem, false);
                },
                error: function(xhr) {
                    const errorMsg = xhr.responseJSON ? xhr.responseJSON.mensagem : "Erro desconhecido.";
                    setStatus(`Falha: ${errorMsg}`, true);
                }
            });
        });

        // --- Ação 2: Buscar Impressoras ---
        fetchBtn.on('click', function() {
            setLoading('Buscando impressoras...');
            
            $.ajax({
                url: fetchUrl,
                type: 'GET',
                headers: {'X-CSRFToken': csrftoken},
                success: function(response) {
                    if (response.status === 'sucesso' && response.impressoras) {
                        printerList.empty(); // Limpa a lista
                        
                        if (response.impressoras.length === 0) {
                            printerList.append('<li class="readonly">Nenhuma impressora encontrada no servidor.</li>');
                        }
                        
                        const currentPrinter = printerNameField.val();

                        // Popula a lista com as impressoras
                        response.impressoras.forEach(function(printer) {
                            const $li = $('<li>')
                                .text(printer.nome)
                                .attr('data-printer-name', printer.nome);
                            
                            // Marca a impressora que já está salva
                            if (printer.nome === currentPrinter) {
                                $li.addClass('selected');
                            }
                            
                            printerList.append($li);
                        });
                        
                        setStatus(response.impressoras.length + ' impressoras encontradas.', false);
                    } else {
                        setStatus(response.mensagem || "Resposta inválida do servidor.", true);
                    }
                },
                error: function(xhr) {
                    const errorMsg = xhr.responseJSON ? xhr.responseJSON.mensagem : "Erro desconhecido.";
                    setStatus(`Falha: ${errorMsg}`, true);
                }
            });
        });
        
        // --- Ação 3: Selecionar uma Impressora ---
        // Usa "event delegation" para lidar com cliques nos <li>s
        printerList.on('click', 'li:not(.readonly)', function() {
            const $li = $(this);
            const printerName = $li.data('printer-name');
            
            // Atualiza a seleção visual
            printerList.find('li').removeClass('selected');
            $li.addClass('selected');
            
            // Define o valor no campo do formulário
            printerNameField.val(printerName);
            
            // Mostra uma mensagem de status
            setStatus(`Impressora '${printerName}' selecionada. Clique em Salvar.`, false);
        });

    });
})(django.jQuery || jQuery);