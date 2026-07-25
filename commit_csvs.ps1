# Sincroniza CSVs para o GitHub (executar DEPOIS de python main.py)
$origem  = "C:\Users\garciac\OneDrive\Meus Documentos\Forex\iForex\Projetos\HLFE\Desenvolvimento\Versão atual"
$destino = Join-Path $origem "cloud_deploy"

Write-Host "Copiando OUTPUT_M*.csv ..." -ForegroundColor Cyan
Copy-Item -Path (Join-Path $origem "OUTPUT_M*.csv") -Destination $destino -Force

Write-Host "Copiando CROSS_TF_*.csv ..." -ForegroundColor Cyan
Copy-Item -Path (Join-Path $origem "CROSS_TF_*.csv") -Destination $destino -Force

Write-Host "Copiando telegram_prefs.json ..." -ForegroundColor Cyan
Copy-Item -Path (Join-Path $origem "telegram_prefs.json") -Destination $destino -Force

Set-Location -LiteralPath $destino

Write-Host "A adicionar ao git..." -ForegroundColor Cyan
git add *.csv dashboard.py notifier.py hma.py config.py telegram_prefs.json

$data = Get-Date -Format "yyyy-MM-dd HH:mm"
git commit -m "atualizacao $data"

Write-Host "Enviando para GitHub..." -ForegroundColor Cyan
git push

Write-Host "Concluido! O Streamlit Cloud vai atualizar automaticamente." -ForegroundColor Green
