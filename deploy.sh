#!/bin/bash

# ==============================================================================
# Script de déploiement pour EvilGPT
# ==============================================================================

# 1. Chargement des variables du fichier .env
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "❌ Erreur : Fichier .env manquant."
    exit 1
fi

# 2. Vérification de la configuration
if [ "$DEPLOY_REMOTE_HOST" == "votre_ip_ou_domaine" ] || [ -z "$DEPLOY_REMOTE_HOST" ]; then
    echo "❌ Erreur : Vous devez configurer votre adresse IP ou domaine dans le fichier .env"
    echo "Variables attendues : DEPLOY_REMOTE_USER, DEPLOY_REMOTE_HOST, DEPLOY_REMOTE_DIR, DEPLOY_SERVICE_NAME"
    exit 1
fi

REMOTE_USER="${DEPLOY_REMOTE_USER:-user}"
REMOTE_HOST="${DEPLOY_REMOTE_HOST}"
REMOTE_DIR="${DEPLOY_REMOTE_DIR:-/.evil}"
SERVICE_NAME="${DEPLOY_SERVICE_NAME:-evilgpt.service}"

# 3. Demander le mot de passe s'il n'est pas fourni
if [ -z "$SSHPASS" ]; then
    read -sp "Entrez le mot de passe SSH pour ${REMOTE_USER}@${REMOTE_HOST}: " SSH_PASSWORD
    echo ""
    export SSHPASS="$SSH_PASSWORD"
fi

# 4. Vérification de sshpass
if ! command -v sshpass >/dev/null 2>&1; then
    echo "⚠️  Attention : sshpass n'est pas installé. Tentative en mode interactif."
fi

# Fonctions utilitaires
run_ssh() {
    if command -v sshpass >/dev/null 2>&1; then
        sshpass -e ssh -o StrictHostKeyChecking=no "$@"
    else
        ssh "$@"
    fi
}

run_rsync() {
    if command -v sshpass >/dev/null 2>&1; then
        sshpass -e rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" "$@"
    else
        rsync -avz --delete "$@"
    fi
}

echo "------------------------------------------------------------"
echo "🚀 Déploiement sur ${REMOTE_HOST}"
echo "------------------------------------------------------------"

# 1. Préparation du dossier distant
echo "📂 Préparation du dossier distant..."
run_ssh "${REMOTE_USER}@${REMOTE_HOST}" "echo '$SSHPASS' | sudo -S mkdir -p ${REMOTE_DIR} && echo '$SSHPASS' | sudo -S chown ${REMOTE_USER}:${REMOTE_USER} ${REMOTE_DIR}"

# 2. Transfert
echo "📤 Transfert des fichiers..."
run_rsync \
    --exclude '.git/' \
    --exclude '.venv/' \
    --exclude '__pycache__/' \
    --exclude '.ruff_cache/' \
    --exclude 'data/' \
    ./ "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"

# 3. Maintenance sur le serveur
echo "⚙️  Maintenance sur le serveur..."
run_ssh "${REMOTE_USER}@${REMOTE_HOST}" "SSHPASS='$SSHPASS' REMOTE_DIR='$REMOTE_DIR' SERVICE_NAME='$SERVICE_NAME' bash -s" << 'REMOTE_COMMANDS'
    set -e
    cd "${REMOTE_DIR}"
    
    if [ ! -d ".venv" ]; then 
        python3 -m venv .venv
    fi
    
    echo "🚀 Installation des dépendances avec uv..."
    ./.venv/bin/python -m pip install --quiet --upgrade uv
    ./.venv/bin/python -m uv pip install -r requirements.txt
    
    if [ -f "$SERVICE_NAME" ]; then
        echo "📜 Mise à jour du service systemd..."
        echo "$SSHPASS" | sudo -S cp "$SERVICE_NAME" /etc/systemd/system/
        echo "$SSHPASS" | sudo -S systemctl daemon-reload
        echo "$SSHPASS" | sudo -S systemctl enable "$SERVICE_NAME"
    fi
    
    echo "🔄 Redémarrage du service..."
    echo "$SSHPASS" | sudo -S systemctl restart "$SERVICE_NAME"
    
    echo "------------------------------------------------------------"
    echo "✅ Déploiement terminé !"
    echo "------------------------------------------------------------"
REMOTE_COMMANDS
