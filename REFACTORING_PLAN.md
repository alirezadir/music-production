# Refactoring Plan

## Phase 1: Critical Fixes (Immediate)

### 1.1 Fix Hardcoded Paths
- [x] Create configuration system
- [ ] Update `tag-sounds/config.py` to use environment variables
- [ ] Update `project-mngmnt/organize_music.py` to accept paths as arguments
- [ ] Create `.env.example` template

### 1.2 Package Structure
- [ ] Add `__init__.py` files to all modules
- [ ] Create shared `utils/` module with common functions
- [ ] Organize imports properly

### 1.3 Consolidate Duplicate Code
- [ ] Merge `analyze_samples*.py` into single file with options
- [ ] Merge `count_file_types*.py` into single file
- [ ] Merge `delete_asd_files*.py` into single file
- [ ] Choose Python over Shell for `organize_music`

## Phase 2: Code Quality (Short-term)

### 2.1 Dependencies
- [ ] Create root `requirements.txt`
- [ ] Create `setup.py` or `pyproject.toml`
- [ ] Document optional dependencies

### 2.2 Error Handling
- [ ] Add try/except blocks to file operations
- [ ] Add input validation
- [ ] Improve error messages

### 2.3 Code Style
- [ ] Add type hints
- [ ] Format code with black
- [ ] Add docstrings

## Phase 3: Enhancements (Long-term)

### 3.1 Testing
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Create test fixtures

### 3.2 Documentation
- [ ] API documentation
- [ ] User guides
- [ ] Architecture docs

### 3.3 CLI Interface
- [ ] Unified CLI with click/argparse
- [ ] Subcommands for each module
- [ ] Better UX

