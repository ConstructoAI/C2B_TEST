# Script PowerShell pour lancer l'application
Clear-Host
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   GESTIONNAIRE DE SOUMISSIONS C2B CONSTRUCTION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[+] VERSION PRODUCTION COMPLETE" -ForegroundColor Green
Write-Host ""
Write-Host "Fonctionnalites disponibles :" -ForegroundColor Yellow
Write-Host "  - Dashboard unifie (Heritage + Uploads)"
Write-Host "  - Creation de soumissions Heritage"
Write-Host "  - Upload multi-format (PDF, Word, Excel, Images)"
Write-Host "  - Modification et suppression"
Write-Host "  - Liens clients avec approbation"
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verifier Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[1/3] Python detecte : $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERREUR] Python n'est pas installe" -ForegroundColor Red
    Write-Host "Installez Python depuis : https://www.python.org" -ForegroundColor Yellow
    Read-Host "Appuyez sur Entree pour fermer"
    exit
}

Write-Host ""
Write-Host "[2/3] Installation des dependances..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

Write-Host ""
Write-Host "[3/3] Creation des dossiers..." -ForegroundColor Yellow
if (-not (Test-Path "data")) { New-Item -ItemType Directory -Path "data" | Out-Null }
if (-not (Test-Path "files")) { New-Item -ItemType Directory -Path "files" | Out-Null }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   APPLICATION PRETE !" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URL LOCAL : " -NoNewline
Write-Host "http://localhost:8501" -ForegroundColor Yellow
Write-Host ""
Write-Host "ACCES ADMIN :" -ForegroundColor Cyan
Write-Host "  - Mot de passe : admin2025"
Write-Host ""
Write-Host "RACCOURCIS :" -ForegroundColor Cyan
Write-Host "  - Ctrl+C pour arreter"
Write-Host "  - F5 pour rafraichir"
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Lancement..." -ForegroundColor Green
Write-Host ""

# Lancer Streamlit
streamlit run app.py --server.port=8501 --server.address=localhost

Write-Host ""
Write-Host "Application fermee" -ForegroundColor Yellow
Read-Host "Appuyez sur Entree pour fermer"