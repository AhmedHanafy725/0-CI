# Installation and running

## Requirements

- Create a [kubernetes cluster](https://sdk2.threefold.io/#/solution_kubernetes?id=kubernetes-cluster-deployment) .
- Connect to the cluster using `ssh`.
- Create a directories for bcdb and redis 
  
  ```bash
  sudo mkdir -p /sandbox/{var,redis}
  ```

- Create zeroci directory and get installation yaml files.

  ```bash
  mkdir ~/zeroci
  cd ~/zeroci
  for s in authorization deployment service; do wget https://raw.githubusercontent.com/threefoldtech/zeroCI/development/install/zeroci/$s.yaml; done
  ```

- Apply the installation yaml files.

  ```bash
  kubectl apply -f ~/zeroci
  ```

- Create a Telegram group chat.
- Create Telegram bot and add it to this group chat.

## Configuration

Go to the domain that ZeroCI has been deployed on, you will be asked for login first, then please fill the following configurations:

- **Domain**:  The domain that will point to your server.

- **Telegram chat ID**: Should result messages will be sent on.
- **Telegram bot token**: The bot token that has been created in requirement step.
- **vcs host**: The domain or ip that the version control system is working on.
- **vcs token**: Version control system access token for user.
- **repos**: List of repositories full name that will run on your zeroCI

Also in this page, admins can add or remove admins or users.

(**Note**: Once the configuration is done, ZeroCI will set you as admin, This configuration can be changed only by admins)

```diff
- Once the configuration page is finished, I will add pictures for how to configure
```
