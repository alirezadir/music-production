"""Script to sync all CSV files to Google Sheets."""
import os
from sheets_client import get_sheets_client


def main():
    """Main function to sync all CSVs to Google Sheets."""
    # Get sheets client
    client = get_sheets_client()
    
    if not client:
        print("Google Sheets credentials not configured.")
        print("Set GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_SHEET_URL environment variables.")
        return
    
    # Define CSV paths and corresponding tab names
    os.makedirs("out", exist_ok=True)
    csv_tabs = [
        ("out/artists.csv", "artists", ["artist_name"]),
        ("out/labels.csv", "labels", ["b_label_name", "associated_a_label"]),  # New format uses b_label_name
        ("out/tracks.csv", "tracks", ["track_url"]),
    ]
    
    # Resolve CSV paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    for csv_file, tab_name, key_columns in csv_tabs:
        csv_path = os.getenv(
            csv_file.replace(".csv", "").upper().replace("-", "_") + "_CSV",
            csv_file
        )
        
        # Resolve relative paths
        if not os.path.isabs(csv_path):
            csv_path = os.path.join(project_root, csv_path)
        
        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            continue
        
        print(f"Syncing {csv_file} to '{tab_name}' tab...")
        try:
            client.sync_csv_to_sheet(csv_path, tab_name, key_columns)
            print(f"  ✓ Successfully synced {csv_file}")
        except Exception as e:
            print(f"  ✗ Error syncing {csv_file}: {e}")
    
    print("\nDone syncing all CSV files to Google Sheets!")


if __name__ == "__main__":
    main()

