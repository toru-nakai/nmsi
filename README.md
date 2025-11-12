# nmsi

No More Search for Installation. I am tired to search the same opens source 
installation method again, again...
This tool intends to be a quick and handy tool to install open source software.

## Installation

```bash
pip install nmsi
```

or run directly via uvx.

```bash
uvx nmsi update && uvx nmsi install uv
```

## Usage

Update installation scripts

```bash
nmsi update
```

List available tools

```bash
nmsi list
```

Install a tool

```bash
nmsi install <tool_name>
```

Add a custom script

```bash
nmsi add --name <tool_name> <script.sh>
```

Download installation scripts from a custom URL. Archive file is only supported 
like zip, tar, etc. for http). This option overrides current installation scripts.

```bash
nmsi update --from <url>
```

## Configuration

Set `NMSI_PATH` environment variable to customize the installation directory (default: `~/.local/share/nmsi`).

```bash
export NMSI_PATH="/custom/path"
```

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit an issue or pull request.
