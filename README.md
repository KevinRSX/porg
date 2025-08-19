# porg - Paper Organization Tool

**porg** is a command line tool to download research papers and add corresponding entries to a Notion paper collection database.

porg is almost completely written by [Claude Code](https://www.anthropic.com/claude-code).

## Installation

First, install the project:
```bash
pip install .
```

You may also do an editable install if you want to customize the source file:
```bash
pip install -e .
```

You need a [Notion](https://www.notion.so/) account. Create a Notion database page that is a superset of the [example page](https://quark-tent-6b7.notion.site/250c9b097e058071abb1d7e5f9bcee3b?v=250c9b097e058190b0e3000cebfdedf3). You are encouraged to duplicate the example page. Then, follow the instructions given by to connect port to your [Notion integrations](https://www.notion.com/integrations).
```bash
porg notion --setup
```

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
usage: porg [-h] {add,sync,download,notion} ...

Download and organize research papers

positional arguments:
  {add,sync,download,notion}
                        Available commands
    add                 Add paper (metadata + download + Notion)
    sync                Sync papers from config to downloads and Notion
    download            Download a research paper
    notion              Notion integration commands

optional arguments:
  -h, --help            show this help message and exit
```

## Configuration Files
porg stores configuration and metadata in `~/.porg/`:
- `notion.json` - Notion integration tokens and database settings
- `papers.json` - Local paper metadata and naming information


## Project Roadmap
- [x] **Formalized Download Location** - Create a configurable and structured approach to paper storage locations, with support for custom directory hierarchies and organization schemes
- [ ] **Zotero Integration** - Add comprehensive support for Zotero reference manager, including import/export functionality and synchronization with existing Zotero libraries
- [ ] **Paper notes** - Support connecting the paper to paper notes written externally
- [x] **Queries** - Allow users to query the paper store by project or topic
- [ ] **Full Paper Titles** - Add support for storing and displaying full paper titles separately from codenames, allowing display format like "Full Paper Title [Codename] (Conference)" for better readability

### License

MIT License - see LICENSE file for details.
