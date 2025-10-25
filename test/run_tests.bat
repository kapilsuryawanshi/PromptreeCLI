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

echo All tests completed successfully!
goto end

:error
echo One or more tests failed!
exit /b 1

:end
cd test