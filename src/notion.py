#!/usr/bin/env python
import json
from pathlib import Path
import requests


def get_config_dir() -> Path:
    return Path.home() / ".porg"


def get_notion_config_path() -> Path:
    return get_config_dir() / "notion.json"


def ensure_config_dir() -> None:
    """Ensure the config directory exists."""
    config_dir = get_config_dir()
    config_dir.mkdir(exist_ok=True)


def load_notion_config() -> dict:
    """Load Notion-specific configuration."""
    notion_config_path = get_notion_config_path()
    if notion_config_path.exists():
        with open(notion_config_path, 'r') as f:
            return json.load(f)
    return {}


def save_notion_config(notion_config: dict) -> None:
    """Save Notion-specific configuration."""
    ensure_config_dir()
    notion_config_path = get_notion_config_path()
    with open(notion_config_path, 'w') as f:
        json.dump(notion_config, f, indent=2)


def inspect_database(token: str, database_id: str) -> dict:
    """Inspect database properties and return database info."""
    # Clean database ID (remove view parameters)
    if '?' in database_id:
        database_id = database_id.split('?')[0]
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f'https://api.notion.com/v1/databases/{database_id}', headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Error accessing database: {response.status_code} - {response.text}")
    
    return response.json()


def validate_database_properties(db_info: dict) -> bool:
    """Validate that the database has the expected properties for paper management."""
    properties = db_info.get('properties', {})
    
    # Required properties for paper management
    required_props = {
        'Name': 'title',
        'Related Project': 'multi_select', 
        'Topic': 'multi_select',
        'Last Read': 'date',
        'Status': 'status'
    }
    
    missing_props = []
    invalid_types = []
    
    for prop_name, expected_type in required_props.items():
        if prop_name not in properties:
            missing_props.append(prop_name)
        else:
            actual_type = properties[prop_name].get('type')
            if actual_type != expected_type:
                invalid_types.append(f"{prop_name} (expected: {expected_type}, found: {actual_type})")
    
    if missing_props or invalid_types:
        print("❌ Database validation failed!")
        if missing_props:
            print(f"Missing properties: {', '.join(missing_props)}")
        if invalid_types:
            print(f"Invalid property types: {', '.join(invalid_types)}")
        
        print("\nYour database should have these properties:")
        for prop_name, prop_type in required_props.items():
            print(f"• {prop_name}: {prop_type}")
        
        return False
    
    return True


def display_database_info(db_info: dict) -> None:
    """Display database information for user confirmation."""
    properties = db_info.get('properties', {})
    db_title = db_info.get('title', [{}])[0].get('plain_text', 'Unknown')
    
    print(f"\n📊 Database: {db_title}")
    print("=" * 40)
    
    for prop_name, prop_info in properties.items():
        prop_type = prop_info.get('type', 'unknown')
        print(f"• {prop_name}: {prop_type}")
        
        # Show options for select/multi_select
        if prop_type in ['select', 'multi_select']:
            options = prop_info.get(prop_type, {}).get('options', [])
            if options:
                option_names = [opt['name'] for opt in options]
                print(f"  Options: {', '.join(option_names)}")


def setup_notion() -> None:
    print("Setting up Notion integration...")
    
    # Check for existing configuration
    existing_notion = load_notion_config()
    existing_token = existing_notion.get('token')
    existing_db_id = existing_notion.get('database_id')
    notion_config_path = get_notion_config_path()
    
    # Security warning
    print("\n⚠️  SECURITY WARNING:")
    print("Your Notion integration token will be stored in plain text on your computer.")
    print(f"Location: {notion_config_path}")
    print("Make sure your computer is secure and consider the risks.")
    print("You can delete the config file anytime to remove stored tokens.")
    
    if not existing_token:
        print("\nTo connect to Notion, you need to:")
        print("1. Go to https://www.notion.so/my-integrations")
        print("2. Click '+ New integration'")
        print("3. Give it a name (e.g., 'porg paper organizer')")
        print("4. Select your workspace")
        print("5. Click 'Submit'")
        print("6. Copy the 'Internal Integration Token' from the Secrets tab")
        print("7. Share your database page with the integration:")
        print("   - Open your database page")
        print("   - Click ••• at the top right")
        print("   - Click 'Add connections'")
        print("   - Select your integration")
    
    # Token input with default handling
    if existing_token:
        token_prompt = f"\nYour Notion integration token (default token stored at {notion_config_path}): "
    else:
        token_prompt = "\nPaste your Notion integration token: "
    
    token = input(token_prompt).strip()
    
    # Handle token logic
    if not token and existing_token:
        token = existing_token
        print("Using cached token.")
    elif not token and not existing_token:
        print("Error: Token cannot be empty")
        return
    elif token and existing_token and token != existing_token:
        # Confirm token change
        confirm = input(f"You entered a different token. Replace the cached token? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Setup cancelled.")
            return
        print("Token will be updated.")
    
    # Database ID input with default handling
    if existing_db_id:
        db_prompt = f"\nYour database ID (default database stored at {notion_config_path}): "
    else:
        db_prompt = "\nEnter your database ID (from the database URL): "
    
    database_id = input(db_prompt).strip()
    
    # Handle database ID logic
    if not database_id and existing_db_id:
        database_id = existing_db_id
        print("Using cached database ID.")
    elif not database_id and not existing_db_id:
        print("Error: Database ID cannot be empty")
        return
    elif database_id and existing_db_id and database_id != existing_db_id:
        # Confirm database change
        confirm = input(f"You entered a different database ID. Replace the cached database? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Setup cancelled.")
            return
        print("Database ID will be updated.")
    
    # Test connection and inspect database
    print("\n🔍 Inspecting database...")
    try:
        db_info = inspect_database(token, database_id)
        display_database_info(db_info)
        
        # Validate database structure
        if not validate_database_properties(db_info):
            print("\n❌ Please fix your database structure and try again.")
            return
        
        print("\n✅ Database validation passed!")
        
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
        return
    
    # Save configuration
    notion_config = {
        'token': token,
        'database_id': database_id.split('?')[0]  # Clean database ID
    }
    save_notion_config(notion_config)
    
    print("✅ Notion integration configured successfully!")
    print(f"Configuration saved to: {get_notion_config_path()}")


def get_database_properties(token: str, database_id: str) -> dict:
    """Get database properties for field input."""
    try:
        db_info = inspect_database(token, database_id)
        return db_info.get('properties', {})
    except Exception as e:
        print(f"❌ Error getting database properties: {e}")
        return {}


def prompt_for_multi_select(prop_name: str, options: list) -> list:
    """Prompt user for multi-select field with available options."""
    print(f"\n{prop_name} options:")
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option['name']}")
    
    print("\nEnter selections (comma-separated numbers or names, e.g., '1,3' or 'CSE582,Hotness', leave empty to skip):")
    user_input = input(f"{prop_name}: ").strip()
    
    if not user_input:
        return []
    
    selected = []
    for item in user_input.split(','):
        item = item.strip()
        
        # Try to parse as number (1-indexed)
        try:
            idx = int(item) - 1
            if 0 <= idx < len(options):
                selected.append(options[idx])
                continue
        except ValueError:
            pass
        
        # Try to find by name
        for option in options:
            if option['name'].lower() == item.lower():
                selected.append(option)
                break
    
    return selected


def prompt_for_status(prop_name: str, options: list) -> dict:
    """Prompt user for status field with available options."""
    print(f"\n{prop_name} options:")
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option['name']}")
    
    # Find default "Not Started" option
    default_option = None
    for option in options:
        if option['name'].lower() in ['not started', 'not-started', 'todo', 'to do']:
            default_option = option
            break
    
    if default_option:
        user_input = input(f"{prop_name} (number or name, default: {default_option['name']}): ").strip()
    else:
        user_input = input(f"{prop_name} (number or name): ").strip()
    
    if not user_input:
        return default_option  # Return default or None if no default found
    
    # Try to parse as number (1-indexed)
    try:
        idx = int(user_input) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except ValueError:
        pass
    
    # Try to find by name
    for option in options:
        if option['name'].lower() == user_input.lower():
            return option
    
    print(f"Invalid selection: {user_input}")
    return default_option  # Return default on invalid input


def add_paper(paper_name: str, paper_url: str = None) -> None:
    """Add a paper to the Notion database."""
    notion_config = load_notion_config()
    
    if not notion_config:
        print("❌ Notion not configured. Run 'porg notion --setup' first.")
        return
    
    token = notion_config['token']
    database_id = notion_config['database_id']
    
    print(f"Adding paper: {paper_name}")
    
    # Get database properties
    properties = get_database_properties(token, database_id)
    if not properties:
        return
    
    # Handle URL - either from command line or prompt
    if paper_url is None:
        url = input("\nPaper URL (leave empty to skip): ").strip()
    else:
        url = paper_url
        print(f"Using URL: {url}")
    
    # Prepare properties for the new page
    # Format title with proper Notion link format
    if url:
        page_properties = {
            "Name": {
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": paper_name,
                            "link": {
                                "url": url
                            }
                        }
                    }
                ]
            }
        }
    else:
        page_properties = {
            "Name": {
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": paper_name
                        }
                    }
                ]
            }
        }
    
    # Handle Related Project (multi_select)
    if "Related Project" in properties:
        project_options = properties["Related Project"].get("multi_select", {}).get("options", [])
        if project_options:
            selected_projects = prompt_for_multi_select("Related Project", project_options)
            if selected_projects:
                page_properties["Related Project"] = {
                    "multi_select": [{"name": proj["name"]} for proj in selected_projects]
                }
    
    # Handle Topic (multi_select)
    if "Topic" in properties:
        topic_options = properties["Topic"].get("multi_select", {}).get("options", [])
        if topic_options:
            selected_topics = prompt_for_multi_select("Topic", topic_options)
            if selected_topics:
                page_properties["Topic"] = {
                    "multi_select": [{"name": topic["name"]} for topic in selected_topics]
                }
    
    # Handle Status (always set, with default)
    if "Status" in properties:
        status_options = properties["Status"].get("status", {}).get("options", [])
        if status_options:
            selected_status = prompt_for_status("Status", status_options)
            if selected_status:
                page_properties["Status"] = {
                    "status": {"name": selected_status["name"]}
                }
    
    # Handle Last Read (date)
    last_read = input("\nLast Read (YYYY-MM-DD, leave empty for today): ").strip()
    if last_read:
        # Validate date format
        try:
            from datetime import datetime
            datetime.strptime(last_read, '%Y-%m-%d')
            page_properties["Last Read"] = {
                "date": {"start": last_read}
            }
        except ValueError:
            print("Invalid date format, skipping Last Read")
    else:
        # Use today's date
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        page_properties["Last Read"] = {
            "date": {"start": today}
        }
    
    # Create the page
    headers = {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    # Add URL as page content (only if provided)
    page_data = {
        "parent": {"database_id": database_id},
        "properties": page_properties
    }
    
    if url:
        page_data["children"] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Paper URL: "
                            }
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": url,
                                "link": {
                                    "url": url
                                }
                            }
                        }
                    ]
                }
            }
        ]
    
    try:
        response = requests.post('https://api.notion.com/v1/pages', headers=headers, json=page_data)
        
        if response.status_code == 200:
            print(f"✅ Successfully added paper '{paper_name}' to Notion!")
        else:
            print(f"❌ Error adding paper: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error creating page: {e}")