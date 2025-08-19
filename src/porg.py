#!/usr/bin/env python
import argparse
import os
import urllib.request
import urllib.parse
from pathlib import Path
from src.notion import setup_notion, add_paper
from src.papers import add_paper_complete, sync_papers, open_paper, flush_papers, get_paper_info, get_papers_by_project_filter, get_papers_by_topic_filter, get_all_papers_list


def download_paper(url: str, filename: str = None) -> None:
    if not url.startswith(('http://', 'https://')):
        print("Error: URL must start with http:// or https://")
        return
    
    from src.papers import get_download_dir
    download_dir = get_download_dir()
    download_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        filename = input("Enter filename (without .pdf extension): ").strip()
        if not filename:
            print("Error: Filename cannot be empty")
            return
    
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    
    filepath = download_dir / filename
    
    if filepath.exists():
        print(f"File already exists: {filepath}")
        return
    
    print(f"Downloading paper from {url}")
    print(f"Saving to {filepath}")
    
    try:
        urllib.request.urlretrieve(url, filepath)
        print(f"Successfully downloaded: {filepath}")
    except urllib.error.URLError as e:
        print(f"Error downloading paper: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Download and organize research papers")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add command (top-level)
    add_parser = subparsers.add_parser('add', help='Add paper (metadata + download + Notion)')
    add_parser.add_argument('url', help='URL of the paper to add')
    
    # Sync command (top-level)
    sync_parser = subparsers.add_parser('sync', help='Sync papers from config to downloads and Notion')
    
    # Open command (top-level)
    open_parser = subparsers.add_parser('open', help='Open a paper by codename')
    open_parser.add_argument('name', help='Paper codename to open')
    
    # Flush command (top-level)
    flush_parser = subparsers.add_parser('flush', help='Flush papers from download_dir to archive_dir')
    flush_parser.add_argument('names', nargs='+', help='Paper codenames to flush')
    
    # Get command (top-level)
    get_parser = subparsers.add_parser('get', help='Query paper information from Notion')
    get_group = get_parser.add_mutually_exclusive_group(required=False)
    get_group.add_argument('--name', help='Paper codename to get info for')
    get_group.add_argument('--project', help='Project name to filter papers by')
    get_group.add_argument('--topic', help='Topic name to filter papers by')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download a research paper')
    download_parser.add_argument("--url", required=True, help="URL of the paper to download")
    download_parser.add_argument("--file", "-f", help="Custom filename for the downloaded paper (without .pdf extension)")
    
    # Notion command
    notion_parser = subparsers.add_parser('notion', help='Notion integration commands')
    notion_parser.add_argument('--setup', action='store_true', help='Set up Notion integration')
    notion_parser.add_argument('--add', action='store_true', help='Add a paper to Notion database')
    notion_parser.add_argument('--name', help='Paper name (required with --add)')
    notion_parser.add_argument('--url', help='Paper URL (optional with --add)')
    
    args = parser.parse_args()
    
    if args.command == "add":
        add_paper_complete(args.url)
    elif args.command == "sync":
        sync_papers()
    elif args.command == "open":
        open_paper(args.name)
    elif args.command == "flush":
        flush_papers(args.names)
    elif args.command == "get":
        if args.name:
            get_paper_info(args.name)
        elif args.project:
            get_papers_by_project_filter(args.project)
        elif args.topic:
            get_papers_by_topic_filter(args.topic)
        else:
            get_all_papers_list()
    elif args.command == "download":
        download_paper(args.url, args.file)
    elif args.command == "notion":
        if args.setup:
            setup_notion()
        elif args.add:
            if not args.name:
                print("Error: --name is required when using --add")
                notion_parser.print_help()
                return
            add_paper(args.name, args.url)
        else:
            notion_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
