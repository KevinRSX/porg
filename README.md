# porg - Paper Organization Tool

**porg** is a command line tool to download research papers and add corresponding entries to a Notion paper collection database.

porg is almost completely written by [Claude Code](https://www.anthropic.com/claude-code).

## Installation

First, install the project:
```bash
pip install .
```

Install in editable mode if you want to customize the source file:
```bash
pip install -e .
```

You need a [Notion](https://www.notion.so/) account. Create a Notion database page that is a superset of the [example page](https://quark-tent-6b7.notion.site/250c9b097e058071abb1d7e5f9bcee3b?v=250c9b097e058190b0e3000cebfdedf3). You are encouraged to duplicate the example page. Then, follow the instructions given by to connect port to your [Notion integrations](https://www.notion.com/integrations).
```bash
porg notion --setup
```

## File Organization

porg uses a flexible directory structure that separates active reading from long-term storage:

### Directory Structure

```yaml
# ~/.porg/config.yaml
download_dir: "~/Desktop/quick_reads"                    # Active reading cache
archive_dir: "~/Desktop/Readings/Papers/General"        # Long-term storage (write)
archive_read_dir: "~/Desktop/Readings/Papers"           # Long-term storage (read)
```

**How it works:**
- **`download_dir`**: Your active reading cache where papers are temporarily stored for quick access
- **`archive_dir`**: Where papers are permanently stored when using `porg flush` 
- **`archive_read_dir`**: The root directory for recursive paper searches

### Manual Organization Support

You can manually organize papers into subdirectories like:
```
~/Desktop/Readings/Papers/
├── General/           # Default archive location
├── CSE585/           # Course-specific papers
├── Research/         # Research project papers
└── Conferences/      # Conference proceedings
```

**Benefits:**
- `porg sync` and `porg open` will find papers in any subdirectory
- `porg flush` always writes to the consistent `General/` directory
- You maintain full control over paper organization
- No need to update configuration when creating new subdirectories

## Papers porg cannot download

Some papers sit behind a paywall or otherwise refuse to be fetched from their
URL. When a download fails, `porg add` still records the metadata and creates
the Notion entry, and reports the PDF as `missing`:

```
Process Summary:
   ✅ Metadata saved: Yes
   ✗ PDF: missing
   ✅ Notion integration: Success
```

Every command that lists papers shows where each PDF actually is:

- `local` — in `download_dir`
- `archived` — somewhere under `archive_read_dir`
- `missing` — in neither, so you do not have the paper yet

```bash
$ porg get
• DistServe (OSDI 2024) [local]
• Exokernel (SIGOPS 1995) [archived]
• Paywalled Thing (ISCA 2022) [missing]
```

Download such a paper by hand into `download_dir` or anywhere under
`archive_read_dir`, and the next command that looks for it will find it. There
is no state to update: the directories are the source of truth for whether you
have a paper.

## What `porg sync` reconciles

`porg sync` keeps three things in step — your metadata config, your paper
directories, and your Notion database:

1. **Config → disk and Notion.** Every paper in `papers.json` that has no PDF
   is downloaded, and every one without a Notion entry gets one. A paper with
   no URL is reported as needing a manual download instead.
2. **Disk → config.** Any PDF in `download_dir` or the archive that no metadata
   entry claims was downloaded by hand, so sync offers to adopt it. It asks for
   a codename and conference exactly like `porg add`, and — since there is no
   URL for a paper you fetched yourself — the Notion page it creates does not
   link out. Accepting a conventional name that differs from the filename
   renames the PDF to match.
3. **Notion → config.** Any Notion entry that no metadata entry claims is shown
   to you, and you can add it to the config or delete it from Notion.

The config stays the source of truth for a paper's *details* — sync never
rewrites the codename, conference, or URL of a paper you have already
recorded. The directories are the source of truth for whether the paper is
actually on hand.

Sync is interactive whenever it finds something unclaimed. Skipping a paper is
not remembered, so a PDF you keep declining will be offered again next time.

## Usage
Basic usage:
```bash
porg add <paper-url>
```

This will:
1. Prompt for paper metadata (title, conference)
2. Download the PDF with consistent naming (`<codename>-<conference>.pdf`)
3. Add an entry to your Notion database
4. Store metadata in your local configuration


`porg add` will do everything at once, but each component is also exposed to the CLI:
```
usage: porg [-h] {add,sync,open,flush,get,download,notion} ...

Download and organize research papers

positional arguments:
  {add,sync,open,flush,get,download,notion}
                        Available commands
    add                 Add paper (metadata + download + Notion)
    sync                Sync papers from config to downloads and Notion
    open                Open a paper by codename
    flush               Flush papers from download_dir to archive_dir
    get                 Query paper information from Notion
    download            Download a research paper
    notion              Notion integration commands

optional arguments:
  -h, --help            show this help message and exit
```

You can use `porg <command> -h|--help` to understand how to run each of the commands.

## Configuration Files
porg stores configuration and metadata in `~/.porg/`:
- `config.yaml` - Directories for quick read and long term storage locations
- `notion.json` - Notion integration tokens and database settings
- `papers.json` - Local paper metadata and naming information


### License
MIT License - see LICENSE file for details.
