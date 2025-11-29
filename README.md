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

## Add your own installation scripts as a repository

NMSI supports to update installation scripts from a your own repository.
The repository name is generated from basename of the repository URL.
Supported schemes are http, https, file, git.

```bash
nmsi update --from git@github.com:myusername/myapp.git
```

For example, you can prepare a source repository as follows:

```
myapp
├── linux
│   ├── general
│   │   └── install.sh
│   └── x86_64
│       └── install.sh
└── macos
    ├── general
    │   └── install.sh
    └── arm64
        └── install.sh
```

## List your own repositories

```bash
nmsi list --all
```

## Configuration

Set `NMSI_PATH` environment variable to customize the installation directory (default: `~/.local/share/nmsi`).

```bash
export NMSI_PATH="/custom/path"
```
