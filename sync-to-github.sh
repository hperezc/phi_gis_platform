#!/bin/bash

echo " Syncing changes to GitHub..."

cd /opt/phi_gis_platform

# Clean up temporary files first
rm -rf next
rm -rf temp_*
rm -f *.backup*
rm -f .tar.gz

# Check if there are changes
if [[ -n $(git status --porcelain) ]]; then
    echo "📝 Changes detected, committing..."
    
    # Add all changes except temporary files
    git add .
    git reset -- .tar.gz
    git reset -- *.backup*
    git reset -- temp_*
    git reset -- "aux | grep"
    git reset -- "e up -d"
    git reset -- "frontend@0.1.0"
    git reset -- "next"
    git reset -- "udo systemctl"
    git reset -- "ystemctl stop"
    git reset -- "EXTRA:"
    git reset -- "next.config.mjsY"
    git reset -- "udo systemctl status nginx"
    git reset -- "ystemctl stop geoportal.service"
    git reset -- "temp_mapupdater.jsx"
    
    # Commit with timestamp
    git commit -m "Server update: $(date '+%Y-%m-%d %H:%M:%S') - $(git status --porcelain | wc -l) files changed"
    
    # Push to GitHub
    git push origin main
    
    echo "✅ Changes synced to GitHub successfully!"
else
    echo "✅ No changes to sync"
fi
