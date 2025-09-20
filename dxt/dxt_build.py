#!/usr/bin/env python3
"""
DXT Extension Build Script for Ring MCP Server

This script creates a properly packaged DXT extension with all dependencies bundled.
Based on the DXT_BUILDING_GUIDE.md and DXT_PACKAGING_ISSUES.md documentation.

Usage:
    python dxt_build.py [--output-dir OUTPUT_DIR] [--clean]

Requirements:
    - Python 3.9+
    - fastmcp>=2.12.0
    - All dependencies listed in requirements.txt
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

def install_dependencies(lib_dir: Path, requirements_file: Path):
    """Install dependencies to the lib directory."""
    print(f"📦 Installing dependencies to {lib_dir}")

    cmd = [
        sys.executable, "-m", "pip", "install",
        "--target", str(lib_dir),
        "-r", str(requirements_file)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to install dependencies: {result.stderr}")
        return False

    print("✅ Dependencies installed successfully")
    return True

def validate_imports(lib_dir: Path, src_dir: Path):
    """Validate that all imports work correctly."""
    print("🔍 Validating imports...")

    # Add paths to sys.path for testing
    import sys
    sys.path.insert(0, str(lib_dir))
    sys.path.insert(0, str(src_dir))

    try:
        # Test core imports
        import fastmcp
        print(f"✅ FastMCP imported: {fastmcp.__version__}")

        # Test our main module
        import ring_mcp
        from ring_mcp.server import create_app
        print("✅ Ring MCP modules imported successfully")

        # Test FastMCP version requirement
        from packaging import version
        if version.parse(fastmcp.__version__) < version.parse("2.12.0"):
            print(f"❌ FastMCP version {fastmcp.__version__} is too old (need >= 2.12.0)")
            return False

        print("✅ All imports validated successfully")
        return True

    except ImportError as e:
        print(f"❌ Import validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during validation: {e}")
        return False
    finally:
        # Clean up sys.path
        if str(lib_dir) in sys.path:
            sys.path.remove(str(lib_dir))
        if str(src_dir) in sys.path:
            sys.path.remove(str(src_dir))

def create_main_py(temp_dir: Path):
    """Create main.py entry point with proper sys.path setup."""
    main_py_content = '''#!/usr/bin/env python3
"""
Ring MCP Server - DXT Entry Point

This file serves as the entry point for the Ring MCP Server DXT extension.
It properly sets up the Python path to include the lib and src directories.
"""

import os
import sys

# Get the current directory (where this script is located)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add lib and src to Python path
lib_dir = os.path.join(current_dir, 'lib')
src_dir = os.path.join(current_dir, 'src')

if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Now import and run the main module
from ring_mcp.__main__ import main

if __name__ == "__main__":
    main()
'''

    main_py_path = temp_dir / 'main.py'
    main_py_path.write_text(main_py_content)
    print(f"✅ Created main.py entry point at {main_py_path}")

def build_dxt_package(source_dir: Path, output_dir: Path, clean: bool = False):
    """Build the DXT package with proper dependency bundling."""

    print("🚀 Starting DXT package build...")

    if clean and output_dir.exists():
        print(f"🧹 Cleaning output directory: {output_dir}")
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Create temporary directory for building
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        print(f"📁 Using temporary directory: {temp_dir}")

        # Copy source files
        src_dest = temp_dir / 'src'
        shutil.copytree(source_dir / 'src', src_dest)
        print("✅ Copied source files")

        # Copy manifest files
        for file_name in ['manifest.json', 'dxt.json']:
            src_file = source_dir / file_name
            if src_file.exists():
                shutil.copy2(src_file, temp_dir / file_name)
                print(f"✅ Copied {file_name}")

        # Install dependencies to lib directory
        lib_dir = temp_dir / 'lib'
        requirements_file = source_dir / 'requirements.txt'

        if not install_dependencies(lib_dir, requirements_file):
            return False

        # Validate imports
        if not validate_imports(lib_dir, src_dest):
            return False

        # Create main.py entry point
        create_main_py(temp_dir)

        # Create the DXT package (ZIP file)
        package_name = "ring-mcp-server.dxt"
        package_path = output_dir / package_name

        print(f"📦 Creating DXT package: {package_path}")

        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_dir)
                    zf.write(file_path, arcname)
                    print(f"  📄 Added: {arcname}")

        # Get package size
        package_size = package_path.stat().st_size / (1024 * 1024)  # MB
        print(f"✅ DXT package created: {package_name} ({package_size:.2f} MB)")

        # Validate package size (should be > 1MB with dependencies)
        if package_size < 1.0:
            print(f"⚠️  Warning: Package size ({package_size:.2f} MB) seems small. Check if dependencies were bundled correctly.")
        else:
            print(f"✅ Package size looks good ({package_size:.2f} MB) - dependencies likely bundled correctly")

        return True

def main():
    parser = argparse.ArgumentParser(description="Build Ring MCP Server DXT package")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("dist"),
        help="Output directory for DXT package"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean output directory before building"
    )

    args = parser.parse_args()

    # Use the dxt directory as source
    source_dir = Path(__file__).parent
    output_dir = args.output_dir

    print("🏗️  Ring MCP Server - DXT Package Builder")
    print(f"📂 Source directory: {source_dir}")
    print(f"📂 Output directory: {output_dir}")
    print(f"🧹 Clean build: {args.clean}")
    print("-" * 50)

    try:
        success = build_dxt_package(source_dir, output_dir, args.clean)

        if success:
            print("\n🎉 DXT package build completed successfully!")
            print(f"📦 Package location: {output_dir / 'ring-mcp-server.dxt'}")
            print("\n📋 Next steps:")
            print("1. Test the package in Claude Desktop")
            print("2. Verify all tools work correctly")
            print("3. Check that dependencies are properly bundled")
            print("4. Create a GitHub release with the .dxt file")
        else:
            print("\n❌ DXT package build failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️  Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Build failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
