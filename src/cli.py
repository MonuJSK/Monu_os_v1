"""
Command-line interface for Monu OS v1 market update pipeline.
"""

import argparse
import sys
from typing import Optional
import logging

from .utils import logger, validate_config, get_today_date
from .fetcher import MarketDataFetcher
from .sheets import GoogleSheetsManager
from .formatter import OracleMessageFormatter
from .notifier import TelegramNotifier

class MonuOSCLI:
    """
    Command-line interface for Monu OS v1.
    """

    def __init__(self):
        """Initialize CLI."""
        self.config = None
        self.fetcher = None
        self.sheets = None
        self.formatter = None
        self.notifier = None

    def setup_components(self) -> bool:
        """
        Setup all components with configuration.

        Returns:
            True if setup successful, False otherwise
        """
        try:
            self.config = validate_config()

            # Initialize components
            self.fetcher = MarketDataFetcher(
                self.config['tvdata_username'],
                self.config['tvdata_password']
            )

            self.sheets = GoogleSheetsManager(
                self.config['google_sa_json_path'],
                self.config['sheets_id']
            )

            self.formatter = OracleMessageFormatter(
                self.config.get('claude_api_key')
            )

            self.notifier = TelegramNotifier(
                self.config['telegram_bot_token'],
                self.config['telegram_chat_id']
            )

            logger.info("All components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to setup components: {str(e)}")
            return False

    def run_daily_pipeline(self) -> bool:
        """
        Run the complete daily market update pipeline.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting daily market update pipeline")

            # Fetch market data
            symbol_data = self.fetcher.fetch_all_symbols()
            if not symbol_data:
                logger.error("No symbol data fetched, aborting pipeline")
                self.notifier.send_error_notification(
                    "Data fetching failed",
                    "Unable to fetch market data for any symbols"
                )
                return False

            # Generate market summary
            market_summary = self.fetcher.get_market_summary(symbol_data)

            # Store raw data in Google Sheets
            raw_stored = 0
            for symbol, data in symbol_data.items():
                indicators = data['indicators']
                # Get latest OHLCV data
                latest_data = data['data'].iloc[-1] if not data['data'].empty else {}

                row = {
                    'open': latest_data.get('open', 0),
                    'high': latest_data.get('high', 0),
                    'low': latest_data.get('low', 0),
                    'close': latest_data.get('close', 0),
                    'volume': latest_data.get('volume', 0),
                    **indicators
                }

                if self.sheets.append_raw(symbol, row):
                    raw_stored += 1

            logger.info(f"Stored raw data for {raw_stored}/{len(symbol_data)} symbols")

            # Update summary in Google Sheets
            today = get_today_date()
            summary_stored = self.sheets.update_summary(today, market_summary)

            # Generate Oracle message
            prompt_inputs = self.formatter.create_prompt_inputs(symbol_data, market_summary)
            oracle_message = self.formatter.generate_oracle_message(prompt_inputs)

            # Send notification
            notification_sent = self.notifier.send_message(
                self.notifier.format_market_message(oracle_message)
            )

            # Log results
            success_msg = f"Pipeline completed: {len(symbol_data)} symbols processed, {raw_stored} raw records stored, summary {'stored' if summary_stored else 'failed'}, notification {'sent' if notification_sent else 'failed'}"
            logger.info(success_msg)

            if notification_sent:
                self.notifier.send_success_notification("Daily pipeline completed", success_msg)

            return True

        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            logger.error(error_msg)
            if self.notifier:
                self.notifier.send_error_notification("Pipeline execution failed", str(e))
            return False

    def test_connections(self) -> bool:
        """
        Test all external connections.

        Returns:
            True if all tests pass, False otherwise
        """
        tests = []

        # Test Google Sheets
        try:
            sheets_ok = self.sheets.initialize_sheets()
            tests.append(("Google Sheets", sheets_ok))
        except Exception as e:
            logger.error(f"Google Sheets test failed: {str(e)}")
            tests.append(("Google Sheets", False))

        # Test Telegram
        try:
            telegram_ok = self.notifier.test_connection()
            tests.append(("Telegram", telegram_ok))
        except Exception as e:
            logger.error(f"Telegram test failed: {str(e)}")
            tests.append(("Telegram", False))

        # Test TradingView Data (fetch small amount)
        try:
            test_data = self.fetcher.fetch_symbol_data('NIFTY', 'NSE', n_bars=5)
            tv_ok = test_data is not None and not test_data.empty
            tests.append(("TradingView Data", tv_ok))
        except Exception as e:
            logger.error(f"TradingView test failed: {str(e)}")
            tests.append(("TradingView Data", False))

        # Log results
        all_passed = True
        for service, passed in tests:
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{service}: {status}")
            if not passed:
                all_passed = False

        return all_passed

    def run(self, args: Optional[list] = None) -> int:
        """
        Main CLI entry point.

        Args:
            args: Command line arguments

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        parser = argparse.ArgumentParser(
            description="Monu OS v1 - Automated Daily Market Update Pipeline"
        )

        parser.add_argument(
            'command',
            choices=['run', 'test', 'daily'],
            help='Command to execute'
        )

        parser.add_argument(
            '--daily',
            action='store_true',
            help='Run daily pipeline (same as "run daily")'
        )

        parser.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            default='INFO',
            help='Set logging level'
        )

        if args is None:
            args = sys.argv[1:]

        parsed_args = parser.parse_args(args)

        # Set log level
        from .utils import setup_logging
        setup_logging(parsed_args.log_level)

        logger.info(f"Monu OS v1 CLI started with command: {parsed_args.command}")

        # Setup components
        if not self.setup_components():
            logger.error("Component setup failed, exiting")
            return 1

        # Execute command
        if parsed_args.command in ['run', 'daily'] or parsed_args.daily:
            success = self.run_daily_pipeline()
        elif parsed_args.command == 'test':
            success = self.test_connections()
            if success:
                logger.info("All connection tests passed!")
            else:
                logger.error("Some connection tests failed!")
        else:
            logger.error(f"Unknown command: {parsed_args.command}")
            return 1

        return 0 if success else 1

def main():
    """Main entry point."""
    cli = MonuOSCLI()
    sys.exit(cli.run())

if __name__ == "__main__":
    main()
