import base64, hashlib, hmac, json, time, secrets
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from apps.glpiintegrator.models import GlpiProfile


SECRET_KEY = settings.SECRET_KEY
TIMESTAMP_TOLERANCE = 300  # 5 minutes

def glpi_sso(request):
    payload_b64 = request.GET.get('payload')
    signature = request.GET.get('sig')
    
    if not payload_b64 or not signature:
        return HttpResponseForbidden("Missing payload or signature")
    
    # 1. Validate signature
    expected_signature = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return HttpResponseForbidden("Invalid signature")
    
    # 2. Decode payload
    try:
        payload_json = base64.b64decode(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)
    except (ValueError, TypeError, json.JSONDecodeError):
        return HttpResponseForbidden("Invalid payload format")
    
    # 3. Validate timestamp
    if abs(time.time() - payload.get('ts', 0)) > TIMESTAMP_TOLERANCE:
        return HttpResponseForbidden("Request timestamp is out of tolerance.")
    
    # 4. Extract data from payload
    glpi_user_id = payload.get('uid')
    email = payload.get('email')
    first_name = payload.get('name', '')
    
    if not glpi_user_id or not email:
        return HttpResponseForbidden("Missing user ID or email in payload.")
    
    # 5. Find or create user and link GLPI Profile
    # Identidade é sempre resolvida por glpi_id (via GlpiProfile), nunca por
    # e-mail: User.email não é unique no Django, então buscar/criar por e-mail
    # logaria na conta local de quem quer que já tenha esse e-mail cadastrado,
    # sem checar senha nem posse dele.
    try:
        glpi_profile = GlpiProfile.objects.select_related('user').get(glpi_id=glpi_user_id)
        user = glpi_profile.user
    except GlpiProfile.DoesNotExist:
        if User.objects.filter(email=email).exists():
            # E-mail já pertence a uma conta local não vinculada a este GLPI
            # ID: falha fechado em vez de logar em conta alheia.
            return HttpResponseForbidden(
                "E-mail já associado a uma conta existente não vinculada a este usuário do GLPI."
            )

        user = User.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            is_staff=True,
        )
        # Em Django 5.x, make_random_password foi removido.
        # Usamos secrets para gerar uma senha segura e aleatória.
        user.set_password(secrets.token_urlsafe(32))
        user.save()

        GlpiProfile.objects.create(user=user, glpi_id=glpi_user_id)

    # 6. Log the user in and redirect
    if user is not None and user.is_active:
        login(request, user)
        next_url = request.GET.get('next')
        # 'next' não faz parte do payload assinado por HMAC, então qualquer um
        # com um link de SSO válido poderia usá-lo pra redirecionar a vítima
        # após o login real; validar contra o host atual antes de seguir.
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(next_url)
        return redirect(reverse('admin:index'))

    return HttpResponseForbidden("User account is inactive or could not be authenticated.")
