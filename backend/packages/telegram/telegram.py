import time

from telegram import Bot, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton

from bcdb.bcdb import InitialConfig

RETRIES = 5


class Telegram(InitialConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.configured:
            self.telegram_cl = Bot(self.bot_token)

    def send_msg(self, msg, link, repo=None, branch=None, commit=None, committer=None):
        """Send Telegram message using Telegram bot.

        :param msg: message to be sent.
        :type msg: str
        :param repo: full repo name
        :type repo: str
        :param branch: branch name
        :type branch: str
        :param commit: commit hash.
        :type commit: str
        :param committer: committer name.
        :type committer: str
        """
        if commit:
            msg = f"""{msg}
<a href="{self.vcs_host}/{repo}">{repo}</a>
{branch} <a href="{self.vcs_host}/{repo}/commit/{commit}">{commit[:7]}</a>
👤 <a href="{self.vcs_host}/{committer}">{committer}</a>"""

        button_list = [InlineKeyboardButton("Result", url=link)]
        reply_markup = InlineKeyboardMarkup([button_list])

        # msg = "\n".join([msg, repo, branch, committer, commit])
        for _ in range(RETRIES):
            try:
                self.telegram_cl.send_message(
                    chat_id=self.chat_id,
                    text=msg,
                    reply_markup=reply_markup,
                    parse_mode="html",
                    disable_web_page_preview=True,
                )
                break
            except Exception:
                time.sleep(1)
