#!/bin/bash
# setup-web.sh — Deploy PM Pipeline web dashboard on the VPS.
# Run as root: bash /home/lenar/pipeline/tools/scripts/setup-web.sh

set -e

USERS=(lenar slava olya zhanna sergey)
PORTS=(7681 7682 7683 7684 7685)
SCRIPT_DIR="/home/lenar/pipeline/tools/scripts"
WEB_DIR="/home/lenar/pipeline/tools/web"
LOG_DIR="/home/lenar/pipeline/logs"

echo "==> Installing Flask..."
pip3 install flask

echo "==> Creating log directory..."
mkdir -p "$LOG_DIR"

# ---------------------------------------------------------------------------
# 1. systemd service for Flask dashboard
# ---------------------------------------------------------------------------
echo "==> Writing pm-web.service..."
cat > /etc/systemd/system/pm-web.service << 'EOF'
[Unit]
Description=PM Pipeline Web Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/lenar/pipeline/tools/web
ExecStart=/usr/bin/python3 /home/lenar/pipeline/tools/web/app.py
Restart=on-failure
RestartSec=5
StandardOutput=append:/home/lenar/pipeline/logs/web.log
StandardError=append:/home/lenar/pipeline/logs/web.log

[Install]
WantedBy=multi-user.target
EOF

# ---------------------------------------------------------------------------
# 2. nginx config
# ---------------------------------------------------------------------------
echo "==> Writing nginx config..."
cat > /etc/nginx/sites-enabled/default << 'NGINXEOF'
map $http_upgrade $connection_upgrade {
    default upgrade;
    ""      close;
}

server {
    listen 80;
    server_name _;

    # ---- lenar ----
    location /lenar/terminal/ {
        auth_basic "PM Pipeline";
        auth_basic_user_file /etc/nginx/htpasswd-lenar;
        proxy_pass http://localhost:7681/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
    location /lenar/ {
        auth_basic "PM Pipeline";
        auth_basic_user_file /etc/nginx/htpasswd-lenar;
        proxy_pass http://localhost:5000/lenar/;
        proxy_set_header X-PM-User lenar;
        proxy_set_header Host $host;
    }

    # ---- slava ----
    location /slava/terminal/ {
        auth_basic "PM Pipeline";
        auth_basic_user_file /etc/nginx/htpasswd-slava;
        proxy_pass http://localhost:7682/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
    location /slava/ {
        auth_basic "PM Pipeline";
        auth_basic_user_file /etc/nginx/htpasswd-slava;
        proxy_pass http://localhost:5000/slava/;
        proxy_set_header X-PM-User slava;
        proxy_set_header Host $host;
    }

    # ---- olya ----
    location /olya/terminal/ {
        auth_basic "PM Pipeline";
        auth_basic_user_file /etc/nginx/htpasswd-olya;
        proxy_pass http://localhost:7683/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
    location /olya/ {
        auth_basic "PM Pipeline";
        auth_basic_user_file /etc/nginx/htpasswd-olya;
        proxy_pass http://localhost:5000/olya/;
        proxy_set_header X-PM-User olya;
        proxy_set_header Host $host;
    }

    # ---- zhanna ----
    location /zhanna/terminal/ {
        auth_basic "PM Pipeline";
        auth_basic_user_file /etc/nginx/htpasswd-zhanna;
        proxy_pass http://localhost:7684/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
    location /zhanna/ {
        auth_basic "PM Pipeline";
        auth_basic_user_file /etc/nginx/htpasswd-zhanna;
        proxy_pass http://localhost:5000/zhanna/;
        proxy_set_header X-PM-User zhanna;
        proxy_set_header Host $host;
    }

    # ---- sergey ----
    location /sergey/terminal/ {
        auth_basic "PM Pipeline";
        auth_basic_user_file /etc/nginx/htpasswd-sergey;
        proxy_pass http://localhost:7685/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
    location /sergey/ {
        auth_basic "PM Pipeline";
        auth_basic_user_file /etc/nginx/htpasswd-sergey;
        proxy_pass http://localhost:5000/sergey/;
        proxy_set_header X-PM-User sergey;
        proxy_set_header Host $host;
    }
}
NGINXEOF

# ---------------------------------------------------------------------------
# 3. ttyd systemd services — one per user, using session-start.sh
# ---------------------------------------------------------------------------
echo "==> Writing ttyd services and making session-start.sh executable..."

for i in "${!USERS[@]}"; do
    USER="${USERS[$i]}"
    PORT="${PORTS[$i]}"
    SESSION_SCRIPT="/home/${USER}/pipeline/tools/scripts/session-start.sh"

    # Ensure the script exists for this user (copy from lenar's if needed)
    if [ ! -f "$SESSION_SCRIPT" ]; then
        mkdir -p "/home/${USER}/pipeline/tools/scripts"
        cp "${SCRIPT_DIR}/session-start.sh" "$SESSION_SCRIPT"
        chown "${USER}:${USER}" "$SESSION_SCRIPT"
    fi

    chmod +x "$SESSION_SCRIPT"

    cat > "/etc/systemd/system/ttyd-${USER}.service" << EOF
[Unit]
Description=ttyd terminal for ${USER}
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/ttyd --writable --port ${PORT} su -l ${USER} -c /home/${USER}/pipeline/tools/scripts/session-start.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    echo "  wrote ttyd-${USER}.service (port ${PORT})"
done

# ---------------------------------------------------------------------------
# 4. Reload systemd, enable & start everything
# ---------------------------------------------------------------------------
echo "==> Reloading systemd..."
systemctl daemon-reload

echo "==> Enabling and starting pm-web..."
systemctl enable --now pm-web

echo "==> Restarting ttyd services..."
for USER in "${USERS[@]}"; do
    systemctl enable "ttyd-${USER}"
    systemctl restart "ttyd-${USER}"
done

echo "==> Testing and reloading nginx..."
nginx -t && systemctl reload nginx

# ---------------------------------------------------------------------------
# 5. Done
# ---------------------------------------------------------------------------
echo ""
echo "======================================================"
echo " PM Pipeline dashboard deployed successfully!"
echo "======================================================"
echo ""
echo " User dashboards:"
for USER in "${USERS[@]}"; do
    echo "   http://<server>/${USER}/"
done
echo ""
echo " Terminals:"
for USER in "${USERS[@]}"; do
    echo "   http://<server>/${USER}/terminal/"
done
echo ""
echo " Flask log: ${LOG_DIR}/web.log"
echo " Check status: systemctl status pm-web"
echo "======================================================"
