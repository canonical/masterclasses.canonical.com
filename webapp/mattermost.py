import json
from dataclasses import asdict, dataclass
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class MattermostMessagePayload:
    """
    More fields can be found here: https://developers.mattermost.com/integrate/webhooks/incoming/#parameters

    Example:
    ```python
    payload = MattermostMessagePayload(text="Hello, world!")
    ```
    """
    text: str
    """
    [Markdown-formatted](https://docs.mattermost.com/messaging/formatting-text.html) message to display in the post.
    To trigger notifications, use `@<username>`, `@channel`, and `@here` like you would in other Mattermost messages.
    """
    username: Optional[str] = None
    """
    Overrides the username the message posts as.
    Defaults to the username set during webhook creation; if no username was set during creation, webhook is used.
    The [Enable integrations to override usernames](https://docs.mattermost.com/configure/configuration-settings.html#enable-integrations-to-override-usernames) configuration setting must be enabled for the username override to take effect.
    """
    icon_url: Optional[str] = None
    """
    Overrides the profile picture the message posts with.
    Defaults to the URL set during webhook creation; if no icon was set during creation, the standard webhook is displayed.
    The [Enable integrations to override profile picture icons](https://docs.mattermost.com/configure/configuration-settings.html#enable-integrations-to-override-profile-picture-icons) configuration setting must be enabled for the icon override to take effect."""
    channel: Optional[str] = None
    """
    Overrides the channel the message posts in. Use the channel's name and not the display name, e.g. use `town-square`, not `Town Square`.
    Use an `@` followed by a username to send to a Direct Message.

    Defaults to the channel set during webhook creation.
    The webhook can post to any Public channel and Private channel the webhook creator is in.
    Posts to Direct Messages will appear in the Direct Message between the targeted user and the webhook creator.
    """


class MattermostSendMessageError(Exception):
    """
    Raised when a message fails to send to mattermost.
    """
    pass


def send_message(message_payload: MattermostMessagePayload,  webhook_url: str):
    """
    Sends a message to a mattermost webhook.

    Args:
        messagePayload: The message payload to send.
        webhook_url: The URL of the mattermost webhook, instructions on how to create one can be found here: https://developers.mattermost.com/integrate/webhooks/incoming/#create-an-incoming-webhook
    Raises:
        `requests.exceptions.RequestException`: If the message fails to send.
        `MattermostSendMessageError`: If the message fails to send.
    """
    logger.info(f"Sending mattermost message to {webhook_url}")
    response = requests.post(webhook_url, json=asdict(message_payload), headers={
                             "Content-Type": "application/json"})
    if response.text != "ok":
        raise MattermostSendMessageError(
            f"Failed to send message to mattermost: {response.text}")


def try_send_message(message_payload: MattermostMessagePayload,  webhook_url: str) -> bool:
    """
    Tries to send a message to a mattermost webhook.
    If the message fails to send, it will log an error and return False.
    If the message is sent successfully, it will return True.

    Args:
        messagePayload: The message payload to send.
        webhook_url: The URL of the mattermost webhook, instructions on how to create one can be found here: https://developers.mattermost.com/integrate/webhooks/incoming/#create-an-incoming-webhook
    """
    try:
        send_message(message_payload, webhook_url)
        return True
    except (MattermostSendMessageError, requests.exceptions.RequestException) as e:
        logger.error(f"Error sending message: {e}")
        return False
