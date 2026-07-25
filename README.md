# HFLE Dashboard — Streamlit Cloud

## 1. Criar conta GitHub (se não tiver)
- Aceder a https://github.com e registar-se

## 2. Criar repositório
- Clicar no `+` (canto superior direito) → "New repository"
- Nome: `hfle-dashboard` (ou outro)
- Público
- NÃO iniciar com README (vamos usar os ficheiros locais)

## 3. Enviar ficheiros para o GitHub
```powershell
cd cloud_deploy
git init
git add .
git commit -m "primeiro deploy"
git remote add origin https://github.com/SEU_USUARIO/hfle-dashboard.git
git branch -M main
git push -u origin main
```

## 4. Deploy no Streamlit Cloud
- Ir a https://share.streamlit.io
- Login com conta GitHub
- Clicar "New app" → escolher o repositório `hfle-dashboard`
- Branch: `main`, Main file: `dashboard.py`
- Clicar "Deploy"

## 5. Após cada execução local do HFLE
Para atualizar o dashboard com dados novos:
```powershell
.\cloud_deploy\commit_csvs.ps1
```
(O script copia os CSVs, faz git add/commit/push, e o Streamlit Cloud atualiza automaticamente)

## Opcional: Telegram a partir do Cloud
Editar `cloud_deploy/.streamlit/secrets.toml` com o token real (APENAS se quiser testar Telegram do dashboard online). Depois fazer commit e push.
