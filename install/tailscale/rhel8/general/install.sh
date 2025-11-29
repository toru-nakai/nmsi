# https://tailscale.com/kb/1046/install-rhel-8

set -e

sudo dnf config-manager --add-repo https://pkgs.tailscale.com/stable/rhel/8/tailscale.repo
sudo dnf -y install tailscale
sudo systemctl enable --now tailscaled
sudo tailscale up

