# Installation and Configuration

## Installation

- Create a [kubernetes cluster](https://manual2.threefold.io/#/kubernetes).
- Create a [solution expose](https://manual2.threefold.io/#/exposed) to tls-port 443 and port 80.
- Connect to the cluster using `ssh`.
- Install [helm](https://helm.sh/docs/intro/install/).

### Install from repository

- Clone the repository and go to installation directory.

  ```bash
  git clone https://github.com/threefoldtech/zeroCI.git
  cd zeroCI/install/zeroci
  ```

- Install ZeroCI.
  (**Note:** the domain used should be the same as the one on solution expose in the second step.

  ```bash
  helm install mytest . --namespace myspace --create-namespace --set "ingress.hosts[0].host=<domain>" --set "ingress.hosts[0].paths[0]=/"
  ```

  **Example:**
    If you need to set domain to `zeroci.grid.tf`, so the command will be:

  ```bash
  helm install mytest . --namespace myspace --create-namespace --set "ingress.hosts[0].host=zeroci.grid.tf" --set "ingress.hosts[0].paths[0]=/"
  ```

### Install from marketplace

- Add marketplace helm charts repository.

  ```bash
  helm repo add marketplace https://threefoldtech.github.io/marketplace-charts/
  ```

- Install ZeroCI.
  (**Note:** the domain used should be the same as the one on solution expose in the second step.

  ```bash
  helm install mytest marketplace/zeroci --namespace myspace --create-namespace --set "ingress.hosts[0].host=<domain>" --set "ingress.hosts[0].paths[0]=/"
  ```

  **Example:**
    If you need to set domain to `zeroci.grid.tf`, so the command will be:

  ```bash
  helm install mytest marketplace/zeroci --namespace myspace --create-namespace --set "ingress.hosts[0].host=zeroci.grid.tf" --set "ingress.hosts[0].paths[0]=/"
  ```

## Configuration

Go to the domain that ZeroCI has been deployed on, you will be asked for login first, then please fill the following configurations:

### 1- Version Control System

![vcs](../docs/Images/vcs.png)

- **Domain**:  The domain that will point to your server, this will be used to add webhooks on the repositories (will be added in [Repositories](#2--repositories) step) and send the result link with it.
- **Version Control System Host**: The domain or ip that the version control system is running on.
(**Note:** [Github](https://github.com) and [Gitea](https://gitea.io/en-us/) are only supported)
- **Version Control System**: Version control system access token for user, [create one](https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token) and make sure that this token his full permission on hooks and status as the following:

![vcs token](../docs/Images/vcs_token.png)
  
### 2- Repositories

![repos](../docs/Images/repos_config.png)

- **Username:** A username on Version Control System that has been added in the pervious step to search and get his public repositories.

- **Organization** : An organization on Version Control System that has been added in the pervious step to search and get the public repositories on this organization.

(**Note:**`username` and/or `organization` can be added.)

- **Select Repos**: Once the username and/or organization is added, the dropdown list will be available to select the repositories that ZeroCI will run on.

### 3- Telegram

![telegram config](../docs/Images/telegram_config.png)

- **Telegram Chat ID**: a Telegram Channel or Group ID that the result messages will be sent on. (**Note:** it should start with `@`)

- **Telegram Bot**: Telegram bot token that will be used to send the result messages, [Create one](https://core.telegram.org/bots#3-how-do-i-create-a-bot) and add it to this Channel.

(**Note**: Once the configuration is done, ZeroCI will set you as admin, and this configuration can be changed only by admins)
