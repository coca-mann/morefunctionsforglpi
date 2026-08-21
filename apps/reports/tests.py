from unittest.mock import patch

from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from apps.dbcom.models import GLPIConfig
from apps.reports.models import ItemLaudo, LaudoBaixa, MotivoBaixa


class ItemLaudoStatusLockTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tecnico', password='x')
        self.laudo = LaudoBaixa.objects.create(
            tecnico_responsavel=self.user,
            destinacao='DESCARTE',
        )
        self.item = ItemLaudo.objects.create(
            laudo=self.laudo,
            glpi_id=1,
            nome_equipamento='PC-001',
            tipo_equipamento='Computador',
        )

    def test_new_item_defaults_to_pendente(self):
        self.assertEqual(self.item.status, 'PENDENTE')

    def test_pendente_item_can_be_edited(self):
        self.item.numero_serie = 'SN-123'
        self.item.save()
        self.item.refresh_from_db()
        self.assertEqual(self.item.numero_serie, 'SN-123')

    def test_transition_to_processado_is_allowed(self):
        self.item.status = 'PROCESSADO'
        self.item.processado_em = None
        self.item.save()
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, 'PROCESSADO')

    def test_editing_already_processado_item_is_blocked(self):
        self.item.status = 'PROCESSADO'
        self.item.save()

        self.item.numero_serie = 'SN-999'
        with self.assertRaises(ValidationError):
            self.item.save()

    def test_deleting_already_processado_item_is_blocked(self):
        self.item.status = 'PROCESSADO'
        self.item.save()

        with self.assertRaises(ValidationError):
            self.item.delete()

    def test_falha_item_can_still_be_edited_and_deleted(self):
        self.item.status = 'FALHA'
        self.item.glpi_erro = 'timeout'
        self.item.save()

        self.item.numero_serie = 'SN-001'
        self.item.save()  # must not raise

        self.item.delete()  # must not raise
        self.assertFalse(ItemLaudo.objects.filter(pk=self.item.pk).exists())


class AtualizarStatusItensNoGlpiActionTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser('admin', 'admin@example.com', 'senha123')
        self.client = Client()
        self.client.force_login(self.superuser)

        self.motivo = MotivoBaixa.objects.create(codigo='M1', titulo='Quebrado', descricao='Equipamento com defeito.')
        self.laudo = LaudoBaixa.objects.create(
            tecnico_responsavel=self.superuser,
            destinacao='DESCARTE',
        )
        self.item_pendente = ItemLaudo.objects.create(
            laudo=self.laudo, glpi_id=101, nome_equipamento='PC-101',
            tipo_equipamento='Computador', motivo_baixa=self.motivo,
        )
        self.item_ja_processado = ItemLaudo.objects.create(
            laudo=self.laudo, glpi_id=102, nome_equipamento='PC-102',
            tipo_equipamento='Computador', motivo_baixa=self.motivo,
            status='PROCESSADO',
        )
        GLPIConfig.objects.create(
            glpi_api_url='https://glpi.example.com/apirest.php',
            glpi_app_token='app-token',
            glpi_user_token='user-token',
            glpi_status_baixa_id=42,
        )

    def _post_action(self, extra=None):
        data = {
            'action': 'atualizar_status_itens_no_glpi',
            ACTION_CHECKBOX_NAME: [str(self.laudo.pk)],
        }
        if extra:
            data.update(extra)
        return self.client.post(reverse('admin:reports_laudobaixa_changelist'), data)

    def test_first_click_renders_confirmation_without_calling_glpi(self):
        with patch('apps.reports.admin.get_legacy_session_token') as mock_session:
            response = self._post_action()
            mock_session.assert_not_called()

        self.assertContains(response, 'PC-101')
        self.assertNotContains(response, 'PC-102')  # já processado, não entra na lista a processar
        self.item_pendente.refresh_from_db()
        self.assertEqual(self.item_pendente.status, 'PENDENTE')

    @patch('apps.reports.admin.kill_legacy_session')
    @patch('apps.reports.admin.update_glpi_asset_status', return_value=(True, None))
    @patch('apps.reports.admin.get_legacy_session_token', return_value=('sess-token', None))
    def test_confirmed_submit_processes_only_pending_items(self, mock_session, mock_update, mock_kill):
        self._post_action({'confirma_baixa_glpi': 'yes'})

        mock_update.assert_called_once()
        self.item_pendente.refresh_from_db()
        self.laudo.refresh_from_db()
        self.assertEqual(self.item_pendente.status, 'PROCESSADO')
        self.assertEqual(self.item_pendente.processado_por_id, self.superuser.pk)
        self.assertIsNotNone(self.item_pendente.processado_em)
        self.assertEqual(self.laudo.status, 'PROCESSADO')
        self.assertIsNotNone(self.laudo.data_baixa_glpi)

    @patch('apps.reports.admin.kill_legacy_session')
    @patch('apps.reports.admin.update_glpi_asset_status', return_value=(False, 'timeout'))
    @patch('apps.reports.admin.get_legacy_session_token', return_value=('sess-token', None))
    def test_failed_item_is_marked_falha_and_laudo_stays_rascunho(self, mock_session, mock_update, mock_kill):
        self._post_action({'confirma_baixa_glpi': 'yes'})

        self.item_pendente.refresh_from_db()
        self.laudo.refresh_from_db()
        self.assertEqual(self.item_pendente.status, 'FALHA')
        self.assertEqual(self.item_pendente.glpi_erro, 'timeout')
        self.assertEqual(self.laudo.status, 'RASCUNHO')

    def test_action_rejects_laudo_without_destinacao(self):
        self.laudo.destinacao = ''
        self.laudo.save()
        response = self._post_action()
        self.assertEqual(response.status_code, 302)

    def test_action_warns_when_all_items_already_processed(self):
        self.item_pendente.status = 'PROCESSADO'
        self.item_pendente.save()
        response = self._post_action()
        self.assertEqual(response.status_code, 302)
