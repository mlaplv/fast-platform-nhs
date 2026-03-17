import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from backend.controllers.order import OrderController
    print("Successfully imported OrderController")
    import annotationlib
    for name, method in OrderController.__dict__.items():
        if callable(method) and not name.startswith("__"):
            try:
                ann = annotationlib.get_annotations(method)
                print(f"Annotations for {name}: {ann}")
            except Exception as e:
                print(f"Error getting annotations for {name}: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
