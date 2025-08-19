#!/usr/bin/env python
import json
import yaml
from pathlib import Path
from typing import Dict, List

from src.icons import SUCCESS, ERROR, WARNING


def get_config_dir() -> Path:
    """Get the porg configuration directory."""
    return Path.home() / ".porg"


def get_papers_config_path() -> Path:
    """Get the path to papers metadata file."""
    return get_config_dir() / "papers.json"


def get_config_path() -> Path:
    """Get the path to main config file."""
    return get_config_dir() / "config.yaml"


def load_config() -> Dict:
    """Load configuration from config.yaml."""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {
        "download_dir": "~/Desktop/quick_reads",
        "archive_dir": "~/Desktop/Readings/Papers/General",
    }


def get_download_dir() -> Path:
    """Get the configured download directory."""
    config = load_config()
    return Path(config["download_dir"]).expanduser()


def get_archive_dir() -> Path:
    """Get the configured archive directory."""
    config = load_config()
    return Path(config["archive_dir"]).expanduser()


def ensure_config_dir() -> None:
    """Ensure the config directory exists."""
    config_dir = get_config_dir()
    config_dir.mkdir(exist_ok=True)


def load_papers_metadata() -> Dict:
    """Load papers metadata from papers.json."""
    papers_path = get_papers_config_path()
    if papers_path.exists():
        with open(papers_path) as f:
            return json.load(f)
    return {"papers": []}


def save_papers_metadata(papers_data: Dict) -> None:
    """Save papers metadata to papers.json."""
    ensure_config_dir()
    papers_path = get_papers_config_path()
    with open(papers_path, "w") as f:
        json.dump(papers_data, f, indent=2)


def generate_conventional_name(codename: str, conference: str) -> str:
    """Generate conventional name in format <codename>-<conference>."""
    # Clean the inputs to make valid filenames
    clean_codename = codename.lower().replace(" ", "-").replace("_", "-")
    clean_conference = conference.lower().replace(" ", "").replace("-", "")
    return f"{clean_codename}-{clean_conference}"


def add_paper_metadata(url: str = None) -> dict:
    """Add paper metadata by prompting user for required fields.

    Returns paper metadata dict.
    """
    print("Adding paper metadata...")
    print("Please provide the following information:")

    # Prompt for codename
    print(
        "\n1. Paper's formal title/codename "
        "(e.g., 'DistServe', 'Attention Is All You Need'):"
    )
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
        "conference": conference,
    }

    return paper_metadata


def save_paper_metadata(paper_metadata: dict) -> bool:
    """Save a single paper's metadata to the papers file."""
    # Load existing papers and add new one
    papers_data = load_papers_metadata()

    # Check if paper already exists (by codename or conventional name)
    existing_paper = None
    for paper in papers_data["papers"]:
        if (
            paper["codename"].lower() == paper_metadata["codename"].lower()
            or paper["conventional_name"].lower()
            == paper_metadata["conventional_name"].lower()
        ):
            existing_paper = paper
            break

    if existing_paper:
        print(f"\n{WARNING} Paper already exists:")
        print(f"   Codename: {existing_paper['codename']}")
        print(f"   Conventional name: {existing_paper['conventional_name']}")
        print(f"   Conference: {existing_paper['conference']}")

        confirm = input("Do you want to update it? (y/N): ").strip().lower()
        if confirm not in ["y", "yes"]:
            print("Operation cancelled.")
            return False

        # Update existing paper
        papers_data["papers"] = [
            p for p in papers_data["papers"] if p != existing_paper
        ]
        papers_data["papers"].append(paper_metadata)
        print(f"{SUCCESS} Paper metadata updated!")
    else:
        # Add new paper
        papers_data["papers"].append(paper_metadata)
        print(f"{SUCCESS} Paper metadata added!")

    # Save to file
    save_papers_metadata(papers_data)
    print(f"Saved to: {get_papers_config_path()}")

    return True


def add_paper_complete(url: str) -> None:
    """Complete workflow: add metadata, download paper, and add to Notion."""
    from src.notion import add_paper
    import urllib.request
    import urllib.parse

    # Step 1: Add paper metadata
    paper_metadata = add_paper_metadata(url)
    if not paper_metadata:
        return

    # Save metadata
    if not save_paper_metadata(paper_metadata):
        return

    # Display summary
    print("\nPaper Summary:")
    print(f"   Conventional name: {paper_metadata['conventional_name']}")
    print(f"   Codename: {paper_metadata['codename']}")
    print(f"   Conference: {paper_metadata['conference']}")
    print(f"   URL: {paper_metadata['url']}")

    # Step 2: Download paper
    print("\nDownloading paper...")
    download_dir = get_download_dir()
    download_dir.mkdir(parents=True, exist_ok=True)

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
            print(f"{SUCCESS} Successfully downloaded: {filepath}")
            download_successful = True
        except Exception as e:
            print(f"{ERROR} Error downloading paper: {e}")
            print(f"{WARNING} Download failed, but continuing with Notion integration...")

    # Step 3: Add to Notion
    print("\nAdding to Notion...")
    notion_title = f"{paper_metadata['codename']} ({paper_metadata['conference']})"
    try:
        add_paper(notion_title, url, paper_metadata["conventional_name"])
        notion_successful = True
    except Exception as e:
        print(f"{ERROR} Error adding to Notion: {e}")
        notion_successful = False

    # Final status summary
    print("\nProcess Summary:")
    print(f"   {SUCCESS} Metadata saved: Yes")
    download_status = "Success" if download_successful else "Failed"
    download_icon = SUCCESS if download_successful else ERROR
    print(f"   {download_icon} Download: {download_status}")
    notion_status = "Success" if notion_successful else "Failed"
    notion_icon = SUCCESS if notion_successful else ERROR
    print(f"   {notion_icon} Notion integration: {notion_status}")

    if not download_successful:
        print(f"\nNote: You may need to manually download the paper from: {url}")
        print(f"   Save it as: {filepath}")

    if download_successful and notion_successful:
        print("\nPaper successfully added to your research collection!")


def sync_papers() -> None:
    """Sync papers from config to downloads and Notion."""
    from src.notion import add_paper, check_paper_exists_in_notion
    import urllib.request

    print("Starting paper synchronization...")

    # Load papers from config
    papers_data = load_papers_metadata()
    papers = papers_data.get("papers", [])

    if not papers:
        print("No papers found in configuration file.")
        return

    print(f"Found {len(papers)} papers in configuration")

    # Set up paths
    download_dir = get_download_dir()
    download_dir.mkdir(parents=True, exist_ok=True)

    # Track sync progress
    missing_downloads = []
    missing_notion = []
    download_failures = []
    notion_failures = []

    # Check each paper
    for paper in papers:
        conventional_name = paper["conventional_name"]
        codename = paper["codename"]
        conference = paper["conference"]
        url = paper["url"]

        print(f"\nChecking: {conventional_name}")

        # Check if file exists
        filename = f"{conventional_name}.pdf"
        filepath = download_dir / filename

        if not filepath.exists():
            missing_downloads.append(paper)
            print("   Missing download")
        else:
            print(f"   {SUCCESS} File exists")

        # Check if Notion entry exists
        if not check_paper_exists_in_notion(conventional_name):
            missing_notion.append(paper)
            print("   Missing Notion entry")
        else:
            print(f"   {SUCCESS} Notion entry exists")

    # Summary of what needs to be synced
    print("\nSync Summary:")
    print(f"   Missing downloads: {len(missing_downloads)}")
    print(f"   Missing Notion entries: {len(missing_notion)}")

    if not missing_downloads and not missing_notion:
        print(f"\n{SUCCESS} Everything is already in sync!")
        return

    # Download missing files
    if missing_downloads:
        print(f"\nDownloading {len(missing_downloads)} missing files...")
        for paper in missing_downloads:
            conventional_name = paper["conventional_name"]
            url = paper["url"]
            filename = f"{conventional_name}.pdf"
            filepath = download_dir / filename

            try:
                print(f"   Downloading {conventional_name}...")
                urllib.request.urlretrieve(url, filepath)
                print(f"   {SUCCESS} Downloaded: {filename}")
            except Exception as e:
                print(f"   {ERROR} Failed to download {conventional_name}: {e}")
                download_failures.append(paper)

    # Add missing Notion entries
    if missing_notion:
        print(f"\nAdding {len(missing_notion)} missing Notion entries...")
        for paper in missing_notion:
            conventional_name = paper["conventional_name"]
            codename = paper["codename"]
            conference = paper["conference"]
            url = paper["url"]

            notion_title = f"{codename} ({conference})"

            try:
                print(f"   Adding to Notion: {conventional_name}")
                add_paper(notion_title, url, conventional_name)
                print(f"   {SUCCESS} Added to Notion: {notion_title}")
            except Exception as e:
                print(f"   {ERROR} Failed to add {conventional_name} to Notion: {e}")
                notion_failures.append(paper)

    # Final summary
    print("\nSync Results:")
    print(
        f"   {SUCCESS} Downloads completed: {len(missing_downloads) - len(download_failures)}"
    )
    print(f"   {ERROR} Download failures: {len(download_failures)}")
    print(f"   {SUCCESS} Notion entries added: {len(missing_notion) - len(notion_failures)}")
    print(f"   {ERROR} Notion failures: {len(notion_failures)}")

    if download_failures:
        print(f"\n{WARNING} Download failures:")
        for paper in download_failures:
            print(f"   - {paper['conventional_name']}: {paper['url']}")

    if notion_failures:
        print(f"\n{WARNING} Notion failures:")
        for paper in notion_failures:
            print(f"   - {paper['conventional_name']}")

    if not download_failures and not notion_failures:
        print("\nSync completed successfully!")


def find_paper_by_codename(codename: str) -> dict:
    """Find a paper by codename (case insensitive).

    Returns paper metadata dict or None.
    """
    papers_data = load_papers_metadata()
    papers = papers_data.get("papers", [])

    for paper in papers:
        if paper["codename"].lower() == codename.lower():
            return paper

    return None


def open_paper(codename: str) -> None:
    """Open a paper by codename.

    Check download_dir first, copy from archive_dir if needed.
    """
    import subprocess
    import shutil

    # Find paper metadata
    paper = find_paper_by_codename(codename)
    if not paper:
        print(
            f"Paper '{codename}' not found in metadata. Use 'porg add' to add it first."
        )
        return

    conventional_name = paper["conventional_name"]
    filename = f"{conventional_name}.pdf"

    download_dir = get_download_dir()
    archive_dir = get_archive_dir()

    download_path = download_dir / filename
    archive_path = archive_dir / filename

    # Check if file exists in download_dir (cache)
    if download_path.exists():
        print(f"Opening from cache: {download_path}")
    elif archive_path.exists():
        # Copy from archive to download_dir
        print(f"Copying from archive to cache: {conventional_name}")
        download_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(archive_path, download_path)
        print(f"{SUCCESS} Copied to: {download_path}")
    else:
        print(
            f"Paper '{conventional_name}.pdf' not found in either "
            f"download_dir or archive_dir"
        )
        print(f"   Download dir: {download_dir}")
        print(f"   Archive dir: {archive_dir}")
        return

    # Open the file
    try:
        print(f"Opening: {download_path}")
        subprocess.run(["open", str(download_path)], check=True)
        print(f"{SUCCESS} Opened: {conventional_name}")
    except subprocess.CalledProcessError as e:
        print(f"{ERROR} Failed to open file: {e}")
    except FileNotFoundError:
        print(f"{ERROR} 'open' command not found. Are you on macOS?")


def flush_papers(codenames: List[str]) -> None:
    """Flush papers from download_dir to archive_dir, then remove from download_dir."""
    import subprocess
    import shutil

    download_dir = get_download_dir()
    archive_dir = get_archive_dir()
    archive_dir.mkdir(parents=True, exist_ok=True)

    successful_flushes = []
    failed_flushes = []

    for codename in codenames:
        # Find paper metadata
        paper = find_paper_by_codename(codename)
        if not paper:
            print(f"{ERROR} Paper '{codename}' not found in metadata")
            failed_flushes.append(codename)
            continue

        conventional_name = paper["conventional_name"]
        filename = f"{conventional_name}.pdf"

        download_path = download_dir / filename
        archive_path = archive_dir / filename

        # Check if file exists in download_dir
        if not download_path.exists():
            print(
                f"Paper '{conventional_name}' not found in download_dir: "
                f"{download_path}"
            )
            failed_flushes.append(codename)
            continue

        try:
            # Copy to archive_dir
            print(f"Flushing {conventional_name} to archive...")
            shutil.copy2(download_path, archive_path)
            print(f"   {SUCCESS} Copied to: {archive_path}")

            # Remove from download_dir
            subprocess.run(["rm", str(download_path)], check=True)
            print(f"   Removed from cache: {download_path}")

            successful_flushes.append(conventional_name)

        except Exception as e:
            print(f"{ERROR} Failed to flush {conventional_name}: {e}")
            failed_flushes.append(codename)

    # Summary
    print("\nFlush Summary:")
    print(f"   {SUCCESS} Successfully flushed: {len(successful_flushes)}")
    print(f"   {ERROR} Failed: {len(failed_flushes)}")

    if successful_flushes:
        print(f"   Flushed papers: {', '.join(successful_flushes)}")

    if failed_flushes:
        print(f"   Failed papers: {', '.join(failed_flushes)}")


def get_paper_info(codename: str) -> None:
    """Get and display paper information from Notion by codename."""
    from src.notion import get_paper_by_name, format_paper_info

    paper_data = get_paper_by_name(codename)
    if paper_data:
        format_paper_info(paper_data)


def get_papers_by_project_filter(project_name: str) -> None:
    """Get and display papers filtered by project name."""
    from src.notion import get_papers_by_project, format_paper_list

    papers = get_papers_by_project(project_name)
    if papers:
        print(f"Papers in project '{project_name}':")
        print("=" * 40)
        format_paper_list(papers)
    else:
        print(f"No papers found for project '{project_name}'.")


def get_papers_by_topic_filter(topic_name: str) -> None:
    """Get and display papers filtered by topic name."""
    from src.notion import get_papers_by_topic, format_paper_list

    papers = get_papers_by_topic(topic_name)
    if papers:
        print(f"Papers with topic '{topic_name}':")
        print("=" * 40)
        format_paper_list(papers)
    else:
        print(f"No papers found for topic '{topic_name}'.")


def get_all_papers_list() -> None:
    """Get and display all papers from local papers.json metadata."""
    papers_data = load_papers_metadata()
    papers = papers_data.get("papers", [])

    if not papers:
        print("No papers found in local metadata.")
        print("Use 'porg add <url>' to add papers.")
        return

    print(f"Found {len(papers)} paper(s):")
    print("-" * 30)

    for paper in papers:
        codename = paper.get("codename", "Unknown")
        conference = paper.get("conference", "Unknown")
        print(f"• {codename} ({conference})")
