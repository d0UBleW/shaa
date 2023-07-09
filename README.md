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
  - [Managing Profile](#managing-profile)
  - [Running Automation](#running-automation)
  - [General](#general)
  - [Script Examples](#script-examples)

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
    d0ublew/shaa-shell
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

3. Run a `shaa-shell` script. Read more about [`shaa-shell` script](#script-examples)

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
    shaa> inventory unload

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

1. To create a preset, specify the preset type: `cis`, `oscap`, `sec_tools`, `util`

    ```console
    shaa> preset cis create part-1

    [cis: part-1]
    shaa>
    ```

2. To list out available presets

    ```console
    shaa> preset cis list
    ```

3. To unload current preset

    ```console
    [cis: part-1]
    shaa> preset cis unload

    shaa>
    ```

4. To load an existing preset

    ```console
    shaa> preset cis load part-1 

    [cis: part-1]
    shaa>
    ```

5. To list out available tasks on a preset

    - CIS preset

        ```console
        [cis: part-1]
        shaa> cis section list

        [cis: part-1]
        shaa> cis section list 3.2
        ```

    - Other preset, e.g., `oscap`

        ```console
        [oscap: pre_hardened]
        shaa> oscap action list
        ```

6. To enable or disable tasks

    - CIS preset

        ```console
        [cis: part-1]
        shaa> cis section enable 3.5 5.2.5

        [cis: part-1]
        shaa> cis section disable 3.5.1 3.5.2.2
        ```

    - Other preset, e.g., `sec_tools`

        ```console
        [sec_tools: example]
        shaa> sec_tools action enable all

        [sec_tools: example]
        shaa> sec_tools action disable all
        ```

7. To list out enabled or disabled sections

    - CIS preset

        ```console
        [cis: part-1]
        shaa> cis section list --status enabled

        [cis: part-1]
        shaa> cis section list --status disabled
        ```

    - Other preset, e.g., `util`

        ```console
        [util: example]
        shaa> util action list --status enabled

        [util: example]
        shaa> util action list --status disabled
        ```

8. To search sections with matching title

    ```console
    [cis: part-1]
    shaa> cis search ssh

    [cis: part-1]
    shaa> cis search --ignore-case ssh
    ```

9. To view a section information on settable variables

    - CIS preset

        ```console
        [cis: part-1]
        shaa> cis section info 5.2.15
        ```

    - Other preset, e.g., `oscap`

        ```console
        [oscap: pre_hardened]
        shaa> oscap action info scan
        ```

10. To set or unset a variable value globally

    - CIS preset

        ```console
        [cis: part-1]
        shaa> cis set -s 5.2.15 sshd_kex_algs ecdh-sha2-nistp521

        [cis: part-1]
        shaa> cis unset -s 5.2.5 sshd_log_level
        ```

    - Other preset

        ```console
        [oscap: pre_hardened]
        shaa> oscap set -a scan scan_profiles level_1_server level_1_workstation

        [oscap: pre_hardened]
        shaa> oscap unset -a scan report_output_prefix
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

### Managing Profile

1. To list out existing profiles

    ```console
    shaa> profile list
    ```

2. To create a profile

    - No inventory and presets loaded

        ```console
        shaa> profile create empty

        [pro: empty]
        shaa> profile info

        profile name      :  empty
        inventory         :
        cis               :
        oscap             :
        sec_tools         :
        util              :
        ```

    - With inventory or preset loaded

        ```console
        [inv: my/local] [cis: part-1]
        shaa> profile create example-1

        [pro: example-1] [inv: my/local] [cis: part-1]
        shaa> profile info

        profile name      :  example-1
        inventory         :  my/local
        cis               :  part-1
        oscap             :
        sec_tools         :
        util              :
        ```

3. To unload current profile

    ```console
    [pro: example-1] [inv: my/local] [cis: part-1]
    shaa> profile unload

    [inv: my/local] [cis: part-1]
    shaa>
    ```

4. To load an existing profile

    ```console
    [inv: idk] [cis: idk] [oscap: idk]
    shaa> profile load example-1

    [pro: example-1] [inv: my/local] [cis: part-1]
    shaa>
    ```

5. To configure profile

    ```console
    [pro: example-1] [inv: my/local] [cis: part-1]
    shaa> profile set inventory idk

    [pro: example-1] [inv: idk] [cis: part-1]
    shaa> profile set oscap pre_hardened

    [pro: example-1] [inv: idk] [cis: part-1] [oscap: pre_hardened]
    shaa> profile unset cis

    [pro: example-1] [inv: idk] [*cis: part-1] [oscap: pre_hardened]
    shaa>
    ```

    Notice the asterisk `*` in `[*cis: part-1]`. This is to indicate that the loaded object differs from the loaded profile configuration

6. To save current profile

    ```console
    [pro: example-1] [inv: my/local] [oscap: pre_hardened]
    shaa> profile save
    ```

7. To save current profile as another name

    ```console
    [pro: example-1] [inv: my/local] [oscap: pre_hardened]
    shaa> profile save example-1-dup
    ```

8. To rename current profile (saves changes internally)

    ```console
    [pro: example-1] [inv: my/local] [oscap: pre_hardened]
    shaa> profile rename example-2

    [pro: example-2] [inv: my/local] [oscap: pre_hardened]
    shaa> inventory rename example-1

    [pro: example-1] [inv: my/local] [oscap: pre_hardened]
    shaa>
    ```

9. To delete a profile

    - If a profile is currently loaded

        ```console
        [pro: example-1] [inv: my/local] [oscap: pre_hardened]
        shaa> profile delete

        [inv: my/local] [oscap: pre_hardened]
        shaa>
        ```

    - Otherwise

        ```console
        [pro: example-1] [inv: my/local] [oscap: pre_hardened]
        shaa> profile delete example-1-dup
        ```

### Running Automation

1. Run according to currently loaded inventory and presets (`-c` to enable colorized output)

    ```console
    [inv: my/local] [cis: part-1]
    shaa> play -c
    ```

2. Run on specific target

    ```console
    [inv: my/local] [cis: part-1]
    shaa> play -c --target production ubuntu-focal-01
    ```

3. Run specific presets

    ```console
    [inv: my/local] [cis: part-1] [oscap: pre_hardened] [sec_tools: idk]
    shaa> play -c -p oscap sec_tools
    ```

### General

1. Unload everything, i.e., profile, inventory, and presets

    ```console
    [pro: example-1] [inv: my/local] [oscap: pre_hardened] [sec_tools: idk]
    shaa> unload

    shaa>
    ```

2. Clear screen

    ```console
    shaa> clear
    ```

3. Create alias

    ```console
    shaa> alias create c clear
    shaa> alias create inv inventory
    shaa> alias create pre preset
    shaa> alias create pro profile
    ```

4. Edit startup script

    ```console
    shaa> config
    ```

    Alternative: edit the file directly on `~/.shaa/shaashrc`

5. Suppress output that starts with `[*]` or `[+]`

    ```console
    shaa> set quiet true
    ```

6. Disable error message red highlight

    ```console
    shaa> set allow_style never
    ```

### Script Examples

- Example script to initialize inventory

    ```sh
    # file: /tmp/init-inv.shaa

    set quiet true
    inventory delete -f abcdef
    inventory create abcdef
    node create ubuntu-01 192.168.10.101 vagrant -p vagrant
    node create rhel-01 192.168.11.101 vagrant -k rhel.key -g prod
    inventory save
    ```

- Example script to run automation

    ```sh
    # file: /tmp/run-example.shaa

    profile load example
    play -c
    ```

If shaa-shell is installed locally

```console
$ shaa-shell /tmp/init-inv.shaa
```

If shaa-shell is run via docker, copy the script to the directory which is mounted to the docker container

```sh
# Prepare the directory
mkdir -p ~/.shaa/scripts

# Copy the scripts
cp /tmp/init-inv.shaa ~/.shaa/scripts

# Run the docker container
docker run -it \
    --rm \
    -v ~/.shaa:/home/shaa/.shaa \
    d0ublew/shaa-shell \
    shaa-shell /home/shaa/.shaa/scripts/init-inv.shaa
```
