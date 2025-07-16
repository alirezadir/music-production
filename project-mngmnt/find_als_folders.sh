#!/bin/bash

# Find all folders containing Ableton project files (.als)
find "${1:-.}" -type f -name "*.als" -exec dirname {} \; | sort -u
