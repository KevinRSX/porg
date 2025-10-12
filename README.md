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
