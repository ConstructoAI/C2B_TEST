#!/bin/bash

# Script pour Mac/Linux
clear
echo -e "\033[36m============================================================\033[0m"
echo -e "\033[36m   GESTIONNAIRE DE SOUMISSIONS C2B CONSTRUCTION\033[0m"
echo -e "\033[36m============================================================\033[0m"
echo ""
echo -e "\033[32m[+] VERSION PRODUCTION COMPLETE\033[0m"
echo ""
echo -e "\033[33mFonctionnalites disponibles :\033[0m"
echo "  - Dashboard unifie (Heritage + Uploads)"
echo "  - Creation de soumissions Heritage"
echo "  - Upload multi-format (PDF, Word, Excel, Images)"
echo "  - Modification et suppression"
echo "  - Liens clients avec approbation"
echo ""
echo -e "\033[36m============================================================\033[0m"
echo ""

# Verifier Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo -e "\033[31m[ERREUR] Python n'est pas installe\033[0m"
    echo "Installez Python depuis : https://www.python.org"
    exit 1
fi

echo -e "\033[32m[1/3] Python detecte : $($PYTHON_CMD --version)\033[0m"
echo ""

echo -e "\033[33m[2/3] Installation des dependances...\033[0m"
$PYTHON_CMD -m pip install -r requirements.txt --quiet

echo ""
echo -e "\033[33m[3/3] Creation des dossiers...\033[0m"
mkdir -p data files

echo ""
echo -e "\033[36m============================================================\033[0m"
echo -e "\033[32m   APPLICATION PRETE !\033[0m"
echo -e "\033[36m============================================================\033[0m"
echo ""
echo -e "URL LOCAL : \033[33mhttp://localhost:8501\033[0m"
echo ""
echo -e "\033[36mACCES ADMIN :\033[0m"
echo "  - Mot de passe : admin2025"
echo ""
echo -e "\033[36mRACCOURCIS :\033[0m"
echo "  - Ctrl+C pour arreter"
echo "  - F5 pour rafraichir"
echo ""
echo -e "\033[36m============================================================\033[0m"
echo ""
echo -e "\033[32mLancement...\033[0m"
echo ""

# Lancer Streamlit
$PYTHON_CMD -m streamlit run app.py --server.port=8501 --server.address=localhost

echo ""
echo -e "\033[33mApplication fermee\033[0m"