/*global interpolate, ngettext*/
document.addEventListener('DOMContentLoaded', function () {
    /*
     * Esconde o checkbox "Remover" da inline de ItemLaudo para linhas cujo
     * item já está PROCESSADO no GLPI.
     *
     * O Django TabularInline não expõe has_delete_permission por linha (só
     * tudo-ou-nada pro formset inteiro) — a trava real contra exclusão é o
     * ValidationError de ItemLaudo.delete() no model. Isso aqui é só UX: evita
     * que o usuário marque "Remover" numa linha que o servidor vai recusar de
     * qualquer forma, sem precisar de um formset customizado.
     */
    document.querySelectorAll('.lb-badge--processado').forEach(function (badge) {
        var row = badge.closest('tr') || badge.closest('[class*="dynamic-"]');
        if (!row) {
            return;
        }
        var deleteCheckbox = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (!deleteCheckbox) {
            return;
        }
        // Esconde só o checkbox, não a célula — escondendo a <td> ela some
        // da linha e desalinha as colunas com o resto da tabela.
        deleteCheckbox.style.display = 'none';
    });

    /*
     * Desabilita (e esconde) o checkbox de seleção da changelist de Laudo
     * de Baixa pras linhas já PROCESSADO — não faz sentido selecionar um
     * laudo fechado pra rodar uma action nele. 'data-laudo-status' vem de
     * LaudoBaixaAdmin.status_com_marcador.
     */
    var linhasTravadas = Array.from(
        document.querySelectorAll('[data-laudo-status="PROCESSADO"]')
    ).map(function (marcador) {
        return marcador.closest('tr');
    }).filter(Boolean);

    if (linhasTravadas.length === 0) {
        return;
    }

    linhasTravadas.forEach(function (row) {
        var checkbox = row.querySelector('input[name="_selected_action"]');
        if (checkbox) {
            // 'disabled' (não só escondido) é o que importa de verdade: um
            // input disabled não é enviado no submit do form, então mesmo
            // que o "selecionar todos" continue marcando ele via JS, esse
            // valor não é enviado quando a action roda.
            checkbox.disabled = true;
            checkbox.style.display = 'none';
        }
    });

    /*
     * O actions.js do Unfold (e o do Django) marca 'checked' e destaca a
     * linha (.selected) direto em todos os checkboxes de ação quando o
     * "selecionar todos" do cabeçalho é clicado, sem checar 'disabled' —
     * então mesmo travado, ele aparecia marcado/destacado visualmente e o
     * contador ("N de N selecionados") contava as linhas travadas também.
     * Corrige isso desfazendo o efeito nas linhas travadas e recalculando
     * o contador com a mesma fórmula do actions.js, sempre depois (setTimeout 0)
     * do listener original já ter rodado.
     */
    function corrigirSelecaoTravada() {
        var wrapper = document.querySelector('.result-list-wrapper') || document;
        var todosCheckboxes = wrapper.querySelectorAll('tr input.action-select');
        var counter = wrapper.querySelector('span.action-counter');

        linhasTravadas.forEach(function (row) {
            var checkbox = row.querySelector('input[name="_selected_action"]');
            if (checkbox) {
                checkbox.checked = false;
            }
            row.classList.remove('selected');
        });

        if (!counter) {
            return;
        }
        var sel = Array.from(todosCheckboxes).filter(function (el) {
            return el.checked;
        }).length;
        var total = Number(counter.dataset.actionsIcnt || todosCheckboxes.length);
        counter.textContent = interpolate(
            ngettext('%(sel)s of %(cnt)s selected', '%(sel)s of %(cnt)s selected', sel),
            { sel: sel, cnt: total },
            true
        );
        var allToggle = wrapper.querySelector('.action-toggle');
        if (allToggle) {
            allToggle.checked = sel > 0 && sel === todosCheckboxes.length;
        }
    }

    var actionToggle = document.querySelector('.action-toggle');
    if (actionToggle) {
        actionToggle.addEventListener('click', function () {
            setTimeout(corrigirSelecaoTravada, 0);
        });
    }
    var resultList = document.querySelector('.result-list');
    if (resultList) {
        resultList.addEventListener('change', function (event) {
            if (event.target.classList.contains('action-select')) {
                setTimeout(corrigirSelecaoTravada, 0);
            }
        });
    }
});
