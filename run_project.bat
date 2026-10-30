@echo off
setlocal

title Customer Segmentation and RFM Analysis Pipeline

echo =====================================================================
echo  CUSTOMER SEGMENTATION ^& RFM ANALYSIS - AUTOMATED PIPELINE
echo =====================================================================
echo.

:: 1. Virtual Environment Activation
if not exist ".venv\Scripts\activate.bat" goto no_venv
echo [Step 1/5] Activating Python virtual environment (.venv)...
call .venv\Scripts\activate.bat
goto venv_done

:no_venv
echo [Step 1/5] Virtual environment not found at .venv. Proceeding with system Python...

:venv_done

:: Verify python is available
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH or the virtual environment.
    echo Please install Python 3.10+ or configure the virtual environment.
    pause
    exit /b 1
)

:: 2. Install missing dependencies
echo.
echo [Step 2/5] Checking and installing dependencies from requirements.txt...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies from requirements.txt.
    pause
    exit /b 1
)
echo Dependencies verified successfully.

:: 3. Run Core Python Analysis Pipeline
echo.
echo [Step 3/5] Executing core RFM analysis pipeline (src/analyze.py)...
python src/analyze.py
if errorlevel 1 (
    echo [ERROR] The analysis pipeline failed during execution.
    pause
    exit /b 1
)

:: 4. Run Automated Validation and Reconciliation Checks
echo.
echo [Step 4/5] Running automated validation and reconciliation tests...
python tests/validate_pipeline.py
if errorlevel 1 (
    echo [ERROR] Pipeline validation tests failed! Check output above.
    pause
    exit /b 1
)

:: 5. Launch Streamlit Interactive Dashboard
echo.
echo [Step 5/5] Launching Streamlit Interactive Dashboard...
echo Dashboard will open in your default browser at http://localhost:8501
echo Press Ctrl+C in this terminal window to stop the dashboard server.
echo.
streamlit run src/dashboard.py

if errorlevel 1 (
    echo [ERROR] Failed to launch Streamlit dashboard.
    pause
    exit /b 1
)

exit /b 0
