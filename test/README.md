# Promptree CLI - Regression Tests

This directory contains test files to ensure that the Promptree CLI functionality continues to work as expected after future enhancements. These tests help prevent regressions when implementing new features.

## Available Tests

1. **test_links.py** - Tests the database functionality for conversation links
2. **test_cli_links.py** - Tests the CLI functionality for linking conversations
3. **test_retrieve_links.py** - Tests retrieving linked conversations
4. **test_unlink.py** - Tests the unlink functionality

## How to Run Tests

To run individual tests, you must run them from the main project directory:

```bash
cd ..
python test/test_links.py
python test/test_cli_links.py
python test/test_retrieve_links.py
python test/test_unlink.py
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

## Adding New Tests

When implementing new features, please add corresponding regression tests to this directory.