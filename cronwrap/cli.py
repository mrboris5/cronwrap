"""CLI entry point for cronwrap."""
import argparse
import sys

from cronwrap.config import Config, from_file
from cronwrap.logger import setup_logging
from cronwrap.runner import run_command
from cronwrap.alerting import AlertConfig, send_alert


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap",
        description="Wrap cron jobs with logging, alerting, and retry support.",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run")
    parser.add_argument("-c", "--config", default=None, help="Path to config file")
    parser.add_argument("-r", "--retries", type=int, default=None, help="Number of retries")
    parser.add_argument("-t", "--timeout", type=int, default=None, help="Timeout in seconds")
    parser.add_argument("--log-level", default=None, dest="log_level", help="Logging level")
    parser.add_argument("--log-file", default=None, dest="log_file", help="Log file path")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Load config from file or defaults
    if args.config:
        cfg = from_file(args.config)
    else:
        cfg = Config()

    # CLI overrides
    if args.retries is not None:
        cfg.retries = args.retries
    if args.timeout is not None:
        cfg.timeout = args.timeout
    if args.log_level is not None:
        cfg.log_level = args.log_level
    if args.log_file is not None:
        cfg.log_file = args.log_file

    command = args.command
    if not command:
        parser.print_help()
        return 1

    # Strip leading '--' separator if present
    if command and command[0] == "--":
        command = command[1:]

    logger = setup_logging(level=cfg.log_level, log_file=cfg.log_file)
    logger.info("cronwrap starting: %s", " ".join(command))

    result = run_command(command, timeout=cfg.timeout, retries=cfg.retries)

    if result.success:
        logger.info("Command succeeded in %.2fs", result.duration)
    else:
        logger.error(
            "Command failed (exit %s) after %.2fs\n%s",
            result.returncode,
            result.duration,
            result.stderr or result.stdout,
        )

    alert_cfg = AlertConfig(
        enabled=cfg.alert_on_failure and not result.success,
        recipients=cfg.alert_recipients,
        smtp_host=cfg.smtp_host,
        smtp_port=cfg.smtp_port,
        sender=cfg.alert_sender,
    )
    send_alert(alert_cfg, result, " ".join(command))

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
