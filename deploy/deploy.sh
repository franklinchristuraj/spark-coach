#!/usr/bin/env bash
set -euo pipefail

# Must run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be run as root. Use: sudo bash deploy.sh" >&2
    exit 1
fi

REPO_URL="https://github.com/your-org/spark-coach.git"
INSTALL_DIR="/opt/spark-coach"
DOMAIN="coach-api.ziksaka.com"
CERTBOT_EMAIL="admin@ziksaka.com"
NGINX_CONF="/etc/nginx/sites-available/${DOMAIN}"
NGINX_LINK="/etc/nginx/sites-enabled/${DOMAIN}"

echo "==> Step 1: Install Docker, Docker Compose, Nginx, Certbot"

if ! command -v docker &>/dev/null; then
    echo "    Installing Docker..."
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
        | tee /etc/apt/sources.list.d/docker.list >/dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable --now docker
    echo "    Docker installed."
else
    echo "    Docker already installed — skipping."
fi

if ! command -v nginx &>/dev/null; then
    echo "    Installing Nginx..."
    apt-get update -y
    apt-get install -y nginx
    systemctl enable --now nginx
    echo "    Nginx installed."
else
    echo "    Nginx already installed — skipping."
fi

if ! command -v certbot &>/dev/null; then
    echo "    Installing Certbot..."
    apt-get update -y
    apt-get install -y certbot python3-certbot-nginx
    echo "    Certbot installed."
else
    echo "    Certbot already installed — skipping."
fi

echo "==> Step 2: Clone repo to ${INSTALL_DIR}"

if [ -d "${INSTALL_DIR}/.git" ]; then
    echo "    Repo already cloned at ${INSTALL_DIR} — skipping."
else
    echo "    Cloning ${REPO_URL} → ${INSTALL_DIR}..."
    git clone "${REPO_URL}" "${INSTALL_DIR}"
    echo "    Repo cloned."
fi

echo "==> Step 3: Ensure .env file exists"

if [ ! -f "${INSTALL_DIR}/.env" ]; then
    echo ""
    echo "    *** ACTION REQUIRED ***"
    echo "    No .env file found at ${INSTALL_DIR}/.env"
    echo "    Copy your .env file to the server before continuing:"
    echo ""
    echo "        scp .env user@your-vps:${INSTALL_DIR}/.env"
    echo ""
    read -r -p "    Press ENTER once .env is in place, or Ctrl-C to abort..."
    if [ ! -f "${INSTALL_DIR}/.env" ]; then
        echo "    ERROR: .env still missing. Aborting."
        exit 1
    fi
    echo "    .env file confirmed."
else
    echo "    .env already exists — skipping prompt."
fi

echo "==> Step 4: Start API with Docker Compose (port 8080)"

cd "${INSTALL_DIR}"
docker compose up -d
echo "    API containers started."

echo "==> Step 5: Install Nginx server block for ${DOMAIN}"

cp "${INSTALL_DIR}/deploy/nginx-api.conf" "${NGINX_CONF}"
echo "    Copied nginx-api.conf to ${NGINX_CONF}."

echo "==> Step 6: Enable site and reload Nginx"

if [ ! -L "${NGINX_LINK}" ]; then
    ln -s "${NGINX_CONF}" "${NGINX_LINK}"
    echo "    Symlink created: ${NGINX_LINK}"
else
    echo "    Symlink already exists — skipping."
fi

nginx -t
systemctl reload nginx
echo "    Nginx reloaded."

echo "==> Step 7: Obtain SSL certificate via Certbot"

CERT_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"

if [ -f "${CERT_PATH}" ]; then
    echo "    Certificate already exists at ${CERT_PATH} — skipping certbot."
else
    echo "    Running certbot --nginx for ${DOMAIN}..."
    certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos \
        --email "${CERTBOT_EMAIL}" --redirect
    echo "    SSL certificate obtained and Nginx updated."
fi

echo "==> Step 8: Verify deployment"

echo "    Waiting 3 seconds for services to settle..."
sleep 3

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}/health" || true)

if [ "${HTTP_STATUS}" = "200" ]; then
    echo "    Health check passed (HTTP ${HTTP_STATUS})."
else
    echo "    WARNING: Health check returned HTTP ${HTTP_STATUS}."
    echo "    Check logs with: docker compose -f ${INSTALL_DIR}/docker-compose.yml logs"
fi

echo ""
echo "==> Deployment complete!"
echo "    API is live at: https://${DOMAIN}"
