# https://rust-lang.org/ja/tools/install/

if ! which rustup; then
  echo "rustup is not installed yet"
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
else
  rustup update
fi
