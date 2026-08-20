# Baixa Patrimonial — Rastreio por Item, Confirmação e Reprocessamento Seletivo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the all-or-nothing `atualizar_status_itens_no_glpi` admin action with a per-item-tracked, confirmed, selectively-retryable flow for applying the GLPI disposal status to `ItemLaudo` records.

**Architecture:** `ItemLaudo` gains its own `status`/`glpi_erro`/`processado_em`/`processado_por` fields, which become the single source of truth enforced in `ItemLaudo.save()`/`delete()`. The admin action becomes two-phase (Django's standard "confirmation page" action pattern, same mechanism `delete_selected` uses): first POST renders a review page, second POST (with a confirmation marker) does the real work, touching only items not already `PROCESSADO`. `LaudoBaixa.status` stays as an aggregate recomputed from item statuses after each run.

**Tech Stack:** Django 6.0.1 admin, `django.test.TestCase` + `django.test.Client`, `unittest.mock`.

**Spec:** `docs/superpowers/specs/2026-08-20-baixa-patrimonial-item-tracking-design.md`

## Global Constraints

- Auditoria fica no estado atual por item (não histórico de tentativas).
- Tela de confirmação é lista simples + status alvo, sem pré-checagem ao vivo no GLPI.
- Trava de edição/exclusão passa a ser por item (`ItemLaudo.status`), não mais pelo agregado do laudo.
- `LaudoBaixaAdmin.has_delete_permission`/`get_readonly_fields` e o bloqueio em `importar_itens_glpi` (nível do laudo) não mudam.
- Checkbox de exclusão por linha no `TabularInline` está fora de escopo (limitação do Django); a trava real é o `ValidationError` do model.

---

### Task 1: `ItemLaudo` status/audit fields, migration, and corrected save/delete guard

**Files:**
- Modify: `apps/reports/models.py:140-224` (the `ItemLaudo` class)
- Create: `apps/reports/migrations/0008_itemlaudo_status_tracking.py` (generated, not hand-written)
- Create: `apps/reports/tests.py`

**Interfaces:**
- Produces: `ItemLaudo.status` (`str`, one of `'PENDENTE'`/`'PROCESSADO'`/`'FALHA'`, default `'PENDENTE'`), `ItemLaudo.glpi_erro` (`str`), `ItemLaudo.processado_em` (`datetime | None`), `ItemLaudo.processado_por` (`User | None`). `ItemLaudo.save()`/`delete()` raise `django.core.exceptions.ValidationError` when the **persisted** status is already `'PROCESSADO'` (in-memory transitions *into* `'PROCESSADO'` are allowed).

Current `ItemLaudo.save()`/`delete()` (to be replaced):

```python
    def save(self, *args, **kwargs):
        if self.laudo.status == 'PROCESSADO':
            raise ValidationError("Laudo já processado no GLPI: não é possível adicionar/editar itens.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.laudo.status == 'PROCESSADO':
            raise ValidationError("Laudo já processado no GLPI: não é possível remover itens.")
        super().delete(*args, **kwargs)
```

Naively checking `self.status == 'PROCESSADO'` in `save()` would block the very save that *sets* the status to `PROCESSADO` in the first place (the admin action does `item.status = 'PROCESSADO'; item.save()`). The guard must compare against what's currently in the database, not the in-memory value being written.

- [ ] **Step 1: Write the failing model tests**

Create `apps/reports/tests.py`:

```python
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.reports.models import ItemLaudo, LaudoBaixa


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.reports -v 2`
Expected: `FAIL`/`ERROR` on `test_new_item_defaults_to_pendente` (and related) with something like `AttributeError: 'ItemLaudo' object has no attribute 'status'` — the field doesn't exist yet.

- [ ] **Step 3: Add the fields and fix the guard in `apps/reports/models.py`**

Replace the `class Meta` through `delete()` block of `ItemLaudo` (currently `apps/reports/models.py:206-223`):

```python
    STATUS_GLPI_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PROCESSADO', 'Processado no GLPI'),
        ('FALHA', 'Falha ao processar no GLPI'),
    ]

    status = models.CharField(
        "Status no GLPI", max_length=15, choices=STATUS_GLPI_CHOICES,
        default='PENDENTE', editable=False,
    )
    glpi_erro = models.TextField(
        "Último Erro (GLPI)", blank=True, editable=False,
        help_text="Mensagem de erro da última tentativa. Fica em branco quando o item é processado com sucesso.",
    )
    processado_em = models.DateTimeField(
        "Processado em", null=True, blank=True, editable=False,
    )
    processado_por = models.ForeignKey(
        User, verbose_name="Processado por", null=True, blank=True,
        editable=False, on_delete=models.SET_NULL, related_name='+',
    )

    class Meta:
        verbose_name = "Item do Laudo"
        verbose_name_plural = "Itens do Laudo"
        # Garante que um item do GLPI não seja adicionado duas vezes NO MESMO laudo
        unique_together = ('laudo', 'glpi_id', 'tipo_equipamento')

    def __str__(self):
        return self.nome_equipamento

    def save(self, *args, **kwargs):
        if self.pk:
            status_atual = ItemLaudo.objects.filter(pk=self.pk).values_list('status', flat=True).first()
            if status_atual == 'PROCESSADO':
                raise ValidationError("Item já processado no GLPI: não é possível editar.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status == 'PROCESSADO':
            raise ValidationError("Item já processado no GLPI: não é possível remover.")
        super().delete(*args, **kwargs)
```

`ItemLaudo.py` already imports `User` at the top (`from django.contrib.auth.models import User`) via the shared import in `apps/reports/models.py:2` — reuse it, no new import needed.

- [ ] **Step 4: Generate and inspect the migration**

Run: `python manage.py makemigrations reports`
Expected output: a new file `apps/reports/migrations/0008_itemlaudo_status_tracking.py` (Django may pick a different auto-generated name/suffix — rename the file to `0008_itemlaudo_status_tracking.py` if it doesn't match) listing four `AddField` operations on `itemlaudo`: `status`, `glpi_erro`, `processado_em`, `processado_por`. Open the generated file and confirm it depends on `('reports', '0007_laudobaixa_data_baixa_glpi_laudobaixa_status')` and does **not** touch any other model.

- [ ] **Step 5: Apply the migration**

Run: `python manage.py migrate reports`
Expected: `Applying reports.0008_itemlaudo_status_tracking... OK`

- [ ] **Step 6: Run tests to verify they pass**

Run: `python manage.py test apps.reports -v 2`
Expected: all 6 tests in `ItemLaudoStatusLockTests` `PASS`.

- [ ] **Step 7: Commit**

```bash
git add apps/reports/models.py apps/reports/tests.py
git commit -m "feat(reports): add per-item GLPI status tracking to ItemLaudo"
```

(Migration is not committed — `migrations/` is gitignored project-wide, matching every other app in this repo.)

---

### Task 2: Simplify `ItemLaudoInline` and show per-item status

**Files:**
- Modify: `apps/reports/admin.py:74-119` (`ItemLaudoInline` class)

**Interfaces:**
- Consumes: `ItemLaudo.status`, `ItemLaudo.get_status_display()`, `ItemLaudo.glpi_erro` (from Task 1)
- Produces: `ItemLaudoInline.status_com_erro` display method, used only within this class

Per the spec, the inline stops trying to enforce the lock itself (Django's `TabularInline.has_delete_permission`/`get_readonly_fields` only support locking the *whole* formset, not one row — the real lock is `ItemLaudo.save()`/`delete()` from Task 1, which raises a validation error the user will see if they try to edit/delete a processed row). The inline's job now is just to show, per item, whether it's been processed.

This class has no independent unit-test surface (it's rendering wiring, exercised end-to-end in Task 5's tests when the changelist/change page loads) — no test step here, but Task 5's admin tests will load the change page and this code path executes as part of that.

- [ ] **Step 1: Replace the inline's permission overrides with a status display column**

Replace `apps/reports/admin.py:74-119`:

```python
class ItemLaudoInline(admin.TabularInline):
    """
    Define a visualização de 'Itens' dentro do admin do 'Laudo'.
    """
    model = ItemLaudo

    # Campos que aparecem no inline
    fields = (
        'nome_equipamento',
        'tipo_equipamento',
        'marca_equipamento',
        'modelo_equipamento',
        'numero_patrimonio',
        'numero_serie',
        'motivo_baixa', # Este é o único campo editável!
        'status_com_erro',
    )

    # Campos que não podem ser editados pelo usuário no inline
    readonly_fields = (
        'nome_equipamento',
        'tipo_equipamento',
        'marca_equipamento',
        'modelo_equipamento',
        'numero_patrimonio',
        'numero_serie',
        'status_com_erro',
    )

    extra = 0 # Não mostrar formulários em branco por padrão
    can_delete = True # Permitir remover um item importado por engano

    def has_add_permission(self, request, obj):
        # Impede que o usuário adicione itens manualmente por este inline
        # Itens SÓ podem ser adicionados pela 'Admin Action'
        return False

    @admin.display(description="Status no GLPI")
    def status_com_erro(self, obj):
        if obj.status == 'FALHA' and obj.glpi_erro:
            return format_html(
                '<span style="color:#ba2121;" title="{}">⚠ Falha</span>',
                obj.glpi_erro,
            )
        return obj.get_status_display()
```

The trava real (o `ValidationError` de `ItemLaudo.save()`/`delete()`) continua valendo mesmo sem `has_delete_permission`/`get_readonly_fields` aqui — o usuário só vai ver um erro de validação do Django se tentar salvar/apagar uma linha travada, em vez de o checkbox desaparecer sozinho (limitação aceita no spec).

- [ ] **Step 2: Add the `format_html` import**

`glpi_erro` comes from an external system's (GLPI's) raw HTTP error response body — treat it as untrusted text. Add to the import block at the top of `apps/reports/admin.py` (currently `apps/reports/admin.py:4`, next to the existing `mark_safe` import):

```python
from django.utils.html import format_html
```

- [ ] **Step 3: Sanity-check with Django's system check**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 4: Commit**

```bash
git add apps/reports/admin.py
git commit -m "feat(reports): show per-item GLPI status in the ItemLaudo inline"
```

---

### Task 3: Confirmation page template

**Files:**
- Create: `apps/reports/templates/admin/reports/laudobaixa/confirma_baixa_glpi.html`

**Interfaces:**
- Consumes (context variables the template expects, all provided by Task 4's action): `laudo` (`LaudoBaixa`), `itens` (iterable of `ItemLaudo`), `status_alvo_id` (`int`), `action_checkbox_name` (`str`, value of `django.contrib.admin.helpers.ACTION_CHECKBOX_NAME`), `queryset` (the 1-item `LaudoBaixa` queryset), `opts` (`LaudoBaixa._meta`), plus whatever `admin_site.each_context(request)` adds (`site_header`, etc. — standard Django admin context).
- Produces: a form that POSTs back to the changelist with `action=atualizar_status_itens_no_glpi` and `confirma_baixa_glpi=yes`, re-triggering the same admin action (Django's standard action-confirmation re-dispatch, same mechanism `admin/delete_selected_confirmation.html` uses).

This is a template — no automated test in isolation; it's exercised by Task 5's `test_first_click_renders_confirmation_without_calling_glpi`.

- [ ] **Step 1: Create the directory and template**

```html
{% extends "admin/base_site.html" %}
{% load i18n l10n admin_urls %}

{% block content %}
<p>
    Você está prestes a aplicar o status ID <strong>{{ status_alvo_id }}</strong> no GLPI
    para os itens abaixo do laudo <strong>{{ laudo.numero_documento }}</strong>.
    Itens já processados com sucesso anteriormente não são reenviados.
</p>

<table>
    <thead>
        <tr>
            <th>Equipamento</th>
            <th>Tipo</th>
            <th>Patrimônio</th>
            <th>Status atual</th>
        </tr>
    </thead>
    <tbody>
        {% for item in itens %}
        <tr>
            <td>{{ item.nome_equipamento }}</td>
            <td>{{ item.tipo_equipamento }}</td>
            <td>{{ item.numero_patrimonio|default:"-" }}</td>
            <td>
                {{ item.get_status_display }}
                {% if item.status == 'FALHA' and item.glpi_erro %}
                    <br><small style="color:#ba2121;">{{ item.glpi_erro }}</small>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<form method="post">
    {% csrf_token %}
    {% for obj in queryset %}
        <input type="hidden" name="{{ action_checkbox_name }}" value="{{ obj.pk|unlocalize }}">
    {% endfor %}
    <input type="hidden" name="action" value="atualizar_status_itens_no_glpi">
    <input type="hidden" name="confirma_baixa_glpi" value="yes">
    <input type="submit" value="Confirmar baixa no GLPI">
    <a href="{% url opts|admin_urlname:'changelist' %}" class="button cancel-link">Cancelar</a>
</form>
{% endblock %}
```

`APP_DIRS=True` is already set in `core/settings.py` (`TEMPLATES[0]['APP_DIRS']`), so this file is picked up automatically — no `settings.py` change needed.

- [ ] **Step 2: Commit**

```bash
git add apps/reports/templates/admin/reports/laudobaixa/confirma_baixa_glpi.html
git commit -m "feat(reports): add GLPI baixa confirmation template"
```

---

### Task 4: Rewrite `atualizar_status_itens_no_glpi` with confirmation and selective retry

**Files:**
- Modify: `apps/reports/admin.py` — the `atualizar_status_itens_no_glpi` method (at the time this plan was written, lines 315-422; Task 2's edit shifts everything below it down by a few lines, so locate it by its `@admin.action(description='[GLPI] Atualizar status de todos os itens deste laudo no GLPI')` decorator rather than the literal line numbers) — and the import block at the top

**Interfaces:**
- Consumes: `ItemLaudo.status`/`glpi_erro`/`processado_em`/`processado_por` (Task 1), `ItemLaudoInline.status_com_erro` indirectly via the change page (Task 2), the template from Task 3, `update_glpi_asset_status(config, session_token, itemtype, item_id, status_id) -> (bool, str | None)` and `map_django_type_to_glpi(django_type) -> str` (both already in `apps/dbcom/utils.py`, already imported at `apps/reports/admin.py:52-57`).
- Produces: nothing new consumed elsewhere — this is the top-level entry point exercised by Task 5's tests via `self.client.post(...)`.

- [ ] **Step 1: Add the new imports**

At the top of `apps/reports/admin.py` (alongside the existing `django.contrib.admin`/`django.http`/`django.utils` imports around lines 1-7):

```python
from django.template.response import TemplateResponse
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
```

- [ ] **Step 2: Replace the action method**

Replace `apps/reports/admin.py:315-422` (from `@admin.action(description='[GLPI] Atualizar status de todos os itens deste laudo no GLPI')` through the closing `kill_legacy_session(config, session_token)` line) with:

```python
    @admin.action(description='[GLPI] Atualizar status dos itens pendentes/com falha no GLPI')
    def atualizar_status_itens_no_glpi(self, request, queryset):
        """
        Aplica o status de baixa (config.glpi_status_baixa_id) nos itens do
        laudo que ainda não foram processados com sucesso. Mostra uma tela
        de confirmação antes de escrever no GLPI e só reenvia itens
        PENDENTE/FALHA (não reprocessa itens já PROCESSADO).
        """
        if queryset.count() != 1:
            self.message_user(request, "Selecione apenas UM laudo para realizar esta ação.", messages.ERROR)
            return

        laudo = queryset.first()

        # 1. Validações de pré-condição do laudo
        if not laudo.destinacao:
            self.message_user(request, "Defina a destinação final do laudo antes de aplicar a baixa no GLPI.", messages.ERROR)
            return

        if not laudo.itens.exists():
            self.message_user(request, "Este laudo não possui itens para atualizar.", messages.WARNING)
            return

        itens_sem_motivo = laudo.itens.filter(motivo_baixa__isnull=True).count()
        if itens_sem_motivo > 0:
            self.message_user(request,
                f"{itens_sem_motivo} item(ns) deste laudo ainda não têm motivo de baixa preenchido. "
                f"Preencha todos os motivos antes de aplicar a baixa no GLPI.",
                messages.ERROR
            )
            return

        config = GLPIConfig.objects.first()
        if not config or not config.glpi_status_baixa_id:
            self.message_user(request, "A configuração do GLPI ou o ID do Status de Baixa não foram definidos.", messages.ERROR)
            return

        if not GLPI_SESSION_UTILS_DISPONIVEL:
            self.message_user(request, "Funções de integração com GLPI não estão disponíveis.", messages.ERROR)
            return

        # 2. Só os itens que ainda não foram processados com sucesso
        itens_a_processar = laudo.itens.exclude(status='PROCESSADO')
        if not itens_a_processar.exists():
            self.message_user(request,
                f"Todos os itens do laudo {laudo.numero_documento} já foram processados no GLPI.",
                messages.WARNING
            )
            return

        # 3. Sem confirmação ainda: mostra a tela intermediária
        if request.POST.get('confirma_baixa_glpi') != 'yes':
            context = {
                **self.admin_site.each_context(request),
                'title': 'Confirmar baixa no GLPI',
                'laudo': laudo,
                'itens': itens_a_processar,
                'status_alvo_id': config.glpi_status_baixa_id,
                'action_checkbox_name': ACTION_CHECKBOX_NAME,
                'queryset': queryset,
                'opts': self.model._meta,
            }
            return TemplateResponse(
                request,
                'admin/reports/laudobaixa/confirma_baixa_glpi.html',
                context,
            )

        # 4. Confirmado: processa cada item pendente/com falha
        session_token = None
        sucesso_count = 0
        erro_count = 0

        try:
            self.message_user(request, "Iniciando sessão na API do GLPI...", messages.INFO)
            session_token, error = get_legacy_session_token(config)
            if error:
                raise Exception(f"Falha ao iniciar sessão: {error}")

            for item in itens_a_processar:
                itemtype = map_django_type_to_glpi(item.tipo_equipamento)
                ok, error_msg = update_glpi_asset_status(
                    config,
                    session_token,
                    itemtype,
                    item.glpi_id,
                    config.glpi_status_baixa_id
                )

                if ok:
                    item.status = 'PROCESSADO'
                    item.processado_em = timezone.now()
                    item.processado_por = request.user
                    item.glpi_erro = ''
                    item.save(update_fields=['status', 'processado_em', 'processado_por', 'glpi_erro'])
                    sucesso_count += 1
                else:
                    item.status = 'FALHA'
                    item.glpi_erro = error_msg or ''
                    item.save(update_fields=['status', 'glpi_erro'])
                    erro_count += 1
                    print(f"Erro ao atualizar item {item.glpi_id} ({itemtype}): {error_msg}")

            # 5. Recomputa o agregado do laudo
            todos_processados = not laudo.itens.exclude(status='PROCESSADO').exists()
            if todos_processados and laudo.status != 'PROCESSADO':
                laudo.status = 'PROCESSADO'
                laudo.data_baixa_glpi = timezone.now()
                laudo.save(update_fields=['status', 'data_baixa_glpi'])

            if erro_count == 0:
                self.message_user(
                    request,
                    f"Sucesso! {sucesso_count} item(ns) do laudo {laudo.numero_documento} foram atualizados no GLPI para o status ID {config.glpi_status_baixa_id}.",
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    f"{sucesso_count} item(ns) atualizados e {erro_count} falha(s). "
                    f"Os itens com falha ficaram marcados como FALHA e podem ser reprocessados executando a ação novamente.",
                    messages.WARNING
                )

        except Exception as e:
            self.message_user(request, f"Erro crítico durante a integração: {e}", messages.ERROR)

        finally:
            if session_token:
                kill_legacy_session(config, session_token)
```

- [ ] **Step 3: Sanity-check with Django's system check**

Run: `python manage.py check`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 4: Commit**

```bash
git add apps/reports/admin.py
git commit -m "feat(reports): confirm-then-process flow with selective retry for GLPI baixa"
```

(Deliberately not run against the automated tests yet — Task 5 writes and runs them against this code together, since the tests are what actually validate this task's behavior.)

---

### Task 5: Tests for the confirm-then-process admin action flow

**Files:**
- Modify: `apps/reports/tests.py` (append a new `TestCase` class)

**Interfaces:**
- Consumes: everything from Tasks 1-4 — `ItemLaudo.status`/`glpi_erro`/`processado_em`/`processado_por`, the `atualizar_status_itens_no_glpi` action, `apps.reports.admin.get_legacy_session_token`/`update_glpi_asset_status`/`kill_legacy_session` (mocked at their point of use, i.e. patched as `apps.reports.admin.<name>` since that's where `atualizar_status_itens_no_glpi` looks them up — they're imported by name into that module).

- [ ] **Step 1: Write the failing tests**

`apps/reports/tests.py` currently (from Task 1) starts with:

```python
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.reports.models import ItemLaudo, LaudoBaixa


class ItemLaudoStatusLockTests(TestCase):
    ...
```

Change the import block at the top to add `Client` and the three new imports:

```python
from unittest.mock import patch

from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from apps.dbcom.models import GLPIConfig
from apps.reports.models import ItemLaudo, LaudoBaixa, MotivoBaixa
```

Then append this new class at the end of the file, below `ItemLaudoStatusLockTests` (leave `ItemLaudoStatusLockTests` itself untouched):

```python
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
```

Add `from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME` to the imports at the top of `apps/reports/tests.py`.

- [ ] **Step 2: Run tests to verify they fail (or pass, confirming coverage) appropriately**

Run: `python manage.py test apps.reports -v 2`
Expected: since Tasks 1-4 already implemented the behavior, these should mostly `PASS` immediately — this step is verifying that the tests actually exercise the real code path (not silently no-op). If any test fails, read the failure message and fix `apps/reports/admin.py` (from Task 4) or `apps/reports/models.py` (from Task 1) — do not weaken the test to make it pass.

- [ ] **Step 3: Run the full test suite once more to confirm a clean pass**

Run: `python manage.py test apps.reports -v 2`
Expected: `OK` — all tests across both `TestCase` classes pass, 0 failures, 0 errors.

- [ ] **Step 4: Commit**

```bash
git add apps/reports/tests.py
git commit -m "test(reports): cover confirm-then-process GLPI baixa flow"
```

---

### Task 6: Manual smoke test in the real admin UI

**Files:** none (verification only)

**Interfaces:** none

Automated tests mock the GLPI HTTP calls; they don't prove the confirmation template renders correctly with real Django admin CSS/layout, or that the two-step POST actually round-trips through a browser. Do this once against a real (dev) environment before considering the feature done.

- [ ] **Step 1: Start the dev server**

Run: `python manage.py runserver`

- [ ] **Step 2: Walk through the flow in a browser**

1. Log into `/admin/`, open a `LaudoBaixa` with at least 2 items, one with `motivo_baixa` set and destinação filled.
2. Select it in the changelist, choose the "[GLPI] Atualizar status dos itens pendentes/com falha no GLPI" action, click "Ir".
3. Confirm the confirmation page renders: shows the item(s) to be processed, the target status ID, a "Confirmar baixa no GLPI" button, and a "Cancelar" link back to the changelist.
4. Click "Cancelar" — confirm it returns to the changelist without changing anything (item status still `PENDENTE`).
5. Repeat steps 2-3, this time click "Confirmar baixa no GLPI" — expect either a GLPI API error message (if `GLPIConfig` points at a real/test GLPI instance and the call fails) or a success message; either way, reopen the laudo and confirm the item's status column in the inline reflects `PROCESSADO` or `FALHA` accordingly, with the error tooltip visible on hover if `FALHA`.
6. With at least one item `PROCESSADO`, try editing that item's `motivo_baixa` in the inline and saving — confirm Django shows a validation error instead of silently succeeding.

- [ ] **Step 3: Report results**

No commit for this task — it's a verification checklist. If any step fails, treat it as a bug against the corresponding earlier task and fix there.
