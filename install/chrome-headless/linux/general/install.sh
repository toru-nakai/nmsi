# https://developer.chrome.com/blog/chrome-headless-shell?hl=ja

set -e

rm -rf $HOME/.local/share/chrome-headless-shell $HOME/.local/bin/chrome-headless-shell
mkdir -p $HOME/.local/share $HOME/.local/bin
cd $HOME/.local/share

npx @puppeteer/browsers install chrome-headless-shell@stable

ln -s $HOME/.local/share/chrome-headless-shell/linux*/chrome-headless-shell-linux64/chrome-headless-shell $HOME/.local/bin
echo "Created link to $HOME/.local/bin/chrome-headless-shell"

