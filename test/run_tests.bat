@echo off
REM Run all regression tests for Promptree CLI

echo Running regression tests for Promptree CLI...

REM Change to the parent directory to run tests
cd ..

echo Testing database functionality for conversation links...
python test/test_links.py
if errorlevel 1 goto error

echo Testing CLI functionality for linking conversations...
python test/test_cli_links.py
if errorlevel 1 goto error

echo Testing retrieval of linked conversations...
python test/test_retrieve_links.py
if errorlevel 1 goto error

echo Testing unlink functionality...
python test/test_unlink.py
if errorlevel 1 goto error

echo Testing basic plain text conversion functionality...
python test/test_text_conversion.py
if errorlevel 1 goto error

echo Testing updated plain text conversion with linked conversations...
python test/test_updated_text_conversion.py
if errorlevel 1 goto error

echo Testing linked conversations editing functionality...
python test/test_linked_conversations_editing.py
if errorlevel 1 goto error

echo Testing multiple comma-separated linked IDs...
python test/test_multiple_linked_ids.py
if errorlevel 1 goto error

echo All tests completed successfully!
goto end

:error
echo One or more tests failed!
exit /b 1

:end
cd test