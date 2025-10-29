# Promptree CLI - Regression Tests

This directory contains test files to ensure that the Promptree CLI functionality continues to work as expected after future enhancements. These tests help prevent regressions when implementing new features.

## Available Tests

1. **test_links.py** - Tests the database functionality for conversation links
2. **test_cli_links.py** - Tests the CLI functionality for linking conversations
3. **test_retrieve_links.py** - Tests retrieving linked conversations
4. **test_unlink.py** - Tests the unlink functionality
5. **test_text_conversion.py** - Tests basic plain text conversion functionality for external editor editing
6. **test_updated_text_conversion.py** - Tests updated plain text conversion with linked conversations display
7. **test_linked_conversations_editing.py** - Tests the ability to edit linked conversations in the text file
8. **test_multiple_linked_ids.py** - Tests handling of multiple comma-separated linked conversation IDs

## How to Run Tests

To run individual tests, you must run them from the main project directory:

```bash
cd ..
python test/test_links.py
python test/test_cli_links.py
python test/test_retrieve_links.py
python test/test_unlink.py
python test/test_text_conversion.py
python test/test_updated_text_conversion.py
python test/test_linked_conversations_editing.py
python test/test_multiple_linked_ids.py
```

Or use the batch file:

```bash
run_tests.bat
```

## Test Coverage

These tests verify:

- Database schema for conversation links
- Adding and removing conversation links
- Linking multiple conversations
- Unlinking specific conversations
- CLI command syntax and functionality
- Retrieving linked conversations from the database
- Display functionality for linked conversations
- Plain text conversion and parsing for external editor functionality

## Adding New Tests

When implementing new features, please add corresponding regression tests to this directory.