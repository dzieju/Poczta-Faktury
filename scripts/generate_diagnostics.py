#!/usr/bin/env python3
"""
Diagnostic script for Poczta-Faktury application.
Collects comprehensive system, repository, and application information for troubleshooting.
"""

import os
import sys
import subprocess
import platform
import json
from datetime import datetime
from pathlib import Path


class DiagnosticsGenerator:
    """Generate comprehensive diagnostics for Poczta-Faktury application."""
    
    def __init__(self, output_dir="diagnostics_output"):
        """Initialize diagnostics generator.
        
        Args:
            output_dir: Directory where diagnostics will be saved
        """
        self.output_dir = Path(output_dir)
        self.repo_root = Path(__file__).parent.parent
        self.diagnostics = []
        
    def log(self, message):
        """Log a message to diagnostics output."""
        print(message)
        self.diagnostics.append(message)
        
    def run_command(self, cmd, cwd=None, timeout=30):
        """Run a shell command and return output.
        
        Args:
            cmd: Command to run (list or string)
            cwd: Working directory (defaults to repo root)
            timeout: Command timeout in seconds
            
        Returns:
            tuple: (stdout, stderr, returncode)
        
        Note:
            shell=True is safe here as all string commands are hardcoded
            literals with no user input. List commands use shell=False.
        """
        if cwd is None:
            cwd = self.repo_root
            
        try:
            if isinstance(cmd, str):
                # shell=True is safe: only used with hardcoded command strings
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            else:
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", f"Command timed out after {timeout}s", -1
        except Exception as e:
            return "", str(e), -1
    
    def collect_git_info(self):
        """Collect Git repository information."""
        self.log("\n" + "="*80)
        self.log("GIT REPOSITORY INFORMATION")
        self.log("="*80)
        
        # Current branch
        stdout, stderr, _ = self.run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        self.log(f"\nCurrent branch: {stdout.strip()}")
        
        # Last 50 commits
        self.log("\n--- Last 50 commits ---")
        stdout, stderr, _ = self.run_command([
            "git", "log", "--oneline", "--decorate", "-50"
        ])
        self.log(stdout if stdout else "No commits found")
        
        # Git status
        self.log("\n--- Git status ---")
        stdout, stderr, _ = self.run_command(["git", "status", "--porcelain"])
        if stdout.strip():
            self.log(stdout)
        else:
            self.log("Working tree clean")
            
        # Git status (verbose)
        stdout, stderr, _ = self.run_command(["git", "status"])
        self.log(f"\n{stdout}")
        
        # Recent tags
        self.log("\n--- Recent tags ---")
        stdout, stderr, _ = self.run_command(["git", "tag", "-l", "--sort=-version:refname"])
        if stdout.strip():
            tags = stdout.strip().split('\n')[:10]  # Last 10 tags
            self.log('\n'.join(tags))
        else:
            self.log("No tags found")
            
        # Remote information
        self.log("\n--- Remote repositories ---")
        stdout, stderr, _ = self.run_command(["git", "remote", "-v"])
        self.log(stdout if stdout else "No remotes configured")
    
    def collect_environment_info(self):
        """Collect system and environment information."""
        self.log("\n" + "="*80)
        self.log("ENVIRONMENT INFORMATION")
        self.log("="*80)
        
        # System information
        self.log(f"\nOperating System: {platform.system()} {platform.release()}")
        self.log(f"Platform: {platform.platform()}")
        self.log(f"Architecture: {platform.machine()}")
        self.log(f"Processor: {platform.processor() or 'Unknown'}")
        
        # uname -a
        stdout, stderr, _ = self.run_command("uname -a")
        if stdout:
            self.log(f"\nuname -a: {stdout.strip()}")
        
        # Python version
        self.log(f"\nPython version: {sys.version}")
        self.log(f"Python executable: {sys.executable}")
        
        # Python packages
        self.log("\n--- Python packages (pip freeze) ---")
        stdout, stderr, _ = self.run_command([sys.executable, "-m", "pip", "freeze"])
        if stdout:
            self.log(stdout)
        else:
            self.log("Could not retrieve pip packages")
            
        # Check for requirements.txt
        requirements_file = self.repo_root / "requirements.txt"
        if requirements_file.exists():
            self.log("\n--- requirements.txt ---")
            with open(requirements_file, 'r') as f:
                self.log(f.read())
        
        # Check for venv or poetry
        self.log("\n--- Python environment detection ---")
        if os.environ.get('VIRTUAL_ENV'):
            self.log(f"Virtual environment detected: {os.environ['VIRTUAL_ENV']}")
        else:
            self.log("No virtual environment detected")
            
        # Check for package.json (Node.js)
        package_json = self.repo_root / "package.json"
        if package_json.exists():
            self.log("\n--- Node.js environment detected ---")
            stdout, stderr, _ = self.run_command("node --version")
            if stdout:
                self.log(f"Node version: {stdout.strip()}")
            stdout, stderr, _ = self.run_command("npm --version")
            if stdout:
                self.log(f"npm version: {stdout.strip()}")
            self.log("\n--- npm packages (npm list --depth=0) ---")
            stdout, stderr, _ = self.run_command("npm list --depth=0")
            self.log(stdout if stdout else "Could not retrieve npm packages")
    
    def collect_docker_info(self):
        """Collect Docker information if available."""
        self.log("\n" + "="*80)
        self.log("DOCKER INFORMATION")
        self.log("="*80)
        
        # Check if docker is available
        stdout, stderr, returncode = self.run_command("docker --version")
        if returncode != 0:
            self.log("\nDocker not available or not installed")
            return
            
        self.log(f"\nDocker version: {stdout.strip()}")
        
        # Docker ps
        self.log("\n--- Running containers (docker ps) ---")
        stdout, stderr, _ = self.run_command("docker ps --format 'table {{.ID}}\\t{{.Names}}\\t{{.Status}}\\t{{.Image}}'")
        if stdout:
            self.log(stdout)
        else:
            self.log("No running containers")
            
        # Docker ps -a (all containers)
        self.log("\n--- All containers (docker ps -a) ---")
        stdout, stderr, _ = self.run_command("docker ps -a --format 'table {{.ID}}\\t{{.Names}}\\t{{.Status}}\\t{{.Image}}'")
        if stdout:
            self.log(stdout)
        else:
            self.log("No containers found")
            
        # Get logs from running containers
        stdout, stderr, _ = self.run_command("docker ps -q")
        if stdout:
            container_ids = stdout.strip().split('\n')
            for container_id in container_ids[:5]:  # Limit to first 5 containers
                self.log(f"\n--- Docker logs for container {container_id} (last 100 lines) ---")
                stdout, stderr, _ = self.run_command(
                    f"docker logs --tail 100 {container_id}",
                    timeout=10
                )
                if stdout:
                    self.log(stdout)
                if stderr:
                    self.log(f"[STDERR]\n{stderr}")
    
    def collect_application_logs(self):
        """Collect application log files."""
        self.log("\n" + "="*80)
        self.log("APPLICATION LOGS")
        self.log("="*80)
        
        # Common log directories to search
        log_dirs = [
            self.repo_root / "logs",
            self.repo_root / "storage" / "logs",
            self.repo_root / "var" / "log",
            Path.home() / ".poczta_faktury_logs",
        ]
        
        logs_output_dir = self.output_dir / "logs"
        logs_output_dir.mkdir(parents=True, exist_ok=True)
        
        found_logs = []
        
        for log_dir in log_dirs:
            if not log_dir.exists():
                continue
                
            self.log(f"\n--- Searching in {log_dir} ---")
            
            # Find all log files
            for log_file in log_dir.rglob("*.log"):
                if log_file.is_file():
                    found_logs.append(log_file)
                    self.log(f"Found: {log_file}")
                    
                    # Copy last 1000 lines to output
                    try:
                        with open(log_file, 'r', errors='replace') as f:
                            lines = f.readlines()
                            last_lines = lines[-1000:] if len(lines) > 1000 else lines
                            
                        output_file = logs_output_dir / f"{log_file.name}"
                        # Handle duplicate names
                        counter = 1
                        while output_file.exists():
                            output_file = logs_output_dir / f"{log_file.stem}_{counter}{log_file.suffix}"
                            counter += 1
                            
                        with open(output_file, 'w', errors='replace') as f:
                            f.writelines(last_lines)
                            
                        self.log(f"  Copied last {len(last_lines)} lines to {output_file.name}")
                    except Exception as e:
                        self.log(f"  Error reading log file: {e}")
            
            # Also find txt files that might be logs
            for txt_file in log_dir.rglob("*.txt"):
                if txt_file.is_file() and 'log' in txt_file.name.lower():
                    found_logs.append(txt_file)
                    self.log(f"Found: {txt_file}")
                    
                    try:
                        with open(txt_file, 'r', errors='replace') as f:
                            lines = f.readlines()
                            last_lines = lines[-1000:] if len(lines) > 1000 else lines
                            
                        output_file = logs_output_dir / f"{txt_file.name}"
                        counter = 1
                        while output_file.exists():
                            output_file = logs_output_dir / f"{txt_file.stem}_{counter}{txt_file.suffix}"
                            counter += 1
                            
                        with open(output_file, 'w', errors='replace') as f:
                            f.writelines(last_lines)
                            
                        self.log(f"  Copied last {len(last_lines)} lines to {output_file.name}")
                    except Exception as e:
                        self.log(f"  Error reading log file: {e}")
        
        if not found_logs:
            self.log("\nNo log files found in common directories")
    
    def collect_application_config(self):
        """Collect application configuration (sanitized)."""
        self.log("\n" + "="*80)
        self.log("APPLICATION CONFIGURATION")
        self.log("="*80)
        
        # Check for config file
        config_file = Path.home() / ".poczta_faktury_config.json"
        if config_file.exists():
            self.log(f"\nConfiguration file found: {config_file}")
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Sanitize sensitive data
                if 'password' in config:
                    config['password'] = "***REDACTED***"
                if 'email' in config:
                    # Partially redact email
                    email = config['email']
                    if '@' in email and not email.startswith('@'):
                        parts = email.split('@')
                        if len(parts) == 2:  # Valid email format
                            username, domain = parts
                            if len(username) >= 3:
                                config['email'] = f"{username[:2]}***@{domain}"
                            else:
                                config['email'] = f"***@{domain}"
                        else:
                            config['email'] = "***REDACTED***"
                    else:
                        config['email'] = "***REDACTED***"
                
                self.log("\n--- Sanitized configuration ---")
                self.log(json.dumps(config, indent=2))
            except Exception as e:
                self.log(f"Error reading config file: {e}")
        else:
            self.log("\nNo configuration file found")
        
        # Application version
        version_file = self.repo_root / "version.txt"
        if version_file.exists():
            try:
                with open(version_file, 'r') as f:
                    version = f.read().strip()
                self.log(f"\nApplication version: {version}")
            except Exception as e:
                self.log(f"\nError reading version file: {e}")
    
    def collect_file_structure(self):
        """Collect repository file structure."""
        self.log("\n" + "="*80)
        self.log("REPOSITORY FILE STRUCTURE")
        self.log("="*80)
        
        self.log("\n--- Top level files and directories ---")
        try:
            for item in sorted(self.repo_root.iterdir()):
                if item.name.startswith('.'):
                    continue
                if item.is_dir():
                    self.log(f"  {item.name}/")
                else:
                    size = item.stat().st_size
                    self.log(f"  {item.name} ({size} bytes)")
        except Exception as e:
            self.log(f"Error listing files: {e}")
    
    def generate(self):
        """Generate full diagnostics report."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log("="*80)
        self.log(f"POCZTA-FAKTURY DIAGNOSTICS REPORT")
        self.log(f"Generated: {timestamp}")
        self.log("="*80)
        
        # Collect all information
        self.collect_git_info()
        self.collect_environment_info()
        self.collect_docker_info()
        self.collect_application_config()
        self.collect_file_structure()
        self.collect_application_logs()
        
        # Save diagnostics to file
        diagnostics_file = self.output_dir / "diagnostics.txt"
        with open(diagnostics_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.diagnostics))
        
        self.log("\n" + "="*80)
        self.log(f"Diagnostics saved to: {diagnostics_file.absolute()}")
        self.log(f"Logs directory: {(self.output_dir / 'logs').absolute()}")
        self.log("="*80)
        
        return diagnostics_file


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate comprehensive diagnostics for Poczta-Faktury application"
    )
    parser.add_argument(
        "--output-dir",
        default="diagnostics_output",
        help="Output directory for diagnostics (default: diagnostics_output)"
    )
    
    args = parser.parse_args()
    
    print(f"Generating diagnostics...")
    print(f"Output directory: {args.output_dir}")
    print()
    
    generator = DiagnosticsGenerator(output_dir=args.output_dir)
    diagnostics_file = generator.generate()
    
    print(f"\n✓ Diagnostics generation complete!")
    print(f"  Report: {diagnostics_file.absolute()}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
