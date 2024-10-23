#!/usr/bin/env python
import argparse
import os
import json


def init_loop() -> None:
    config = {}

    config["paper_path"] = os.path.expandvars("$HOME/Desktop/reading_list/")
    default_paper_path = config["paper_path"]
    paper_path = input(
        f"Where do you want the papers be stored? ({default_paper_path}) ")
    if paper_path != "" and paper_path != default_paper_path:
        config["paper_path"] = paper_path

    str = json.dumps(config)
    print(str)


def init(args: argparse.Namespace) -> None:
    print(f"Initializing porg: The config file will be stored at {args.config}")
    if os.path.exists(args.config):
        print("[WARNING] Config file exists. Abort to prevent overriding")
    init_loop()


def main():
    config_path = os.path.expandvars('$HOME/.porgconfig.json')

    parser = argparse.ArgumentParser(
        description="Download a paper and add an entry Notion")
    parser.add_argument("--init", action="store_true", help="Initialize porg")
    parser.add_argument("-c", "--config", default=config_path,
        help="When initializing, this is where the config will be stored. " + \
             "When running porg, this is where the config will be read.")
    args = parser.parse_args()
    if args.init:
        init(args)


if __name__ == "__main__":
    main()
