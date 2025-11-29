# https://nodejs.org/ja/download

set -e
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
\. "$HOME/.nvm/nvm.sh"
nvm install 24

# find shell configuration file
if [ -z "$SHELL" ]; then
    echo "SHELL variable is not set"
    exit 1
fi

shell_config_file="$HOME/.$(basename $SHELL)rc"
if [ "$SHELL" = "/bin/sh" ]; then
    shell_config_file="$HOME/.profile"
fi

# add nvm initialization to shell configuration file
if ! grep -q "source \$HOME/.nvm/nvm.sh" $shell_config_file; then
    echo "source \$HOME/.nvm/nvm.sh" >> $shell_config_file
    echo "nvm initialization added to $shell_config_file"
else
    echo "nvm initialization seems already installed in $shell_config_file"
    echo "If not, please add the following line to your shell configuration file:"
    echo "source \$HOME/.nvm/nvm.sh"
fi
