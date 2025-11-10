"""Test file for find_packages_in_current_file function.

This file is isolated to avoid import pollution and accurately test
the package detection functionality.
"""
import os
import sys
import json
from pathlib import Path
from typing import TYPE_CHECKING
from d3blobgen.core import find_packages_in_current_file
from d3blobgen import core

# These imports should be detected
import pytest
import requests
from collections import defaultdict

# This import is in TYPE_CHECKING block and should NOT be detected
if TYPE_CHECKING:
    from typing import Optional
    import typing_extensions

import io,\
    time

# This import should be handled correctly
from os import scandir,\
    sched_get_priority_max

from os import (
    abort,
    access,
)

class TestFindPackagesInCurrentFile:
    """Test suite for find_packages_in_current_file function."""

    def test_basic_imports_detected(self):
        """Test that basic imports are correctly detected."""
        packages = find_packages_in_current_file()

        # These should be detected
        assert "import os" in packages
        assert "import sys" in packages
        assert "import json" in packages
        assert "import pytest" in packages
        assert "import requests" in packages

    def test_from_imports_detected(self):
        """Test that 'from X import Y' statements are correctly detected."""
        packages = find_packages_in_current_file()

        # These should be detected
        assert "from pathlib import Path" in packages
        assert "from collections import defaultdict" in packages

    def test_type_checking_imports_filtered(self):
        """Test that imports inside TYPE_CHECKING blocks are filtered out."""
        packages = find_packages_in_current_file()

        # These should NOT be detected (they're in TYPE_CHECKING block)
        assert "from typing import Optional" not in packages
        assert "import typing_extensions" not in packages

        # All typing related packages should not be detected
        assert "from typing import TYPE_CHECKING" not in packages

    def test_d3blobgen_imports_filtered(self):
        """Test that imports from d3blobgen package are filtered out."""
        packages = find_packages_in_current_file()

        # This should NOT be detected (d3blobgen package)
        assert not any("d3blobgen" in pkg for pkg in packages)

    def test_function_itself_not_imported(self):
        """Test that find_packages_in_current_file itself is filtered out."""
        packages = find_packages_in_current_file()

        # The function itself should be filtered
        assert not any("find_packages_in_current_file" in pkg for pkg in packages)

    def test_import_with_reverse_slash(self):
        packages = find_packages_in_current_file()
        assert "import io, time" in packages

    def test_from_import_with_reverse_slash(self):
        packages = find_packages_in_current_file()
        assert "from os import scandir, sched_get_priority_max" in packages

    def test_reverse_import_with_parenthesis(self):
        packages = find_packages_in_current_file()
        assert "from os import abort, access" in packages

    def test_return_type_is_list(self):
        """Test that the function returns a list."""
        packages = find_packages_in_current_file()
        assert isinstance(packages, list)

    def test_return_type_contains_strings(self):
        """Test that all items in the returned list are strings."""
        packages = find_packages_in_current_file()
        assert all(isinstance(pkg, str) for pkg in packages)

    def test_no_duplicates(self):
        """Test that the returned list has no duplicate entries."""
        packages = find_packages_in_current_file()
        assert len(packages) == len(set(packages))

    def test_sorted_output(self):
        """Test that the returned list is sorted."""
        packages = find_packages_in_current_file()
        assert packages == sorted(packages)
