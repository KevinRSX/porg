# porg - Paper Organization Tool

**porg** is a command-line tool designed to streamline the workflow of academic researchers by automating the process of downloading, organizing, and cataloging research papers. It integrates seamlessly with Notion databases to maintain a centralized knowledge base while providing consistent local file organization. Whether you're managing a few papers or building an extensive research library, porg simplifies the entire pipeline from paper discovery to organized storage with rich metadata.

porg is almost completely written by [Claude Code](https://www.anthropic.com/claude-code).

## Usage

porg is designed with composability in mind - you can use individual components or leverage the complete workflow depending on your needs.

### Complete Workflow
You will first need to create a Notion database page that is a superset of the [example page](https://quark-tent-6b7.notion.site/250c9b097e058071abb1d7e5f9bcee3b?v=250c9b097e058190b0e3000cebfdedf3).

Then set up the Notion integration with 
```bash
porg notion --setup
```

For a fully automated experience, use the integrated `add` command:
```bash
porg add https://arxiv.org/pdf/2506.24045
```
This will:
1. Prompt for paper metadata (title, conference)
2. Download the PDF with consistent naming (`<codename>-<conference>.pdf`)
3. Add an entry to your Notion database
4. Store metadata in your local configuration

### Individual Components

**Download papers only:**
```bash
porg download --url https://arxiv.org/pdf/2506.24045 --file my-paper-name
```

**Notion integration setup:**
```bash
porg notion --setup
```

**Add paper to Notion database:**
```bash
porg notion --add --name "Paper Title" --url https://arxiv.org/pdf/2506.24045
```

### Configuration

porg stores configuration and metadata in `~/.porg/`:
- `notion.json` - Notion integration tokens and database settings
- `papers.json` - Local paper metadata and naming information

## Installation

```bash
pip install -e .
```

## Setup

1. **Configure Notion integration** (optional):
   ```bash
   porg notion --setup
   ```
   Follow the prompts to set up your Notion integration token and database.

2. **Start adding papers:**
   ```bash
   porg add https://your-paper-url.pdf
   ```

## Project Roadmap

- [ ] **Updating and deleting papers**

- [ ] **Sync Feature** - Implement bidirectional synchronization between local paper metadata, file organization, and Notion database to ensure consistency across all platforms

- [ ] **Formalized Download Location** - Create a configurable and structured approach to paper storage locations, with support for custom directory hierarchies and organization schemes

- [ ] **Zotero Integration** - Add comprehensive support for Zotero reference manager, including import/export functionality and synchronization with existing Zotero libraries

- [ ] **Paper notes** - Support connecting the paper to paper notes written externally

- [ ] **Queries** - Allow users to query the paper store by project or topic


### License

MIT License - see LICENSE file for details.