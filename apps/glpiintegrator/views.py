import base64, hashlib, hmac, json, time
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.db import transaction
from apps.glpiintegrator.models import GlpiProfile


SECRET_KEY = settings.SECRET_KEY
TIMESTAMP_TOLERANCE = 300  # 5 minutes

def glpi_sso(request):
    payload_b64 = request.GET.get('payload')
    signature = request.GET.get('sig')
    
    if not payload_b64 or not signature:
        return HttpResponseForbidden("Missing payload or signature")
    
    # 1. Validate signature
    expected_signature = hmac.new(SECRET_KEY, payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
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
    first_name = payload.get('first_name', '')
    last_name = payload.get('last_name', '')
    
    if not glpi_user_id or not email:
        return HttpResponseForbidden("Missing user ID or email in payload.")
    
    # 5. Find or create user
    try:
        glpi_profile = GlpiProfile.objects.select_related('user').get(glpi_id=glpi_user_id)
        user = glpi_profile.user
    except GlpiProfile.DoesNotExist:
        if User.objects.filter(email=email).exists():
            return HttpResponseForbidden(f"A user with email {email} already exists but is not linked to a GLPI account.")
        
        new_user = User.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        new_user.set_password(User.objects.make_random_password(length=24))
        new_user.save()
        
        GlpiProfile.objects.create(user=new_user, glpi_id=glpi_user_id)
        user = new_user
        
    # 6. Log the user in and redirect
    if user is not None and user.is_active:
        login(request, user)
        next_url = request.GET.get('next', '/')
        return redirect(next_url)
    
    return HttpResponseForbidden("User account is inactive or could not be authenticated.")
