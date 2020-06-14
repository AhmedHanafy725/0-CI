import time
from urllib.parse import urljoin

from telegram import Bot, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton

from models.initial_config import InitialConfig

RETRIES = 5


class Telegram:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        configs = InitialConfig()
        if configs.bot_token:
            self.telegram_cl = Bot(configs.bot_token)

    def send_msg(self, msg, link, repo=None, branch=None, commit=None, committer=None, bin_link=None, triggered_by=None):
        """Send Telegram message using Telegram bot.

        :param msg: message to be sent.
        :type msg: str
        :param link: result link
        :type link: str
        :param repo: full repo name
        :type repo: str
        :param branch: branch name
        :type branch: str
        :param commit: commit hash.
        :type commit: str
        :param committer: committer name.
        :type committer: str
        """
        configs = InitialConfig()
        repo_link = urljoin(configs.vcs_host, repo)
        commit_link = urljoin(configs.vcs_host, f"{repo}/commit/{commit}")
        committer_link = urljoin(configs.vcs_host, committer)
        if commit:
            msg = f"""{msg}
<a href="{repo_link}">{repo}</a>
{branch} <a href="{commit_link}">{commit[:7]}</a>
👤 <a href="{committer_link}">{committer}</a>"""

        if triggered_by:
            msg += f"\nTriggered_by: {triggered_by}"
        button_list = [InlineKeyboardButton("Result", url=link)]
        if bin_link:
            button_list.append(InlineKeyboardButton("Bin"), url=bin_link)
        reply_markup = InlineKeyboardMarkup([button_list])

        for _ in range(RETRIES):
            try:
                self.telegram_cl.send_message(
                    chat_id=configs.chat_id,
                    text=msg,
                    reply_markup=reply_markup,
                    parse_mode="html",
                    disable_web_page_preview=True,
                )
                break
            except Exception:
                time.sleep(1)
