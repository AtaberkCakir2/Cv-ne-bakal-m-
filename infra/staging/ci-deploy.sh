#!/usr/bin/env bash
# CI anahtarının sunucuda çalıştırabildiği tek komut (T-036). deploy kullanıcısının authorized_keys satırı:
#   restrict,command="bash /home/deploy/careerai/infra/staging/ci-deploy.sh" ssh-ed25519 AAAA... careerai-ci
# CI şöyle çağırır (GHCR token'ı stdin'den gelir, sunucuda kalmaz):
#   printf '%s' "$TOKEN" | ssh deploy@<sunucu> "deploy <commit-sha> <github-kullanıcısı>"
# Anahtar sızsa bile sadece main'deki bir commit deploy edilebilir; kabuk, sudo veya port yönlendirme açılmaz.
set -euo pipefail

# Gövde fonksiyonda: git checkout bu dosyayı değiştirse de bash çalışan sürümü baştan okumuş olur.
main() {
  local verb sha actor extra
  read -r verb sha actor extra <<<"${SSH_ORIGINAL_COMMAND:-}" || true
  if [[ "${verb:-}" != deploy || ! "${sha:-}" =~ ^[0-9a-f]{40}$ || ! "${actor:-}" =~ ^[A-Za-z0-9-]{1,39}(\[bot\])?$ \
    || -n "${extra:-}" ]]; then
    echo "İzin verilmeyen komut. Beklenen: deploy <40 haneli sha> <github-kullanıcısı>" >&2
    exit 2
  fi

  cd "$HOME/careerai"
  git fetch --quiet origin main
  git merge-base --is-ancestor "$sha" origin/main || { echo "$sha main dalında değil, deploy edilmedi" >&2; exit 1; }

  trap 'docker logout ghcr.io >/dev/null 2>&1 || true' EXIT
  docker login ghcr.io -u "$actor" --password-stdin >/dev/null
  git checkout --quiet --detach "$sha"
  bash infra/staging/deploy.sh "$sha"
}

main "$@"
