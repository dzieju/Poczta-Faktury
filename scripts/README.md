# Scripts Directory

This directory contains utility scripts for the Poczta-Faktury application.

## Available Scripts

### generate_diagnostics.py

Generates comprehensive diagnostics for troubleshooting application issues.

**Purpose:**
Collects detailed information about the system, repository, environment, and application state to help diagnose problems.

**Usage:**

```bash
# Generate diagnostics to default directory (diagnostics_output/)
python scripts/generate_diagnostics.py

# Generate diagnostics to custom directory
python scripts/generate_diagnostics.py --output-dir /path/to/output
```

**What it collects:**

1. **Git Repository Information:**
   - Current branch
   - Last 50 commits
   - Git status (working tree changes)
   - Recent tags
   - Remote repositories

2. **Environment Information:**
   - Operating system details (uname -a)
   - Python version and executable path
   - Installed Python packages (pip freeze)
   - Requirements.txt contents
   - Virtual environment detection
   - Node.js information (if package.json exists)

3. **Docker Information (if available):**
   - Docker version
   - Running containers (docker ps)
   - All containers (docker ps -a)
   - Container logs (last 100 lines from each container)

4. **Application Configuration:**
   - Application version (from version.txt)
   - Configuration file (sanitized - passwords redacted)

5. **Repository File Structure:**
   - Top-level files and directories with sizes

6. **Application Logs:**
   - Searches common log directories:
     - logs/
     - storage/logs/
     - var/log/
     - ~/.poczta_faktury_logs/
   - Copies last 1000 lines from each log file to output/logs/

**Output:**

The script generates:
- `diagnostics_output/diagnostics.txt` - Main diagnostics report
- `diagnostics_output/logs/` - Directory containing collected log files

**GitHub Actions Integration:**

You can also generate diagnostics via GitHub Actions:

1. Go to the "Actions" tab in the repository
2. Select "Generate Diagnostics" workflow
3. Click "Run workflow"
4. Optionally provide a reason for generating diagnostics
5. Download the generated artifacts after the workflow completes

The workflow creates two artifacts:
- `diagnostics-[sha].tar.gz` - Compressed archive of all diagnostics
- `diagnostics-raw-[sha]` - Raw diagnostics output directory

**Example:**

```bash
cd /home/runner/work/Poczta-Faktury/Poczta-Faktury
python scripts/generate_diagnostics.py --output-dir /tmp/my_diagnostics

# View the report
cat /tmp/my_diagnostics/diagnostics.txt

# Check collected logs
ls -la /tmp/my_diagnostics/logs/
```

---

### increment_version.py

Automatically increments the patch version in `version.txt`.

**Usage:**

```bash
python scripts/increment_version.py version.txt
```

This script is used by the GitHub Actions workflow to automatically bump the version on each push to the main branch.
