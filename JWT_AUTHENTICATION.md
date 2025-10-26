# Autenticação JWT - DirectLabelPrinter

## Visão Geral

Este projeto agora utiliza autenticação JWT (JSON Web Token) para proteger todas as APIs da aplicação printer. Todas as views da API requerem autenticação.

## Endpoints de Autenticação

### 1. Obter Token de Acesso
**POST** `/api/auth/token/`

**Corpo da requisição:**
```json
{
    "username": "seu_usuario",
    "password": "sua_senha"
}
```

**Resposta:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 2. Renovar Token de Acesso
**POST** `/api/auth/token/refresh/`

**Corpo da requisição:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Resposta:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 3. Verificar Token
**POST** `/api/auth/token/verify/`

**Corpo da requisição:**
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Como Usar nas Requisições

Todas as requisições para as APIs protegidas devem incluir o header de autorização:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## APIs Protegidas

Todas as seguintes APIs agora requerem autenticação JWT:

- `GET /api/impressoras/` - Listar impressoras
- `POST /api/impressoras/{id}/selecionar-padrao/` - Selecionar impressora padrão
- `GET /api/layouts/` - Listar layouts
- `GET /api/layouts/{id}/` - Detalhes do layout
- `PUT /api/layouts/{id}/` - Atualizar layout
- `PATCH /api/layouts/{id}/` - Atualizar layout parcialmente
- `POST /api/layouts/{id}/selecionar-padrao/` - Selecionar layout padrão
- `POST /api/imprimir/` - Imprimir etiquetas

## Configurações JWT

- **Tempo de vida do Access Token:** 60 minutos
- **Tempo de vida do Refresh Token:** 7 dias
- **Rotação de Refresh Tokens:** Habilitada
- **Algoritmo:** HS256

## Exemplo de Uso com cURL

### 1. Obter token:
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

### 2. Usar token para acessar API:
```bash
curl -X GET http://localhost:8000/api/impressoras/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

## Exemplo de Uso com Python (requests)

```python
import requests

# 1. Obter token
response = requests.post('http://localhost:8000/api/auth/token/', json={
    'username': 'admin',
    'password': 'admin'
})
tokens = response.json()
access_token = tokens['access']

# 2. Usar token para acessar API
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get('http://localhost:8000/api/impressoras/', headers=headers)
print(response.json())
```

## Notas Importantes

1. **Criação de Usuários:** Use o Django Admin (`/admin/`) para criar usuários
2. **Segurança:** Mantenha os tokens seguros e não os compartilhe
3. **Renovação:** Use o refresh token para obter novos access tokens
4. **Expiração:** Access tokens expiram em 60 minutos por padrão
