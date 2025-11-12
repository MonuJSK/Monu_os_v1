"""
Telegram notification module for Monu OS v1.
"""

import requests
from typing import Optional
import logging

from .utils import logger

class TelegramNotifier:
    """
    Handles Telegram bot notifications.
    """

    BASE_URL = "https://api.telegram.org/bot"

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"{self.BASE_URL}{bot_token}"
        logger.info("Telegram notifier initialized")

    def send_message(self, message: str) -> bool:
        """
        Send a message to the Telegram channel.

        Args:
            message: Message to send

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }

            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            if result.get('ok'):
                logger.info("Successfully sent Telegram message")
                return True
            else:
                logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {str(e)}")
            return False

    def send_formatted_message(self, title: str, content: str,
                             footer: Optional[str] = None) -> bool:
        """
        Send a formatted message with title, content, and optional footer.

        Args:
            title: Message title
            content: Main content
            footer: Optional footer text

        Returns:
            True if successful, False otherwise
        """
        try:
            full_message = f"<b>{title}</b>\n\n{content}"

            if footer:
                full_message += f"\n\n<i>{footer}</i>"

            return self.send_message(full_message)

        except Exception as e:
            logger.error(f"Failed to send formatted message: {str(e)}")
            return False

    def test_connection(self) -> bool:
        """
        Test Telegram bot connection.

        Returns:
            True if connection is working, False otherwise
        """
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get('ok'):
                bot_info = result.get('result', {})
                logger.info(f"Telegram connection test successful. Bot: {bot_info.get('username', 'Unknown')}")
                return True
            else:
                logger.error(f"Telegram connection test failed: {result.get('description', 'Unknown error')}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram connection test failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing Telegram connection: {str(e)}")
            return False

    def send_error_notification(self, error_message: str, context: Optional[str] = None) -> bool:
        """
        Send error notification.

        Args:
            error_message: Error message
            context: Optional context information

        Returns:
            True if successful, False otherwise
        """
        try:
            title = "🚨 MONU OS v1 - Error Alert"
            content = f"❌ <b>Error:</b> {error_message}"

            if context:
                content += f"\n\n📋 <b>Context:</b> {context}"

            content += "\n\n🔧 Please check logs for more details."

            return self.send_formatted_message(title, content)

        except Exception as e:
            logger.error(f"Failed to send error notification: {str(e)}")
            return False

    def send_success_notification(self, operation: str, details: Optional[str] = None) -> bool:
        """
        Send success notification.

        Args:
            operation: Operation that succeeded
            details: Optional details

        Returns:
            True if successful, False otherwise
        """
        try:
            title = "✅ MONU OS v1 - Success"
            content = f"✅ <b>Operation completed:</b> {operation}"

            if details:
                content += f"\n\n📊 <b>Details:</b> {details}"

            return self.send_formatted_message(title, content)

        except Exception as e:
            logger.error(f"Failed to send success notification: {str(e)}")
            return False

    def format_market_message(self, oracle_message: str) -> str:
        """
        Format market Oracle message for Telegram.

        Args:
            oracle_message: Raw Oracle message

        Returns:
            Formatted message for Telegram
        """
        # Telegram supports basic HTML formatting
        # Convert markdown-style formatting to HTML if needed
        formatted = oracle_message.replace('**', '<b>').replace('**', '</b>')
        formatted = formatted.replace('*', '<i>').replace('*', '</i>')
        formatted = formatted.replace('`', '<code>').replace('`', '</code>')

        return formatted
