# https://developer.chrome.com/blog/chrome-headless-shell?hl=ja

PREFIX=$HOME/.local/share
EXEC=$HOME/.local/share/chrome-headless-shell/*/chrome-headless-shell-*/chrome-headless-shell
LINK=$HOME/.local/bin/chrome-headless-shell

rm -rf $PREFIX/chrome-headless-shell $LINK
mkdir -p $PREFIX $HOME/.local/bin

npx @puppeteer/browsers install chrome-headless-shell@stable --path $PREFIX

ln -s $EXEC $LINK
echo "Created link $LINK"
