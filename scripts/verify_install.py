#!/usr/bin/env python3
"""
Verify PacketClaude installation
Checks dependencies and configuration
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def check_python_version():
    """Check Python version"""
    print("Checking Python version...", end=" ")
    if sys.version_info < (3, 11):
        print("FAIL")
        print(f"  Python 3.11+ required, found {sys.version}")
        return False
    print(f"OK (Python {sys.version.split()[0]})")
    return True


def check_dependencies():
    """Check required Python packages"""
    print("\nChecking Python dependencies...")
    required = [
        ('anthropic', 'Anthropic'),
        ('yaml', 'PyYAML'),
        ('dotenv', 'python-dotenv'),
    ]

    all_ok = True
    for module_name, package_name in required:
        print(f"  {package_name}...", end=" ")
        try:
            __import__(module_name)
            print("OK")
        except ImportError:
            print("MISSING")
            all_ok = False

    return all_ok


def check_optional_dependencies():
    """Check optional dependencies"""
    print("\nChecking optional dependencies...")

    # Hamlib
    print("  Hamlib (for radio control)...", end=" ")
    try:
        import Hamlib
        print("OK")
    except ImportError:
        print("NOT INSTALLED (optional)")

    return True


def check_config_files():
    """Check configuration files"""
    print("\nChecking configuration files...")

    project_dir = Path(__file__).parent.parent

    # Check .env
    print("  .env file...", end=" ")
    env_file = project_dir / ".env"
    if env_file.exists():
        print("OK")
        # Check for API key
        with open(env_file) as f:
            content = f.read()
            if "ANTHROPIC_API_KEY" in content and "your_api_key_here" not in content:
                print("    API key appears to be set")
            else:
                print("    WARNING: Set your ANTHROPIC_API_KEY in .env")
    else:
        print("MISSING")
        print("    Copy .env.example to .env and add your API key")
        return False

    # Check config.yaml
    print("  config/config.yaml...", end=" ")
    config_file = project_dir / "config" / "config.yaml"
    if config_file.exists():
        print("OK")
        # Check for default callsign
        with open(config_file) as f:
            content = f.read()
            if "N0CALL" in content:
                print("    WARNING: Update 'callsign' in config/config.yaml")
    else:
        print("MISSING")
        print("    Copy config/config.yaml.example to config/config.yaml")
        return False

    return True


def check_directories():
    """Check required directories"""
    print("\nChecking directories...")

    project_dir = Path(__file__).parent.parent
    dirs = [
        project_dir / "logs",
        project_dir / "data",
    ]

    all_ok = True
    for d in dirs:
        print(f"  {d.name}/...", end=" ")
        if d.exists():
            print("OK")
        else:
            print("CREATING")
            try:
                d.mkdir(parents=True)
                print(f"    Created {d}")
            except Exception as e:
                print(f"    FAILED: {e}")
                all_ok = False

    return all_ok


def check_imports():
    """Check that PacketClaude modules can be imported"""
    print("\nChecking PacketClaude modules...")

    modules = [
        'packetclaude.config',
        'packetclaude.database',
        'packetclaude.ax25.kiss',
        'packetclaude.ax25.protocol',
        'packetclaude.claude.client',
        'packetclaude.claude.session',
        'packetclaude.auth.rate_limiter',
    ]

    all_ok = True
    for module in modules:
        print(f"  {module}...", end=" ")
        try:
            __import__(module)
            print("OK")
        except Exception as e:
            print(f"FAIL: {e}")
            all_ok = False

    return all_ok


def main():
    """Main verification"""
    print("=" * 60)
    print("PacketClaude Installation Verification")
    print("=" * 60)

    checks = [
        ("Python version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Optional dependencies", check_optional_dependencies),
        ("Configuration files", check_config_files),
        ("Directories", check_directories),
        ("Module imports", check_imports),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\nError during {name} check: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
        if not result:
            all_passed = False

    print()
    if all_passed:
        print("All checks passed! PacketClaude is ready to run.")
        print("\nNext steps:")
        print("  1. Make sure Direwolf is running")
        print("  2. Test KISS connection: python scripts/test_kiss.py")
        print("  3. Run PacketClaude: ./scripts/run.sh")
        return 0
    else:
        print("Some checks failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
