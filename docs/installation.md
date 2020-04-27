# Installation and running

## Requirements

- Create a vm with Ubuntu:18.04.
- Install [JSX](https://github.com/threefoldtech/jumpscaleX_core/tree/development/docs/Installation)
- Create a Telegram group chat.
- Create Telegram bot and add it to this group chat.
- Clone the repository and install packages required.

    ```bash
    mkdir -p /sandbox/code/github/threefoldtech
    cd /sandbox/code/github/threefoldtech
    git clone https://github.com/threefoldtech/zeroCI.git
    cd zeroCI
    pip3 install -r install/requirement.txt
    ```

- Frontend requirements
  
  ```bash
  apt-get install -y nodejs npm
  cd /sandbox/code/github/threefoldtech/zeroCI/frontend
  npm install
  npm run build
  ```

## Configuration

Go to the domain that ZeroCI has been deployed on, you will be asked for login first, then please fill the following configurations:

- **Domain**:  The domain that will point to your server.

- **Telegram chat ID**: Should result messages will be sent on.
- **Telegram bot token**: The bot token that has been created in requirement step.

- **itsyouonline ID and secret**: Used to deploy VMs.

- **vcs host**: The domain or ip that the version control system is working on.
- **vcs token**: Version control system access token for user.
- **repos**: List of repositories full name that will run on your zeroCI

Also in this page, admins can add or remove admins or users.

(**Note**: Once the configuration is done, ZeroCI will set you as admin, This configuration can be changed only by admins)

## How to run the server

```bash
bash install/run.sh
```
