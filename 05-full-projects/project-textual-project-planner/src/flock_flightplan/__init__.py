
#import debugpy

from flock_flightplan.app import FlightPlanApp


def main() -> None:
    """Run the app."""
    app = FlightPlanApp()
    # debugpy.listen(("0.0.0.0", 5679))
    # print("⏳ Waiting for debugger attach...")
    # debugpy.wait_for_client()
    app.run()
