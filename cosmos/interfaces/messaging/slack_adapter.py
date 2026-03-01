"""
<<<<<<< HEAD:cosmos/interfaces/messaging/slack_adapter.py
cosmos Slack Adapter
------------------------
Connects cosmos to Slack via slack-bolt.
=======
Farnsworth Slack Adapter
------------------------
Connects Farnsworth to Slack via slack-bolt.
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/interfaces/messaging/slack_adapter.py

Usage:
    export SLACK_BOT_TOKEN=xoxb-your-token
    export SLACK_SIGNING_SECRET=your-signing-secret

<<<<<<< HEAD:cosmos/interfaces/messaging/slack_adapter.py
    from cosmos.interfaces.messaging.slack_adapter import SlackAdapter
=======
    from farnsworth.interfaces.messaging.slack_adapter import SlackAdapter
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/interfaces/messaging/slack_adapter.py

    adapter = SlackAdapter()
    adapter.set_callback(my_message_handler)
    await adapter.connect()
"""

import os
import asyncio
from datetime import datetime
from typing import Optional, Callable, Awaitable
from loguru import logger

<<<<<<< HEAD:cosmos/interfaces/messaging/slack_adapter.py
from cosmos.interfaces.messaging.base import (
=======
from farnsworth.interfaces.messaging.base import (
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/interfaces/messaging/slack_adapter.py
    MessagingProvider,
    IncomingMessage,
    OutgoingMessage,
    MessageSource
)

# Try to import slack-bolt
try:
    from slack_bolt.async_app import AsyncApp
    from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    logger.warning("slack-bolt not installed. Run: pip install slack-bolt")


class SlackAdapter(MessagingProvider):
    """
<<<<<<< HEAD:cosmos/interfaces/messaging/slack_adapter.py
    Slack messaging adapter for cosmos.

    Provides:
    - Two-way messaging with Slack users
    - Slash command handling (/cosmos)
=======
    Slack messaging adapter for Farnsworth.

    Provides:
    - Two-way messaging with Slack users
    - Slash command handling (/farnsworth)
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/interfaces/messaging/slack_adapter.py
    - Thread support
    - Emoji reactions
    - Channel and DM support
    """

    def __init__(self, bot_token: Optional[str] = None, signing_secret: Optional[str] = None,
                 app_token: Optional[str] = None):
        super().__init__("slack")
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self.signing_secret = signing_secret or os.getenv("SLACK_SIGNING_SECRET")
        self.app_token = app_token or os.getenv("SLACK_APP_TOKEN")  # For Socket Mode
        self.app: Optional[AsyncApp] = None
        self.handler: Optional[AsyncSocketModeHandler] = None
        self._running = False

<<<<<<< HEAD:cosmos/interfaces/messaging/slack_adapter.py
        # cosmos persona
=======
        # Farnsworth persona
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/interfaces/messaging/slack_adapter.py
        self.persona_prefix = "_*adjusts spectacles*_ "
        self.bot_user_id: Optional[str] = None

    async def connect(self):
        """Start the Slack bot."""
        if not SLACK_AVAILABLE:
            logger.error("slack-bolt not installed")
            return

        if not self.bot_token:
            logger.error("SLACK_BOT_TOKEN not set")
            return

        try:
            # Initialize app
            self.app = AsyncApp(
                token=self.bot_token,
                signing_secret=self.signing_secret
            )

            # Get bot user ID
            auth_response = await self.app.client.auth_test()
            self.bot_user_id = auth_response["user_id"]
            logger.info(f"Slack bot connected as {auth_response['user']}")

            # Register event handlers
            self._register_handlers()

            # Start socket mode if app token provided
            if self.app_token:
                self.handler = AsyncSocketModeHandler(self.app, self.app_token)
                self._running = True
                await self.handler.start_async()
            else:
                logger.warning("No SLACK_APP_TOKEN - running in HTTP mode (needs webhook setup)")
                self._running = True

        except Exception as e:
            logger.error(f"Failed to connect Slack bot: {e}")
            self._running = False

    def _register_handlers(self):
        """Register Slack event handlers."""

        @self.app.event("app_mention")
        async def handle_mention(event, say):
            """Handle @mentions of the bot."""
            await self._process_event(event, say)

        @self.app.event("message")
        async def handle_message(event, say):
            """Handle direct messages."""
            # Only respond to DMs or if mentioned
            if event.get("channel_type") == "im":
                await self._process_event(event, say)

<<<<<<< HEAD:cosmos/interfaces/messaging/slack_adapter.py
        @self.app.command("/cosmos")
        async def handle_slash_command(ack, respond, command):
            """Handle /cosmos slash command."""
=======
        @self.app.command("/farnsworth")
        async def handle_slash_command(ack, respond, command):
            """Handle /farnsworth slash command."""
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/interfaces/messaging/slack_adapter.py
            await ack()
            text = command.get("text", "")

            if not text:
                await respond(
<<<<<<< HEAD:cosmos/interfaces/messaging/slack_adapter.py
                    "*Good news, everyone!* Use `/cosmos <your question>` to ask me something!"
=======
                    "*Good news, everyone!* Use `/farnsworth <your question>` to ask me something!"
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/interfaces/messaging/slack_adapter.py
                )
                return

            # Create IncomingMessage
            incoming = IncomingMessage(
                id=command["trigger_id"],
                source=MessageSource.SLACK,
                sender_id=command["user_id"],
                sender_name=command["user_name"],
                channel_id=command["channel_id"],
                content=text,
                timestamp=datetime.now(),
<<<<<<< HEAD:cosmos/interfaces/messaging/slack_adapter.py
                metadata={"command": "/cosmos"}
=======
                metadata={"command": "/farnsworth"}
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/interfaces/messaging/slack_adapter.py
            )

            if self._on_message_callback:
                await self._on_message_callback(incoming)
            else:
                await respond(
                    f"{self.persona_prefix}You asked: {text}\n\n"
<<<<<<< HEAD:cosmos/interfaces/messaging/slack_adapter.py
                    "I'm running in standalone mode. Connect me to the full cosmos system!"
=======
                    "I'm running in standalone mode. Connect me to the full Farnsworth system!"
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/interfaces/messaging/slack_adapter.py
                )

    async def _process_event(self, event: dict, say):
        """Process a Slack event."""
        # Ignore bot's own messages
        if event.get("user") == self.bot_user_id:
            return

        # Ignore bot messages
        if event.get("bot_id"):
            return

        text = event.get("text", "")

        # Remove bot mention from text
        if self.bot_user_id:
            text = text.replace(f"<@{self.bot_user_id}>", "").strip()

        if not text:
            return

        # Create IncomingMessage
        incoming = IncomingMessage(
            id=event.get("ts", ""),
            source=MessageSource.SLACK,
            sender_id=event.get("user", ""),
            sender_name=event.get("user", "Unknown"),
            channel_id=event.get("channel", ""),
            content=text,
            timestamp=datetime.now(),
            metadata={
                "thread_ts": event.get("thread_ts"),
                "channel_type": event.get("channel_type")
            }
        )

        if self._on_message_callback:
            try:
                await self._on_message_callback(incoming)
            except Exception as e:
                logger.error(f"Error processing Slack message: {e}")
                await say(
                    f"{self.persona_prefix}*wakes up suddenly* Eh wha? Something went wrong!",
                    thread_ts=event.get("thread_ts") or event.get("ts")
                )
        else:
            await say(
                f"{self.persona_prefix}You said: {text}\n\n"
<<<<<<< HEAD:cosmos/interfaces/messaging/slack_adapter.py
                "I'm running in standalone mode. Connect me to the full cosmos system!",
=======
                "I'm running in standalone mode. Connect me to the full Farnsworth system!",
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/interfaces/messaging/slack_adapter.py
                thread_ts=event.get("thread_ts") or event.get("ts")
            )

    async def disconnect(self):
        """Stop the Slack bot."""
        self._running = False
        if self.handler:
            await self.handler.close_async()
        logger.info("Slack bot disconnected")

    async def send_message(self, message: OutgoingMessage):
        """Send a message to Slack."""
        if not self.app:
            logger.error("Slack app not connected")
            return

        try:
<<<<<<< HEAD:cosmos/interfaces/messaging/slack_adapter.py
            # Add cosmos persona flavor
=======
            # Add Farnsworth persona flavor
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/interfaces/messaging/slack_adapter.py
            content = message.content
            if not content.startswith("_*"):
                content = self.persona_prefix + content

            # Determine if we should reply in a thread
            thread_ts = None
            if message.reply_to_id:
                thread_ts = message.reply_to_id

            await self.app.client.chat_postMessage(
                channel=message.channel_id,
                text=content,
                thread_ts=thread_ts,
                mrkdwn=True
            )
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")

    async def add_reaction(self, channel: str, timestamp: str, emoji: str = "brain"):
        """Add a reaction to a message."""
        if not self.app:
            return

        try:
            await self.app.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=emoji
            )
        except Exception as e:
            logger.debug(f"Failed to add reaction: {e}")


# Standalone runner for testing
async def run_standalone():
    """Run the Slack bot standalone for testing."""
    adapter = SlackAdapter()

    async def echo_handler(msg: IncomingMessage):
        """Simple echo handler for testing."""
        response = OutgoingMessage(
            channel_id=msg.channel_id,
            content=f"Good news, everyone! I received: {msg.content}",
            reply_to_id=msg.metadata.get("thread_ts") if msg.metadata else None
        )
        await adapter.send_message(response)

    adapter.set_callback(echo_handler)
    await adapter.connect()

    # Keep running
    while adapter._running:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run_standalone())
