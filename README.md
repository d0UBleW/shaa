# shaa

## Table of Contents

- [Features](#features)
  - [Ansible Roles](#ansible-roles)
  - [ShaaShell](#shaashell)
- [Requirements](#requirements)
  - [Tools](#tools)
  - [Platform Support](#platform-support)
- [Installation](#installation)
  - [Docker](#docker)
  - [Source](#source)
- [Usage](#usage)
  - [Quick Start](#quick-start)
  - [Managing Inventory](#managing-inventory)
  - [Managing Inventory Node](#managing-inventory-node)
  - [Managing Inventory Group](#managing-inventory-group)
  - [Managing Preset](#managing-preset)
    - [CIS Preset](#cis-preset)

## Features

### Ansible Roles

- Linux system hardening based on `CIS Distribution Independent Linux` Benchmark `v2.0.0 - 07-16-2019`

  - AlmaLinux 8 and 9
  - Ubuntu 20.04
  - openSUSE Leap 15.3

- Compliance Scanning and Report with OpenSCAP

  - AlmaLinux 8 and 9
  - Ubuntu 20.04

- Security tools installation: Wazuh agent

  - AlmaLinux 8 and 9
  - Ubuntu 20.04
  - openSUSE Leap 15.3

### ShaaShell

User Interface for:

- Creating Ansible inventory file
- Enabling and disabling tasks from above roles
- Overriding default variables from above roles
- Generating Ansible playbook and executing the playbook

Additional features:

- Tab completion
- Input validation
- Sensitive data encryption with Ansible Vault, for instance, password variables in above roles
- Unsaved changes reminder

## Requirements

### Tools

- Python >= 3.9.0

### Platform Support

- GNU/Linux
- Windows with Docker

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

## Usage

### Quick Start

1. Set an environment variable called `VAULT_PASSWORD` to encrypt sensitive data

2. View help page

    ```console
    $ shaa-shell -h
    ```

3. Run a `shaa-shell` script. Read more about [`shaa-shell` script](#abcd)

    ```console
    $ shaa-shell /path/to/shaa-shell-script
    ```

4. Run a `shaa-shell` script and go into interactive mode

    ```console
    $ shaa-shell -i /path/to/shaa-shell-script
    ```

5. Start the interactive shell

    ```console
    $ shaa-shell
    shaa>
    ```

6. Use `help -v` to display the help menu

    ```console
    shaa> help -v
    ```

### Managing Inventory

1. To create an inventory

    ```console
    shaa> inventory create my/local

    [inv: my/local]
    shaa>
    ```

2. To list out existing inventories

    ```console
    shaa> inventory list
    ```

    Notice that even though we have created an inventory, it is not listed because it only lists inventories which have been saved.

3. To unload current inventory

    ```console
    [inv: my/local]
    shaa> unload

    shaa>
    ```

4. To load an existing inventory

    ```console
    shaa> inventory load my/local

    [inv: my/local]
    shaa>
    ```

5. To save current inventory

    ```console
    [inv: my/local]
    shaa> inventory save
    ```

6. To save current inventory as another name

    ```console
    [inv: my/local]
    shaa> inventory save my/local-dup
    ```

7. To rename current inventory (saves changes internally)

    ```console
    [inv: my/local]
    shaa> inventory rename my/new-local

    [inv: my/new-local]
    shaa> inventory rename my/local

    [inv: my/local]
    shaa> inventory rename my/local
    ```

8. To delete an inventory

- If an inventory is currently loaded

  ```console
  [inv: my/local]
  shaa> inventory delete

  shaa>
  ```

- Otherwise

  ```console
  [inv: my/local]
  shaa> inventory delete my/local-dup
  ```

### Managing Inventory Node

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

5. Create a node and put it under a group named `webserver`. The group would be created if does not exist yet.

    ```console
    [inv: my/local]
    shaa> node create rhel-01 192.168.10.13 root -k rhel.key -g webserver
    ```

6. To list available inventory nodes

    ```console
    [inv: my/local]
    shaa> node list
    ```

7. To view detailed information on nodes with name that match given regex pattern

    ```console
    [inv: my/local]
    shaa> node info -g webserver rhel-01

    [inv: my/local]
    shaa> node info ubuntu.*
    ```

8. To edit data other than the node name.

    - Edit `ubuntu-02` node's IP address

        ```console
        [inv: my/local]
        shaa> node edit ubuntu-02 -i 192.168.10.22
        ```

    - Edit `ubuntu-01` node's IP address, username, and switch password authentication to SSH private key

        ```console
        [inv: my/local]
        shaa> node edit ubuntu-01 -i 192.168.10.21 -p '' -k ubuntu.key
        ```

9. To rename a node

    ```console
    [inv: my/local]
    shaa> node rename ubuntu-01 ubuntu-focal-01
    ```

10. To remove an inventory node

    ```console
    [inv: my/local]
    shaa> node delete ubuntu-02

    [inv: my/local]
    shaa> node delete -g webserver rhel-01
    ```

11. To unset host variables

    ```console
    [inv: my/local]
    shaa> node unset ubuntu-focal-01 var_name
    ```

### Managing Inventory Group

1. To create a group

    ```console
    [inv:my/local]
    shaa> group create prod
    ```

2. To list out existing groups

    ```console
    [inv:my/local]
    shaa> group list
    ```

3. To view detailed information on groups with name that match the given regex pattern

    ```console
    [inv: my/local]
    shaa> group info .
    ```

4. To rename a group

    ```console
    [inv: my/local]
    shaa> group rename prod production
    ```

5. To unset group variables

    ```console
    [inv: my/local]
    shaa> group unset production var_name
    ```

### Managing Preset

#### CIS Preset

1. To create a CIS preset

    ```console
    shaa> preset cis create part-1

    [cis: part-1]
    shaa>
    ```

2. To list available CIS preset

    ```console
    shaa> preset cis list
    ```

3. To unload current CIS preset

    ```console
    [cis: part-1]
    shaa> preset cis unload

    shaa>
    ```

4. To load an existing CIS preset

    ```console
    shaa> preset cis load part-1 

    [cis: part-1]
    shaa>
    ```

5. To list out available sections on CIS preset

    ```console
    [cis: part-1]
    shaa> cis section list

    [cis: part-1]
    shaa> cis section list 3.2
    ```

6. To enable or disable a section and its subsections

    ```console
    [cis: part-1]
    shaa> cis section enable 3.5

    [cis: part-1]
    shaa> cis section disable 3.5.1
    ```

7. To list out enabled or disabled sections

    ```console
    [cis: part-1]
    shaa> cis section list --status enabled

    [cis: part-1]
    shaa> cis section list --status disabled
    ```

8. To search sections with matching title

    ```console
    [cis: part-1]
    shaa> cis search ssh

    [cis: part-1]
    shaa> cis search --ignore-case ssh
    ```

9. To view a section information on settable variables

    ```console
    [cis: part-1]
    shaa> cis section info 5.2.15
    ```

10. To set or unset a variable value globally

    ```console
    [cis: part-1]
    shaa> cis set -s 5.2.15 sshd_kex_algs ecdh-sha2-nistp521

    [cis: part-1]
    shaa> cis unset -s 5.2.5 sshd_log_level
    ```

11. To set or unset a variable value on a node under a certain group

    ```console
    [inv: my/local] [cis: part-1]
    shaa> cis set -s 5.2.15 sshd_kex_algs ecdh-sha2-nistp256 -n ubuntu-focal-01

    [inv: my/local] [cis: part-1]
    shaa> cis set -s 5.2.15 sshd_kex_algs ecdh-sha2-nistp256 -n ubuntu-03 -g production

    [inv: my/local] [cis: part-1]
    shaa> cis unset -s 5.2.15 sshd_kex_algs -n ubuntu-focal-01

    [inv: my/local] [cis: part-1]
    shaa> cis unset -s 5.2.15 sshd_kex_algs -n ubuntu-03 -g production
    ```

12. To set or unset a variable value on a certain group

    ```console
    [inv: my/local] [cis: part-1]
    shaa> cis set -s 5.2.5 sshd_log_level INFO -g production

    [inv: my/local] [cis: part-1]
    shaa> cis unset -s 5.2.5 sshd_log_level -g production
    ```

13. To save the current CIS preset

    ```console
    [inv: my/local] [cis: part-1]
    shaa> preset cis save
    ```

14. To save the current CIS preset as another name

    ```console
    [inv: my/local] [cis: part-1]
    shaa> preset cis save dup-part-1
    ```

15. To rename the current CIS preset (saves changes internally)

    ```console
    [inv: my/local] [cis: part-1]
    shaa> preset cis rename new-part-1

    [inv: my/local] [cis: new-part-1]
    shaa> preset cis rename part-1

    [inv: my/local] [cis: part-1]
    shaa>
    ```

16. To delete a CIS preset

- If a CIS preset is currently loaded

  ```console
  [cis: part-1]
  shaa> preset cis delete

  shaa>
  ```

- Otherwise

  ```console
  [cis: part-1]
  shaa> preset cis dup-part-1
  ```
