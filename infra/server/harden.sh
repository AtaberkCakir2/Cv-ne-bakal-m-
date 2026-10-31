#!/usr/bin/env bash
# Yeni Ubuntu 24.04 sunucusunu sertleştirir (T-009). Kurulum adımları: infra/server/README.md
#
# Sunucuda root olarak, SSH anahtarıyla bağlanmışken çalıştırılır:
#   bash harden.sh
# Tekrar çalıştırmak güvenlidir. Root girişi kapanacağı için bitince KAPATMADAN ikinci bir terminalden deploy
# kullanıcısıyla bağlanmayı deneyin.
set -euo pipefail

DEPLOY_USER="${DEPLOY_USER:-deploy}"
SWAP_SIZE="${SWAP_SIZE:-4G}"
TIMEZONE="Europe/Istanbul"

log() { printf '\n==> %s\n' "$*"; }

[[ "$(id -u)" -eq 0 ]] || { echo "root olarak çalıştırın" >&2; exit 1; }
# shellcheck disable=SC1091
. /etc/os-release
[[ "${VERSION_ID:-}" == "24.04" ]] || { echo "Ubuntu 24.04 bekleniyordu: ${PRETTY_NAME:-bilinmiyor}" >&2; exit 1; }

# Anahtar yoksa parola girişi kapanınca sunucuya kimse giremez: hiçbir şeye dokunmadan dur.
grep -qE '^(ssh-|ecdsa-|sk-)' /root/.ssh/authorized_keys 2>/dev/null \
  || { echo "/root/.ssh/authorized_keys içinde SSH anahtarı yok, durduruldu" >&2; exit 1; }

export DEBIAN_FRONTEND=noninteractive

log "Paketler"
apt-get update -q
apt-get upgrade -yq
apt-get install -yq ufw fail2ban unattended-upgrades ca-certificates curl git

log "Saat dilimi: $TIMEZONE"
timedatectl set-timezone "$TIMEZONE"

log "Kullanıcı: $DEPLOY_USER"
id "$DEPLOY_USER" >/dev/null 2>&1 || adduser --disabled-password --gecos "" "$DEPLOY_USER"
usermod -aG sudo "$DEPLOY_USER"
# Parolası olmayan kullanıcı sudo kullanabilsin diye; giriş sadece anahtarla.
printf '%s ALL=(ALL) NOPASSWD:ALL\n' "$DEPLOY_USER" > "/etc/sudoers.d/90-$DEPLOY_USER"
chmod 440 "/etc/sudoers.d/90-$DEPLOY_USER"
visudo -cq
install -d -m 700 -o "$DEPLOY_USER" -g "$DEPLOY_USER" "/home/$DEPLOY_USER/.ssh"
install -m 600 -o "$DEPLOY_USER" -g "$DEPLOY_USER" /root/.ssh/authorized_keys \
  "/home/$DEPLOY_USER/.ssh/authorized_keys"

log "SSH: sadece anahtar, root kapalı"
# 00- öneki şart: sshd ilk gördüğü değeri alır, cloud-init'in 50- dosyası parola girişini açabiliyor.
cat > /etc/ssh/sshd_config.d/00-careerai.conf <<EOF
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
AllowUsers $DEPLOY_USER
EOF
sshd -t
systemctl reload ssh

log "Güvenlik duvarı: 22, 80, 443"
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp  # HTTP/3
ufw --force enable

log "fail2ban"
cat > /etc/fail2ban/jail.d/sshd.local <<'EOF'
[sshd]
enabled = true
backend = systemd
maxretry = 5
findtime = 10m
bantime = 1h
EOF
systemctl enable --now fail2ban
systemctl restart fail2ban

log "Otomatik güvenlik güncellemeleri"
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF
systemctl enable --now unattended-upgrades

log "Swap: $SWAP_SIZE"
if ! swapon --show=NAME --noheadings | grep -q '^/swapfile$'; then
  [[ -f /swapfile ]] || fallocate -l "$SWAP_SIZE" /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
fi
grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
echo 'vm.swappiness=10' > /etc/sysctl.d/90-careerai.conf
sysctl -q --system

log "Docker"
if ! command -v docker >/dev/null; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc]" \
    "https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
  apt-get update -q
  apt-get install -yq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi
# Log dosyaları diski doldurmasın.
cat > /etc/docker/daemon.json <<'EOF'
{ "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }
EOF
systemctl enable docker
systemctl restart docker
usermod -aG docker "$DEPLOY_USER"

log "Bitti. Bu pencereyi KAPATMADAN ikinci terminalden deneyin: ssh $DEPLOY_USER@<sunucu-ip>"
