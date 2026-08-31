#!/usr/bin/env python
import json
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
        "archive_read_dir": "~/Desktop/Readings/Papers",
    }


def get_download_dir() -> Path:
    """Get the configured download directory."""
    config = load_config()
    return Path(config["download_dir"]).expanduser()


def get_archive_dir() -> Path:
    """Get the configured archive directory (for writing)."""
    config = load_config()
    return Path(config["archive_dir"]).expanduser()


def get_archive_read_dir() -> Path:
    """Get the configured archive read directory (for reading recursively)."""
    config = load_config()
    return Path(config["archive_read_dir"]).expanduser()


def find_paper_in_archive(filename: str) -> Path:
    """Recursively search for a paper in the archive read directory.

    Returns the full path if found, None otherwise.
    """
    archive_read_dir = get_archive_read_dir()

    # Use glob to recursively search for the file
    matches = list(archive_read_dir.glob(f"**/{filename}"))

    if matches:
        return matches[0]  # Return first match
    return None


def locate_paper_pdf(conventional_name: str) -> Tuple[Optional[Path], Optional[str]]:
    """Find a paper's PDF on disk.

    Returns (path, "download") or (path, "archive"), and (None, None) when the
    paper is in neither the download directory nor the archive.
    """
    filename = f"{conventional_name}.pdf"

    download_path = get_download_dir() / filename
    if download_path.exists():
        return download_path, "download"

    # archive_dir is normally inside archive_read_dir, but check it directly in
    # case it has been configured somewhere else.
    archive_path = get_archive_dir() / filename
    if archive_path.exists():
        return archive_path, "archive"

    archive_path = find_paper_in_archive(filename)
    if archive_path:
        return archive_path, "archive"

    return None, None


def describe_paper_location(conventional_name: str) -> str:
    """Describe where a paper's PDF is, for display."""
    _, location = locate_paper_pdf(conventional_name)
    if location == "download":
        return "local"
    if location == "archive":
        return "archived"
    return "missing"


def scan_download_pdfs() -> Dict[str, Path]:
    """Find every PDF in the download directory.

    Returns {conventional_name: path}. The archive is deliberately left out:
    it is a long-term store you organize yourself, not a queue of papers
    waiting to be recorded.
    """
    found = {}

    download_dir = get_download_dir()
    if download_dir.exists():
        for path in sorted(download_dir.glob("*.pdf")):
            found.setdefault(path.stem, path)

    return found


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

    # Step 2: Download the paper, unless a copy is already on disk
    print("\nDownloading paper...")
    download_dir = get_download_dir()
    download_dir.mkdir(parents=True, exist_ok=True)

    conventional_name = paper_metadata["conventional_name"]
    filepath = download_dir / f"{conventional_name}.pdf"

    existing_path, location = locate_paper_pdf(conventional_name)
    paper_available = existing_path is not None

    if existing_path:
        where = "download_dir" if location == "download" else "archive"
        print(f"File already exists in {where}: {existing_path}")
    else:
        try:
            print(f"Downloading to: {filepath}")
            urllib.request.urlretrieve(url, filepath)
            print(f"{SUCCESS} Successfully downloaded: {filepath}")
            paper_available = True
        except Exception as e:
            filepath.unlink(missing_ok=True)
            print(f"{ERROR} Error downloading paper: {e}")
            print(
                f"{WARNING} Download failed, but continuing with Notion integration..."
            )

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
    pdf_icon = SUCCESS if paper_available else ERROR
    print(f"   {pdf_icon} PDF: {describe_paper_location(conventional_name)}")
    notion_status = "Success" if notion_successful else "Failed"
    notion_icon = SUCCESS if notion_successful else ERROR
    print(f"   {notion_icon} Notion integration: {notion_status}")

    if not paper_available:
        print(
            f"\nNote: the PDF is in neither download_dir nor the archive. "
            f"Download it manually from: {url}"
        )
        print(f"   Save it as: {filepath}")

    if paper_available and notion_successful:
        print("\nPaper successfully added to your research collection!")


def guess_metadata_from_stem(stem: str) -> Tuple[str, str]:
    """Guess a codename and conference from a conventional-name filename."""
    if "-" in stem:
        codename, conference = stem.rsplit("-", 1)
        return codename, conference
    return stem, ""


def guess_metadata_from_title(title: str) -> Tuple[str, str]:
    """Guess a codename and conference from a '<codename> (<conference>)' title."""
    match = re.match(r"^(.*?)\s*\((.*)\)\s*$", title)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return title.strip(), ""


def prompt_adoption_metadata(
    default_codename: str = "",
    default_conference: str = "",
    known_conventional_name: str = "",
    known_name_label: str = "",
    prefer_generated: bool = True,
) -> Optional[dict]:
    """Prompt for paper metadata the way 'porg add' does, with defaults.

    known_conventional_name is the name the paper already goes by, either the
    PDF's filename or the one recorded in Notion. prefer_generated decides
    which of it and the generated name is offered as the default; the other is
    shown alongside so it can be typed instead.

    Returns the metadata dict, or None if the user gave up on this paper.
    """
    codename_prompt = "   Codename"
    if default_codename:
        codename_prompt += f" [{default_codename}]"
    codename = input(f"{codename_prompt}: ").strip() or default_codename
    if not codename:
        print(f"   {WARNING} Codename cannot be empty, skipping.")
        return None

    conference_prompt = "   Conference"
    if default_conference:
        conference_prompt += f" [{default_conference}]"
    conference = input(f"{conference_prompt}: ").strip() or default_conference
    if not conference:
        print(f"   {WARNING} Conference cannot be empty, skipping.")
        return None

    generated = generate_conventional_name(codename, conference)
    if known_conventional_name and known_conventional_name != generated:
        if prefer_generated:
            fallback, alternative = generated, known_conventional_name
            label = known_name_label or "current"
        else:
            fallback, alternative = known_conventional_name, generated
            label = "generated"
        name_prompt = f"   Conventional name [{fallback}] ({label}: {alternative})"
    else:
        fallback = generated
        name_prompt = f"   Conventional name [{fallback}]"
    conventional_name = input(f"{name_prompt}: ").strip() or fallback

    return {
        "conventional_name": conventional_name,
        "url": None,
        "codename": codename,
        "conference": conference,
    }


def check_configured_papers(papers: List[dict]) -> Tuple[List[dict], List[dict]]:
    """Report where each configured paper stands, on disk and in Notion."""
    from src.notion import check_paper_exists_in_notion

    missing_files = []
    missing_notion = []

    for paper in papers:
        conventional_name = paper["conventional_name"]
        print(f"\nChecking: {conventional_name}")

        path, location = locate_paper_pdf(conventional_name)
        if location == "download":
            print(f"   {SUCCESS} File exists in download_dir")
        elif location == "archive":
            print(f"   {SUCCESS} File exists in archive ({path})")
        else:
            missing_files.append(paper)
            print(f"   {ERROR} Missing: in neither download_dir nor archive")

        if check_paper_exists_in_notion(conventional_name):
            print(f"   {SUCCESS} Notion entry exists")
        else:
            missing_notion.append(paper)
            print(f"   {WARNING} Missing Notion entry")

    return missing_files, missing_notion


def download_missing_papers(missing_files: List[dict]) -> List[dict]:
    """Download the configured papers that are not on disk. Returns failures."""
    import urllib.request

    failures = []
    if not missing_files:
        return failures

    print(f"\nDownloading {len(missing_files)} missing files...")
    download_dir = get_download_dir()

    for paper in missing_files:
        conventional_name = paper["conventional_name"]
        url = paper.get("url")

        if not url:
            print(
                f"   {WARNING} {conventional_name}: no URL recorded, "
                f"download it manually"
            )
            failures.append(paper)
            continue

        filepath = download_dir / f"{conventional_name}.pdf"
        try:
            print(f"   Downloading {conventional_name}...")
            urllib.request.urlretrieve(url, filepath)
            print(f"   {SUCCESS} Downloaded: {filepath.name}")
        except Exception as e:
            filepath.unlink(missing_ok=True)
            print(f"   {ERROR} Failed to download {conventional_name}: {e}")
            failures.append(paper)

    return failures


def create_missing_notion_entries(missing_notion: List[dict]) -> List[dict]:
    """Create Notion entries for configured papers that lack one."""
    from src.notion import add_paper

    failures = []
    if not missing_notion:
        return failures

    print(f"\nAdding {len(missing_notion)} missing Notion entries...")

    for paper in missing_notion:
        conventional_name = paper["conventional_name"]
        notion_title = f"{paper['codename']} ({paper['conference']})"

        try:
            print(f"   Adding to Notion: {conventional_name}")
            add_paper(
                notion_title,
                paper.get("url"),
                conventional_name,
                prompt_url=False,
            )
            print(f"   {SUCCESS} Added to Notion: {notion_title}")
        except Exception as e:
            print(f"   {ERROR} Failed to add {conventional_name} to Notion: {e}")
            failures.append(paper)

    return failures


def adopt_paper_from_file(path: Path) -> Optional[dict]:
    """Record a manually downloaded PDF in the metadata config and Notion."""
    from src.notion import add_paper

    print(f"\nUnregistered PDF: {path}")
    answer = input("   Add it to your paper metadata? (y/N): ").strip().lower()
    if answer not in ["y", "yes"]:
        print("   Skipped.")
        return None

    codename_guess, conference_guess = guess_metadata_from_stem(path.stem)
    metadata = prompt_adoption_metadata(
        codename_guess, conference_guess, path.stem, "current filename"
    )
    if not metadata:
        return None

    # The conventional name has to match the filename, or porg will not find
    # the paper again. Renaming the file keeps the two in step.
    if metadata["conventional_name"] != path.stem:
        new_path = path.with_name(f"{metadata['conventional_name']}.pdf")
        if new_path.exists():
            print(f"   {ERROR} {new_path} already exists, keeping the filename.")
            metadata["conventional_name"] = path.stem
        else:
            path.rename(new_path)
            print(f"   Renamed to: {new_path}")

    if not save_paper_metadata(metadata):
        return None

    # The paper was downloaded by hand, so there is no URL to link to.
    notion_title = f"{metadata['codename']} ({metadata['conference']})"
    try:
        add_paper(notion_title, None, metadata["conventional_name"], prompt_url=False)
    except Exception as e:
        print(f"   {ERROR} Failed to add {notion_title} to Notion: {e}")

    return metadata


def adopt_unregistered_files() -> List[dict]:
    """Offer to adopt PDFs in the download directory that no metadata claims."""
    known = {
        paper["conventional_name"] for paper in load_papers_metadata().get("papers", [])
    }
    orphans = {
        stem: path for stem, path in scan_download_pdfs().items() if stem not in known
    }

    if not orphans:
        return []

    print(f"\nFound {len(orphans)} PDF(s) in download_dir with no metadata entry.")
    adopted = []
    for stem in sorted(orphans):
        metadata = adopt_paper_from_file(orphans[stem])
        if metadata:
            adopted.append(metadata)

    return adopted


def reconcile_notion_page(page: dict) -> Tuple[Optional[dict], bool]:
    """Offer to adopt or delete one Notion entry. Returns (metadata, deleted)."""
    from src.notion import (
        archive_notion_page,
        extract_page_conventional_name,
        extract_page_title,
        extract_page_url,
        set_page_conventional_name,
    )

    title = extract_page_title(page)
    url = extract_page_url(page)
    conventional_name = extract_page_conventional_name(page)

    print(f"\nNotion entry with no metadata record: {title}")
    if conventional_name:
        print(f"   Conventional name: {conventional_name}")
    if url:
        print(f"   URL: {url}")

    answer = (
        input("   [a]dd to metadata, [d]elete from Notion, [s]kip (default): ")
        .strip()
        .lower()
    )

    if answer in ["d", "delete"]:
        confirm = input(f"   Move '{title}' to Notion's trash? (y/N): ").strip().lower()
        if confirm in ["y", "yes"] and archive_notion_page(page["id"]):
            print(f"   {SUCCESS} Deleted from Notion: {title}")
            return None, True
        print("   Skipped.")
        return None, False

    if answer not in ["a", "add"]:
        print("   Skipped.")
        return None, False

    codename_guess, conference_guess = guess_metadata_from_title(title)
    metadata = prompt_adoption_metadata(
        codename_guess, conference_guess, conventional_name, prefer_generated=False
    )
    if not metadata:
        return None, False

    metadata["url"] = url
    if not save_paper_metadata(metadata):
        return None, False

    # Stamp the conventional name onto the page so the next sync matches it.
    if metadata["conventional_name"] != conventional_name:
        set_page_conventional_name(page["id"], metadata["conventional_name"])

    return metadata, False


def reconcile_notion_entries() -> Tuple[List[dict], List[dict]]:
    """Offer to adopt or delete Notion entries that no metadata entry claims."""
    from src.notion import (
        extract_page_conventional_name,
        extract_page_title,
        get_all_papers,
        get_database_properties,
        load_notion_config,
    )

    notion_config = load_notion_config()
    if not notion_config:
        return [], []

    properties = get_database_properties(
        notion_config["token"], notion_config["database_id"]
    )
    if "Conventional Name" not in properties:
        print(
            f"\n{WARNING} Your Notion database has no 'Conventional Name' property, "
            f"so porg cannot match its entries against your metadata. "
            f"Skipping Notion reconciliation."
        )
        return [], []

    papers = load_papers_metadata().get("papers", [])
    known_names = {paper["conventional_name"] for paper in papers}
    known_titles = {
        f"{paper['codename']} ({paper['conference']})".lower() for paper in papers
    }

    orphans = []
    for page in get_all_papers():
        conventional_name = extract_page_conventional_name(page)
        if conventional_name:
            if conventional_name not in known_names:
                orphans.append(page)
        elif extract_page_title(page).lower() not in known_titles:
            orphans.append(page)

    if not orphans:
        return [], []

    print(f"\nFound {len(orphans)} Notion entry(ies) with no metadata record.")
    adopted = []
    deleted = []
    for page in orphans:
        metadata, was_deleted = reconcile_notion_page(page)
        if metadata:
            adopted.append(metadata)
        if was_deleted:
            deleted.append(page)

    return adopted, deleted


def sync_papers() -> None:
    """Sync papers across the metadata config, local directories, and Notion.

    The metadata config stays the source of truth for a paper's details, but
    the download and archive directories are the source of truth for whether a
    paper is on hand, and porg offers to adopt anything it finds in them, or in
    Notion, that the config does not know about yet.
    """
    print("Starting paper synchronization...")

    papers = load_papers_metadata().get("papers", [])
    if papers:
        print(f"Found {len(papers)} papers in configuration")
    else:
        print("No papers found in configuration file.")

    get_download_dir().mkdir(parents=True, exist_ok=True)

    # Pass 1: everything the config already knows about
    missing_files, missing_notion = check_configured_papers(papers)

    print("\nSync Summary:")
    print(f"   Missing files: {len(missing_files)}")
    print(f"   Missing Notion entries: {len(missing_notion)}")

    download_failures = download_missing_papers(missing_files)
    notion_failures = create_missing_notion_entries(missing_notion)

    # Pass 2: PDFs in download_dir that the config has never seen
    adopted_files = adopt_unregistered_files()

    # Pass 3: Notion entries the config has never seen
    adopted_notion, deleted_notion = reconcile_notion_entries()

    # Final summary
    print("\nSync Results:")
    print(
        f"   {SUCCESS} Downloads completed: "
        f"{len(missing_files) - len(download_failures)}"
    )
    print(f"   {ERROR} Download failures: {len(download_failures)}")
    print(
        f"   {SUCCESS} Notion entries added: "
        f"{len(missing_notion) - len(notion_failures)}"
    )
    print(f"   {ERROR} Notion failures: {len(notion_failures)}")
    print(f"   {SUCCESS} Papers adopted from download_dir: {len(adopted_files)}")
    print(f"   {SUCCESS} Papers adopted from Notion: {len(adopted_notion)}")
    print(f"   {SUCCESS} Notion entries deleted: {len(deleted_notion)}")

    if download_failures:
        print(f"\n{WARNING} Still missing, download these by hand:")
        for paper in download_failures:
            url = paper.get("url") or "no URL recorded"
            print(f"   - {paper['conventional_name']}: {url}")

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
    download_path = download_dir / filename
    path, location = locate_paper_pdf(conventional_name)

    if location == "download":
        print(f"Opening from cache: {download_path}")
    elif location == "archive":
        # Copy from archive to download_dir
        print(f"Copying from archive to cache: {conventional_name}")
        download_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, download_path)
        print(f"{SUCCESS} Copied to: {download_path}")
    else:
        print(f"Paper '{filename}' not found in either download_dir or archive")
        print(f"   Download dir: {download_dir}")
        print(f"   Archive search dir: {get_archive_read_dir()}")
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
        location = describe_paper_location(paper["conventional_name"])
        print(f"• {codename} ({conference}) [{location}]")
