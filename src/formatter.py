"""
Message formatting and Claude API integration for Monu OS v1.
"""

import anthropic
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import os

from .utils import logger, get_today_date

class OracleMessageFormatter:
    """
    Formats Hinglish Oracle messages using Claude API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the formatter.

        Args:
            api_key: Claude API key (optional, will use env var if not provided)
        """
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.client = None

        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info("Claude API client initialized")
        else:
            logger.warning("No Claude API key provided - will use fallback messages")

    def generate_oracle_message(self, prompt_inputs: Dict[str, Any]) -> str:
        """
        Generate Hinglish Oracle message using Claude API or fallback.

        Args:
            prompt_inputs: Dictionary containing prompt data

        Returns:
            Formatted Oracle message
        """
        try:
            if self.client:
                return self._generate_with_claude(prompt_inputs)
            else:
                logger.warning("Using fallback message generation")
                return self._generate_fallback_message(prompt_inputs)

        except Exception as e:
            logger.error(f"Error generating Oracle message: {str(e)}")
            return self._generate_fallback_message(prompt_inputs)

    def _generate_with_claude(self, prompt_inputs: Dict[str, Any]) -> str:
        """
        Generate message using Claude API.

        Args:
            prompt_inputs: Dictionary containing prompt data

        Returns:
            Generated message
        """
        # Load prompt template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'example_prompt_template.txt')

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            logger.warning("Prompt template not found, using default template")
            template = self._get_default_template()

        # Fill template with data
        prompt = self._fill_template(template, prompt_inputs)

        # Call Claude API
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0.7,
            system="You are a financial Oracle providing market insights in Hinglish (Hindi-English mix). Be informative, witty, and culturally relevant to Indian investors.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        message = response.content[0].text.strip()
        logger.info("Successfully generated Oracle message with Claude")
        return message

    def _generate_fallback_message(self, prompt_inputs: Dict[str, Any]) -> str:
        """
        Generate fallback message when Claude API is not available.

        Args:
            prompt_inputs: Dictionary containing prompt data

        Returns:
            Fallback message
        """
        date = prompt_inputs.get('date', get_today_date())
        symbols = prompt_inputs.get('symbols', [])
        top_gainer = prompt_inputs.get('top_gainer', 'N/A')
        top_loser = prompt_inputs.get('top_loser', 'N/A')
        volume_alerts = prompt_inputs.get('volume_alerts', [])

        message = f"""🌟 MONU OS v1 - Daily Market Oracle 🌟

📅 Date: {date}

📊 Market Summary:
• Total symbols tracked: {len(symbols)}
• Top Gainer: {top_gainer}
• Top Loser: {top_loser}
• High Volume Alerts: {', '.join(volume_alerts) if volume_alerts else 'None'}

💡 Oracle Wisdom:
"Markets are like monsoon - unpredictable but full of opportunity! Keep learning, keep investing wisely. 🚀"

⚠️ Note: This is an automated message. Claude API unavailable."""

        logger.info("Generated fallback Oracle message")
        return message

    def _fill_template(self, template: str, data: Dict[str, Any]) -> str:
        """
        Fill template with data.

        Args:
            template: Template string
            data: Data dictionary

        Returns:
            Filled template
        """
        filled = template

        # Basic replacements
        filled = filled.replace('{date}', data.get('date', get_today_date()))
        filled = filled.replace('{symbol_list}', ', '.join(data.get('symbols', [])))

        # Top gainer/loser
        gainers = data.get('gainers', [])
        losers = data.get('losers', [])

        top_gainer = gainers[0][0] if gainers else 'N/A'
        top_loser = losers[0][0] if losers else 'N/A'

        filled = filled.replace('{top_gainer}', top_gainer)
        filled = filled.replace('{top_loser}', top_loser)

        # Volume alerts
        volume_alerts = [symbol for symbol, _ in data.get('high_volume', [])]
        filled = filled.replace('{top_volume_alerts}', ', '.join(volume_alerts) if volume_alerts else 'None')

        # Indicator table
        indicator_table = self._create_indicator_table(data.get('symbol_data', {}))
        filled = filled.replace('{per_symbol_indicator_table}', indicator_table)

        return filled

    def _create_indicator_table(self, symbol_data: Dict[str, Dict]) -> str:
        """
        Create formatted indicator table.

        Args:
            symbol_data: Dictionary with symbol data

        Returns:
            Formatted table string
        """
        if not symbol_data:
            return "No data available"

        table_lines = ["📈 Symbol Indicators:"]
        table_lines.append("-" * 50)

        for symbol, data in symbol_data.items():
            indicators = data.get('indicators', {})
            table_lines.append(f"🔹 {symbol}:")
            table_lines.append(f"   • Price Change: {indicators.get('pct_change', 0):.2f}%")
            table_lines.append(f"   • Volume Change: {indicators.get('vol_change_pct', 0):.2f}%")
            table_lines.append(f"   • EMA 20: {indicators.get('ema_20', 0):.2f}")
            table_lines.append(f"   • RSI 14: {indicators.get('rsi_14', 0):.2f}")
            table_lines.append(f"   • Recent High: {indicators.get('recent_high', 0):.2f}")
            table_lines.append(f"   • Recent Low: {indicators.get('recent_low', 0):.2f}")
            table_lines.append("")

        return "\n".join(table_lines)

    def _get_default_template(self) -> str:
        """
        Get default prompt template.

        Returns:
            Default template string
        """
        return """You are the MONU OS v1 Market Oracle, providing daily market insights in Hinglish (mix of Hindi and English) for Indian investors.

📅 Date: {date}
📊 Symbols Tracked: {symbol_list}

🏆 Market Highlights:
• Top Gainer: {top_gainer}
• Top Loser: {top_loser}
• Volume Alerts: {top_volume_alerts}

📈 Detailed Indicators:
{per_symbol_indicator_table}

Please provide a witty, informative Oracle message in Hinglish that:
1. Summarizes the market mood
2. Highlights key movements
3. Gives cultural investment wisdom
4. Keeps it under 800 characters
5. Uses emojis appropriately
6. Is engaging and fun to read

Format as a single cohesive message starting with "🌟 MONU OS v1 - Daily Market Oracle 🌟"."""

    def create_prompt_inputs(self, symbol_data: Dict[str, Dict],
                           market_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create prompt inputs from symbol data and market summary.

        Args:
            symbol_data: Dictionary with symbol data
            market_summary: Market summary dictionary

        Returns:
            Prompt inputs dictionary
        """
        return {
            'date': get_today_date(),
            'symbols': list(symbol_data.keys()),
            'gainers': market_summary.get('gainers', []),
            'losers': market_summary.get('losers', []),
            'high_volume': market_summary.get('high_volume', []),
            'symbol_data': symbol_data,
            'top_gainer': market_summary.get('gainers', [[]])[0][0] if market_summary.get('gainers') else 'N/A',
            'top_loser': market_summary.get('losers', [[]])[0][0] if market_summary.get('losers') else 'N/A',
            'volume_alerts': [symbol for symbol, _ in market_summary.get('high_volume', [])]
        }
