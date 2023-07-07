# shaa

## Requirements

- Python >= 3.9.0

## Installation

### Docker

Choose **either** one:

- Pull from docker hub registry

    ```sh
    docker pull d0ublew/shaa
    ```

- Build from source

    ```sh
    # Clone the repository
    git clone https://github.com/d0UBleW/shaa
    cd shaa

    docker build -t d0ublew/shaa .
    ```

After the docker image is ready, use this command to interact

```sh
docker run -it \
    --rm \
    -v ~/.shaa:/home/shaa/.shaa \
    d0ublew/shaa-shell shaa-shell
```

### Source

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

After the pip installation is done, run the following command to verify if the installation is successful

```sh
shaa-shell
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

#### Creating Inventory

```console
shaa> inventory create my/local
```

This will caused the shell to automatically load the inventory which could be seen from the shell prompt.

```console
[inv: my/local]
shaa>
```

#### Listing Existing Inventory

```console
shaa> inventory list

Name
--------------------------------


shaa>
```

Notice that even though we have created an inventory, it is not listed because it only lists inventories which have been saved.

```console
shaa> inventory create my/local

[inv: my/local]
shaa> inventory save

[inv: my/local]
shaa> inventory list

Name
--------------------------------
my/local


[inv: my/local]
shaa>
```

#### Adding an Inventory Node

1. To add a machine, it is necessary to have an inventory loaded.

    ```console
    shaa> inventory load my/local
    ```

2. View help page

    ```console
    [inv: my/local]
    shaa> help node create

    [inv: my/local]
    shaa> node create --help
    ```

3. Create a node with password authentication

    ```console
    [inv: my/local]
    shaa> node create ubuntu-01 192.168.10.11 root -p P@ssw0rd
    ```

4. Create a node with SSH private key authentication. The keys should be located under `~/.shaa/data/ssh/`

    ```console
    [inv: my/local]
    shaa> node create ubuntu-02 192.168.10.12 root -k ubuntu.key
    ```

5. Create a node and put it under a group named `webserver`

    ```console
    [inv: my/local]
    shaa> node create ubuntu-03 192.168.10.13 root -k ubuntu.key -g webserver
    ```
