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
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.lb-badge--processado').forEach(function (badge) {
        var row = badge.closest('tr') || badge.closest('[class*="dynamic-"]');
        if (!row) {
            return;
        }
        var deleteCheckbox = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (!deleteCheckbox) {
            return;
        }
        var cell = deleteCheckbox.closest('td') || deleteCheckbox.parentElement;
        if (cell) {
            cell.style.display = 'none';
        }
    });
});
