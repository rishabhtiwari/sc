#!/bin/bash

# Migration script for DesignEditor refactoring
# This script helps you switch between old and new versions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DesignEditor Refactoring Migration Script          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if files exist
if [ ! -f "DesignEditor.jsx" ]; then
    echo -e "${RED}❌ Error: DesignEditor.jsx not found${NC}"
    exit 1
fi

if [ ! -f "DesignEditor.refactored.jsx" ]; then
    echo -e "${RED}❌ Error: DesignEditor.refactored.jsx not found${NC}"
    exit 1
fi

# Show menu
echo -e "${YELLOW}What would you like to do?${NC}"
echo ""
echo "  1) Switch to REFACTORED version (use new hooks)"
echo "  2) Switch to ORIGINAL version (rollback)"
echo "  3) Show current version"
echo "  4) Exit"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
  1)
    echo ""
    echo -e "${YELLOW}⚠️  WARNING: This will replace DesignEditor.jsx with the refactored version${NC}"
    echo -e "${YELLOW}   The current version will be backed up to DesignEditor.old.jsx${NC}"
    echo ""
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
      # Backup current version
      cp DesignEditor.jsx DesignEditor.old.jsx
      echo -e "${GREEN}✅ Backed up current version to DesignEditor.old.jsx${NC}"
      
      # Replace with refactored version
      cp DesignEditor.refactored.jsx DesignEditor.jsx
      echo -e "${GREEN}✅ Switched to REFACTORED version${NC}"
      echo ""
      echo -e "${BLUE}📝 Next steps:${NC}"
      echo "  1. Test all functionality thoroughly"
      echo "  2. If everything works, delete DesignEditor.old.jsx"
      echo "  3. If there are issues, run this script again and choose option 2 to rollback"
    else
      echo -e "${YELLOW}❌ Cancelled${NC}"
    fi
    ;;
    
  2)
    echo ""
    if [ ! -f "DesignEditor.old.jsx" ]; then
      echo -e "${RED}❌ Error: No backup found (DesignEditor.old.jsx)${NC}"
      echo -e "${YELLOW}   Cannot rollback without a backup${NC}"
      exit 1
    fi
    
    echo -e "${YELLOW}⚠️  WARNING: This will restore the original version${NC}"
    echo ""
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
      # Save refactored version
      cp DesignEditor.jsx DesignEditor.refactored.jsx
      echo -e "${GREEN}✅ Saved refactored version to DesignEditor.refactored.jsx${NC}"
      
      # Restore original
      cp DesignEditor.old.jsx DesignEditor.jsx
      echo -e "${GREEN}✅ Restored ORIGINAL version${NC}"
    else
      echo -e "${YELLOW}❌ Cancelled${NC}"
    fi
    ;;
    
  3)
    echo ""
    echo -e "${BLUE}📊 File Status:${NC}"
    echo ""
    
    # Check which version is active
    if cmp -s "DesignEditor.jsx" "DesignEditor.refactored.jsx"; then
      echo -e "  Current version: ${GREEN}REFACTORED${NC}"
    elif [ -f "DesignEditor.old.jsx" ] && cmp -s "DesignEditor.jsx" "DesignEditor.old.jsx"; then
      echo -e "  Current version: ${YELLOW}ORIGINAL${NC}"
    else
      echo -e "  Current version: ${YELLOW}UNKNOWN (modified)${NC}"
    fi
    
    echo ""
    echo "  File sizes:"
    echo "    DesignEditor.jsx:            $(wc -l < DesignEditor.jsx) lines"
    echo "    DesignEditor.refactored.jsx: $(wc -l < DesignEditor.refactored.jsx) lines"
    if [ -f "DesignEditor.old.jsx" ]; then
      echo "    DesignEditor.old.jsx:        $(wc -l < DesignEditor.old.jsx) lines"
    fi
    ;;
    
  4)
    echo -e "${BLUE}👋 Goodbye!${NC}"
    exit 0
    ;;
    
  *)
    echo -e "${RED}❌ Invalid choice${NC}"
    exit 1
    ;;
esac

echo ""
echo -e "${GREEN}✨ Done!${NC}"

