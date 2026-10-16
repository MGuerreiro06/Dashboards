# Dashboard E-commerce (Dash)

Aplicação Dash para visualizar a análise estatística do e-commerce.

## Rodar localmente

```bash
pip install -r requirements.txt
python app.py
```

Acesse http://127.0.0.1:8050

## Publicar (Render)

1. Suba esta pasta para um repositório no GitHub.
2. No Render: **New → Web Service** e conecte o repositório.
3. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:server`
4. Após o deploy, o Render gera o link público da aplicação.
