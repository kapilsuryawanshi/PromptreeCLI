# Promptree CLI

Promptree CLI is a command-line interface application that records LLM conversations as a tree structure. Each node stores prompt + response + metadata. When asking under a node, only the chain of ancestors is passed to the LLM for context, allowing users to branch into multiple lines of research without bloating LLM context.

## Features

- Store LLM conversations in a tree structure
- Maintain context only from ancestor conversations
- Browse conversation trees
- Export conversation trees to markdown
- Edit conversation subjects and parent relationships
- Search conversations by text content
- Remove conversations and their subtrees
- Color-coded console output
- Stream LLM responses to console in real-time
- Enhanced `open` command that shows parent conversation subject line before current conversation
- New `close` command to reset current conversation context
- New `up` command to navigate to parent of current conversation

## Requirements

- Python 3.7+
- Ollama running locally (default at http://localhost:11434)

## Installation

1. Clone or download the repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

First, make sure Ollama is running locally. Then run the application with the model name:

```bash
python main.py <model_name>
```

For example:

```bash
python main.py llama2
```

This will start the CLI with the prompt: `Promptree|<model>|Parent:<current_id>> `

## Commands

### quit / exit
Exit the application
```
Promptree|llama2|Parent:None> quit
```

### rm
Remove conversations and their subtrees recursively
```
Promptree|llama2|Parent:None> rm 1,5,8
```

### edit
Update the subject of a conversation and/or parent relationship:
- Update subject: `edit <id> -subject "<new subject>"`
- Update parent: `edit <id> -parent <id|None>`
- Update both: `edit <id> -parent <id|None> -subject "<new subject>"` or `edit <id> -subject "<new subject>" -parent <id|None>`
- Link to other conversations: `edit <id> -link <id>[,<id>,...]` (link to multiple conversations using comma separation)
- Remove all links: `edit <id> -link None`
- Remove specific links: `edit <id> -unlink <id>[,<id>,...]` (unlink from multiple conversations using comma separation)
- Edit in external editor: `edit <id>` (opens conversation in your default editor in plain text format for comprehensive editing)
```
Promptree|llama2|Parent:None> edit 1 -subject "Updated subject"
Promptree|llama2|Parent:None> edit 1 -parent 2
Promptree|llama2|Parent:None> edit 1 -parent 3 -subject "New Subject"
```

### list
List all top-level conversations
```
Promptree|llama2|Parent:None> list
```

### open
Show a conversation and its subtree. Shows the parent conversation subject line before the current conversation, and sub-conversations are displayed with only their subject lines for a clean overview.
```
Promptree|llama2|Parent:None> open 5
```

### close
Close current conversation context and reset to root (clears current parent)
```
Promptree|llama2|Parent:5> close
```

### up
Navigate to the parent of the currently remembered conversation
```
Promptree|llama2|Parent:5> up
```

### search
Search for text in conversations. Supports wildcard characters (*) and case-insensitive matching.
```
Promptree|llama2|Parent:None> search python
Promptree|llama2|Parent:None> search *script*
```

### ask
Ask a question, optionally under a parent conversation. The LLM response will be streamed to the console in real-time.
- Basic usage: `ask <prompt>`
- With parent context: `ask @<id> <prompt>`
- With external editor: `ask` (opens external editor for longer prompts)
  - When 'ask' is used without arguments, it opens a temporary text file with PARENT_ID and USER_PROMPT sections for users to input longer prompts and specify the parent conversation ID
  - The file format includes markers like USER_PROMPT_START/USER_PROMPT_END for editing the prompt content
```
Promptree|llama2|Parent:None> ask What is the capital of France?
Promptree|llama2|Parent:None> ask @5 How does this relate to Paris?
Promptree|llama2|Parent:None> ask
```

### export
Export a conversation tree to a markdown file
```
Promptree|llama2|Parent:None> export 5 output.md
```

### summarize
Summarize a conversation
```
Promptree|llama2|Parent:None> summarize 5
```

### add
Manually add a conversation with parent, links, prompt and response using an external editor.
- Opens a temporary text file that includes fields for PARENT_ID, LINKED_CONVERSATIONS_ID, USER_PROMPT, and LLM_RESPONSE
- The file format includes markers like USER_PROMPT_START/USER_PROMPT_END and LLM_RESPONSE_START/LLM_RESPONSE_END for editing the prompt and response content
- The LLM generates a subject line based on the prompt and response, then adds the conversation to the database with the specified parent and links
```
Promptree|llama2|Parent:None> add
```

### help
Show help information
```
Promptree|llama2|Parent:None> help
```

## Data Storage

The application stores conversations in an SQLite database located at `~/promptree.db` (in the user's home directory).

## Color Coding

- **Yellow**: Subject lines
- **Cyan**: User prompts
- **Green**: LLM responses
- **Red**: Error messages

## How It Works

Promptree allows you to create a tree of conversations with an LLM. Each node in the tree represents a conversation (prompt + response), and nodes can have parent-child relationships.

When you ask a question under a specific node (using `ask @<id> <prompt>`), only the conversation history from the root to that node is provided as context to the LLM. This prevents context bloat and keeps related conversations organized.

This approach enables branching conversations - you can explore multiple follow-up questions from any point in the conversation tree without losing context or interfering with other branches.

The enhanced `edit` command allows you to modify both subject and parent relationships, even allowing you to move conversations to different parts of the tree or make them root conversations by setting parent to None. Circular reference detection prevents creating invalid tree structures.

The `search` command enables full-text search across conversation subjects, prompts, and responses with wildcard support.

## Database Schema

The application uses a SQLite database with a single table:

```
conversations table:
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- subject: TEXT
- model_name: TEXT
- user_prompt: TEXT
- llm_response: TEXT
- pid: INTEGER (foreign key to id, NULL for root nodes)
- user_prompt_timestamp: DATETIME
- llm_response_timestamp: DATETIME
```

## Troubleshooting

- Ensure Ollama is running locally at the default address (http://localhost:11434)
- Verify that the specified model is available in Ollama
- Check that you have write permissions to your home directory for the database file