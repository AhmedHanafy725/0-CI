# Installation and Configuration

## Installation

- Create a [kubernetes cluster](https://sdk2.threefold.io/#/solution_kubernetes?id=kubernetes-cluster-deployment) .
- Connect to the cluster using `ssh`.
- Create directories for BCDB and Redis.
  
  ```bash
  sudo mkdir -p /sandbox/{var,redis}
  ```

- Create zeroci directory and get installation yaml files.

  ```bash
  mkdir ~/zeroci
  cd ~/zeroci
  for s in authorization deployment service; do curl https://raw.githubusercontent.com/threefoldtech/zeroCI/development/install/zeroci/$s.yaml --output $s.yaml; done
  ```

- Apply the installation yaml files.

  ```bash
  kubectl apply -f ~/zeroci
  ```

- Create a Telegram Channel.
- Create a [Telegram bot](https://core.telegram.org/bots#3-how-do-i-create-a-bot) and add it to this Channel.

## Configuration

Go to the domain that ZeroCI has been deployed on, you will be asked for login first, then please fill the following configurations:

- **domain**:  The domain that will point to your server.
- **bot_token**: Telegram bot token that will be used to send the result messages.
- **chat_id**: Telegram Channel ID that the result messages will be sent on.
- **vcs_host**: The domain or ip that the version control system is working on.
- **vcs_token**: Version control system access token for user.
- **repos**: List of repositories full name that will run on your zeroCI

Also in this page, admins can add or remove admins or users.

(**Note**: Once the configuration is done, ZeroCI will set you as admin, This configuration can be changed only by admins)

```diff
- Once the configuration page is finished, I will add pictures for how to configure
```
