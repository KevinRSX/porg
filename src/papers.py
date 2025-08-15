#!/usr/bin/env python
import json
from pathlib import Path
from typing import Dict, List


def get_config_dir() -> Path:
    """Get the porg configuration directory."""
    return Path.home() / ".porg"


def get_papers_config_path() -> Path:
    """Get the path to papers metadata file."""
    return get_config_dir() / "papers.json"


def ensure_config_dir() -> None:
    """Ensure the config directory exists."""
    config_dir = get_config_dir()
    config_dir.mkdir(exist_ok=True)


def load_papers_metadata() -> Dict:
    """Load papers metadata from papers.json."""
    papers_path = get_papers_config_path()
    if papers_path.exists():
        with open(papers_path, 'r') as f:
            return json.load(f)
    return {"papers": []}


def save_papers_metadata(papers_data: Dict) -> None:
    """Save papers metadata to papers.json."""
    ensure_config_dir()
    papers_path = get_papers_config_path()
    with open(papers_path, 'w') as f:
        json.dump(papers_data, f, indent=2)


def generate_conventional_name(codename: str, conference: str) -> str:
    """Generate conventional name in format <codename>-<conference>."""
    # Clean the inputs to make valid filenames
    clean_codename = codename.lower().replace(' ', '-').replace('_', '-')
    clean_conference = conference.lower().replace(' ', '').replace('-', '')
    return f"{clean_codename}-{clean_conference}"


def add_paper_metadata(url: str = None) -> dict:
    """Add paper metadata by prompting user for required fields. Returns paper metadata dict."""
    print("Adding paper metadata...")
    print("Please provide the following information:")
    
    # Prompt for codename
    print("\n1. Paper's formal title/codename (e.g., 'DistServe', 'Attention Is All You Need'):")
    codename = input("Codename: ").strip()
    if not codename:
        print("Error: Codename cannot be empty")
        return None
    
    print("\n2. Conference information (e.g., 'OSDI 2024', 'NeurIPS 2017', 'ArXiv'):")
    conference = input("Conference: ").strip()
    if not conference:
        print("Error: Conference cannot be empty")
        return None
    
    # Use provided URL or prompt for it
    if url is None:
        print("\n3. Paper URL (e.g., 'https://arxiv.org/pdf/2506.24045'):")
        url = input("URL: ").strip()
        if not url:
            print("Error: URL cannot be empty")
            return None
        prompt_num = 4
    else:
        print(f"\n3. Using provided URL: {url}")
        prompt_num = 3
    
    # Generate conventional name
    conventional_name = generate_conventional_name(codename, conference)
    print(f"\n{prompt_num}. Generated conventional name: {conventional_name}")
    custom_name = input("Press Enter to use this name, or type a custom name: ").strip()
    if custom_name:
        conventional_name = custom_name
    
    # Create paper metadata dict
    paper_metadata = {
        "conventional_name": conventional_name,
        "url": url,
        "codename": codename,
        "conference": conference
    }
    
    return paper_metadata


def save_paper_metadata(paper_metadata: dict) -> bool:
    """Save a single paper's metadata to the papers file."""
    # Load existing papers and add new one
    papers_data = load_papers_metadata()
    
    # Check if paper already exists (by codename or conventional name)
    existing_paper = None
    for paper in papers_data["papers"]:
        if (paper["codename"].lower() == paper_metadata["codename"].lower() or 
            paper["conventional_name"].lower() == paper_metadata["conventional_name"].lower()):
            existing_paper = paper
            break
    
    if existing_paper:
        print(f"\n⚠️  Paper already exists:")
        print(f"   Codename: {existing_paper['codename']}")
        print(f"   Conventional name: {existing_paper['conventional_name']}")
        print(f"   Conference: {existing_paper['conference']}")
        
        confirm = input("Do you want to update it? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Operation cancelled.")
            return False
        
        # Update existing paper
        papers_data["papers"] = [p for p in papers_data["papers"] if p != existing_paper]
        papers_data["papers"].append(paper_metadata)
        print("✅ Paper metadata updated!")
    else:
        # Add new paper
        papers_data["papers"].append(paper_metadata)
        print("✅ Paper metadata added!")
    
    # Save to file
    save_papers_metadata(papers_data)
    print(f"📝 Saved to: {get_papers_config_path()}")
    
    return True


def add_paper_complete(url: str) -> None:
    """Complete workflow: add metadata, download paper, and add to Notion."""
    from src.notion import add_paper
    import sys
    import os
    import urllib.request
    import urllib.parse
    from pathlib import Path
    
    # Step 1: Add paper metadata
    paper_metadata = add_paper_metadata(url)
    if not paper_metadata:
        return
    
    # Save metadata
    if not save_paper_metadata(paper_metadata):
        return
    
    # Display summary
    print(f"\nPaper Summary:")
    print(f"   Conventional name: {paper_metadata['conventional_name']}")
    print(f"   Codename: {paper_metadata['codename']}")
    print(f"   Conference: {paper_metadata['conference']}")
    print(f"   URL: {paper_metadata['url']}")
    
    # Step 2: Download paper
    print(f"\n📥 Downloading paper...")
    download_dir = Path.home() / "Desktop/quick_reads"
    download_dir.mkdir(exist_ok=True)
    
    filename = f"{paper_metadata['conventional_name']}.pdf"
    filepath = download_dir / filename
    
    download_successful = False
    if filepath.exists():
        print(f"File already exists: {filepath}")
        download_successful = True
    else:
        try:
            print(f"Downloading to: {filepath}")
            urllib.request.urlretrieve(url, filepath)
            print(f"✅ Successfully downloaded: {filepath}")
            download_successful = True
        except Exception as e:
            print(f"❌ Error downloading paper: {e}")
            print("⚠️  Download failed, but continuing with Notion integration...")
    
    # Step 3: Add to Notion
    print(f"\n📝 Adding to Notion...")
    notion_title = f"{paper_metadata['codename']} ({paper_metadata['conference']})"
    try:
        add_paper(notion_title, url, paper_metadata['conventional_name'])
        notion_successful = True
    except Exception as e:
        print(f"❌ Error adding to Notion: {e}")
        notion_successful = False
    
    # Final status summary
    print(f"\n📊 Process Summary:")
    print(f"   ✅ Metadata saved: Yes")
    print(f"   {'✅' if download_successful else '❌'} Download: {'Success' if download_successful else 'Failed'}")
    print(f"   {'✅' if notion_successful else '❌'} Notion integration: {'Success' if notion_successful else 'Failed'}")
    
    if not download_successful:
        print(f"\n💡 Note: You may need to manually download the paper from: {url}")
        print(f"   Save it as: {filepath}")
    
    if download_successful and notion_successful:
        print(f"\n🎉 Paper successfully added to your research collection!")


def sync_papers() -> None:
    """Sync papers from config to downloads and Notion."""
    from src.notion import add_paper, check_paper_exists_in_notion
    import urllib.request
    
    print("🔄 Starting paper synchronization...")
    
    # Load papers from config
    papers_data = load_papers_metadata()
    papers = papers_data.get('papers', [])
    
    if not papers:
        print("📭 No papers found in configuration file.")
        return
    
    print(f"📋 Found {len(papers)} papers in configuration")
    
    # Set up paths
    download_dir = Path.home() / "Desktop/quick_reads"
    download_dir.mkdir(exist_ok=True)
    
    # Track sync progress
    missing_downloads = []
    missing_notion = []
    download_failures = []
    notion_failures = []
    
    # Check each paper
    for paper in papers:
        conventional_name = paper['conventional_name']
        codename = paper['codename']
        conference = paper['conference']
        url = paper['url']
        
        print(f"\n📄 Checking: {conventional_name}")
        
        # Check if file exists
        filename = f"{conventional_name}.pdf"
        filepath = download_dir / filename
        
        if not filepath.exists():
            missing_downloads.append(paper)
            print(f"   📥 Missing download")
        else:
            print(f"   ✅ File exists")
        
        # Check if Notion entry exists
        if not check_paper_exists_in_notion(conventional_name):
            missing_notion.append(paper)
            print(f"   📝 Missing Notion entry")
        else:
            print(f"   ✅ Notion entry exists")
    
    # Summary of what needs to be synced
    print(f"\n📊 Sync Summary:")
    print(f"   Missing downloads: {len(missing_downloads)}")
    print(f"   Missing Notion entries: {len(missing_notion)}")
    
    if not missing_downloads and not missing_notion:
        print("\n🎉 Everything is already in sync!")
        return
    
    # Download missing files
    if missing_downloads:
        print(f"\n📥 Downloading {len(missing_downloads)} missing files...")
        for paper in missing_downloads:
            conventional_name = paper['conventional_name']
            url = paper['url']
            filename = f"{conventional_name}.pdf"
            filepath = download_dir / filename
            
            try:
                print(f"   Downloading {conventional_name}...")
                urllib.request.urlretrieve(url, filepath)
                print(f"   ✅ Downloaded: {filename}")
            except Exception as e:
                print(f"   ❌ Failed to download {conventional_name}: {e}")
                download_failures.append(paper)
    
    # Add missing Notion entries
    if missing_notion:
        print(f"\n📝 Adding {len(missing_notion)} missing Notion entries...")
        for paper in missing_notion:
            conventional_name = paper['conventional_name']
            codename = paper['codename']
            conference = paper['conference']
            url = paper['url']
            
            notion_title = f"{codename} ({conference})"
            
            try:
                print(f"   Adding to Notion: {conventional_name}")
                add_paper(notion_title, url, conventional_name)
                print(f"   ✅ Added to Notion: {notion_title}")
            except Exception as e:
                print(f"   ❌ Failed to add {conventional_name} to Notion: {e}")
                notion_failures.append(paper)
    
    # Final summary
    print(f"\n📊 Sync Results:")
    print(f"   ✅ Downloads completed: {len(missing_downloads) - len(download_failures)}")
    print(f"   ❌ Download failures: {len(download_failures)}")
    print(f"   ✅ Notion entries added: {len(missing_notion) - len(notion_failures)}")
    print(f"   ❌ Notion failures: {len(notion_failures)}")
    
    if download_failures:
        print(f"\n⚠️  Download failures:")
        for paper in download_failures:
            print(f"   - {paper['conventional_name']}: {paper['url']}")
    
    if notion_failures:
        print(f"\n⚠️  Notion failures:")
        for paper in notion_failures:
            print(f"   - {paper['conventional_name']}")
    
    if not download_failures and not notion_failures:
        print(f"\n🎉 Sync completed successfully!")


