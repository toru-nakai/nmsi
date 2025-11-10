# https://kubernetes.io/ja/docs/tasks/tools/install-kubectl-linux/
set -e

curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check

chmod +x kubectl
sudo mv kubectl /usr/local/bin/
sudo chown root: /usr/local/bin/kubectl
echo "Installation finished."
