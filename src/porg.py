#!/usr/bin/env python
import argparse
import os
import urllib.request
import urllib.parse
from pathlib import Path
from src.notion import setup_notion, add_paper
from src.papers import add_paper_complete, sync_papers


def download_paper(url: str, filename: str = None) -> None:
    if not url.startswith(('http://', 'https://')):
        print("Error: URL must start with http:// or https://")
        return
    
    download_dir = Path.home() / "Desktop/quick_reads"
    download_dir.mkdir(exist_ok=True)
    
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
