try:
    from sqlalchemy.ext.association_proxy import association_proxy
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
