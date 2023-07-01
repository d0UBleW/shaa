# shaa

## Requirements

- Python >= 3.9.0

## Installation

```sh
# Clone the repository
git clone https://github.com/d0UBleW/shaa
cd shaa

# Copy roles to ansible default role search path
cp -r ./ansible/roles ~/.ansible/roles

##########
# Install the interactive shell
##########

# Create virtual environment (optional, but recommended)
python3 -m venv venv
. ./venv/bin/activate

pip install ./ui
```

## Usage

1. Set an environment variable called `VAULT_PASSWORD` to encrypt sensitive data

2. Start the interactive shell

    ```console
    $ shaa-shell
    shaa>
    ```

3. Use `help` to display the help menu

    ```console
    shaa> help
    ```

### Managing Inventory

1. To create inventory named `my/local`

    ```console
    shaa> inventory create my/local
    ```

2. To list out available inventory

3. Load inventory
4. Save inventory
5. Rename inventory

#### Inventory Node

