import os
from supabase import create_client
from datetime import datetime, timedelta

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing Supabase credentials")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
bucket = "video-outputs"

cutoff_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()

try:
    files = supabase.storage.from_(bucket).list()
    deleted = 0
    
    for file in files:
        created_at = file.get('created_at', '')
        if created_at < cutoff_time:
            supabase.storage.from_(bucket).remove([file['name']])
            deleted += 1
            print(f"🗑️ Deleted: {file['name']}")
    
    print(f"✅ Cleanup complete. Deleted {deleted} old videos.")
    
except Exception as e:
    print(f"❌ Error: {e}")
