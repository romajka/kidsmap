#!/usr/bin/env bash
set -euo pipefail

SSH_DIR="${HOME}/.ssh"
KEY_PATH="${SSH_DIR}/id_ed25519"
HOSTNAME_VALUE="$(hostname -f 2>/dev/null || hostname)"
KEY_COMMENT="${GITHUB_KEY_COMMENT:-kidsmap-server@${HOSTNAME_VALUE}}"

log() {
  printf '[github-ssh] %s\n' "$*"
}

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

if [[ ! -f "$KEY_PATH" ]]; then
  log "Generating SSH key at $KEY_PATH"
  ssh-keygen -t ed25519 -C "$KEY_COMMENT" -f "$KEY_PATH" -N ""
else
  log "Using existing SSH key at $KEY_PATH"
fi

touch "${SSH_DIR}/known_hosts"
chmod 600 "${SSH_DIR}/known_hosts"
ssh-keyscan -H github.com >> "${SSH_DIR}/known_hosts" 2>/dev/null || true

cat > "${SSH_DIR}/config" <<EOF
Host github.com
    HostName github.com
    User git
    IdentityFile ${KEY_PATH}
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new
EOF
chmod 600 "${SSH_DIR}/config"

log "Public key to add in GitHub -> Settings -> SSH keys or Deploy keys:"
printf '\n'
cat "${KEY_PATH}.pub"
printf '\n\n'

log "Testing SSH auth to GitHub"
set +e
ssh -T git@github.com
SSH_EXIT=$?
set -e

if [[ "$SSH_EXIT" -eq 1 ]]; then
  log "GitHub SSH auth is working. Exit code 1 is expected for ssh -T."
  exit 0
fi

log "GitHub SSH auth is not ready yet."
log "Add the printed public key to GitHub, then rerun:"
log "  ssh -T git@github.com"
