import argparse
import os
import sys

from attack3_hud import Attack3Controller, Attack3HUD, Calibration


def main():
    parser = argparse.ArgumentParser(
        description="Logitech Attack 3 joystick diagnostics HUD."
    )
    parser.add_argument(
        "--config",
        "-c",
        help="Path to a calibration JSON file to load and save button renames.",
    )
    parser.add_argument(
        "--index",
        "-i",
        type=int,
        default=0,
        help="Joystick index to attach to (default: 0).",
    )
    args = parser.parse_args()

    calibration = None
    if args.config and os.path.exists(args.config):
        calibration = Calibration.from_file(args.config)

    try:
        controller = Attack3Controller(calibration=calibration, index=args.index)
    except RuntimeError as exc:
        print(exc)
        sys.exit(1)

    hud = Attack3HUD(controller=controller, config_path=args.config)
    hud.run()


if __name__ == "__main__":
    main()
