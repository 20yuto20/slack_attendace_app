import json
from firebase_functions import https_fn, scheduler_fn
from slack_sdk import WebClient

from .repositories.firestore_repository import FirestoreRepository
from .services.warning_service import WarningService
from .config import get_config
from .slack.message_builder import MessageBuilder

# Define the alert function directly (not inside another function)
@scheduler_fn.on_schedule(schedule="every 30 minutes")
def attendance_alerts_function(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Scheduled function that checks for long work/break periods and sends warnings
    
    Args:
        event: Schedule event context
    """
    try:
        # Get configuration
        config = get_config()
        
        # Check if alerts are enabled
        if not getattr(config.attendance_alerts, 'enabled', False):
            print("Attendance alerts are disabled in configuration")
            return
            
        print("Running attendance alerts check...")
        
        # Initialize repository and service
        repository = FirestoreRepository(
            project_id=config.firebase.project_id,
            credentials_path=config.firebase.credentials_path
        )
        
        # Initialize warning service
        warning_service = WarningService(repository)
        
        # Get all workspaces (for future multi-workspace support)
        workspaces = repository.get_all_workspaces()
        
        for workspace in workspaces:
            team_id = workspace.get('team_id')
            if not team_id:
                continue
                
            # Get warnings for this workspace
            warnings = warning_service.get_all_warnings(team_id=team_id)
            
            if not warnings:
                print(f"No warnings for workspace {team_id}")
                continue
            
            print(f"Found {len(warnings)} warnings for workspace {team_id}")
            
            # Initialize Slack client
            slack_client = WebClient(token=config.slack.bot_token)
            
            # Send warnings to each user
            for warning in warnings:
                try:
                    # Format warning message (text)
                    text_message = warning_service.format_warning_message(warning)
                    
                    # Generate warning blocks (rich message)
                    blocks = MessageBuilder.create_warning_message(
                        warning_type=warning['warning_type'],
                        user_id=warning['user_id'],
                        user_name=warning['user_name'],
                        duration=warning['duration']
                    )
                    
                    # Send DM with warning
                    slack_client.chat_postMessage(
                        channel=warning['user_id'],
                        text=text_message,
                        blocks=blocks
                    )
                    
                    print(f"Sent warning to user {warning['user_id']} for {warning['warning_type']}")
                except Exception as e:
                    print(f"Error sending warning to user {warning['user_id']}: {str(e)}")
        
        print("Attendance alerts check completed")
    except Exception as e:
        print(f"Error in attendance_alerts_function: {str(e)}")

# Manual execution endpoint (for debugging and testing)
@https_fn.on_request()
def manual_attendance_alerts(request: https_fn.Request) -> https_fn.Response:
    """
    HTTP endpoint to manually trigger attendance alerts check
    For debugging and testing purposes
    
    Args:
        request: HTTP request
        
    Returns:
        Response: Check results
    """
    try:
        config = get_config()
        
        # Simple API key authentication (optional)
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key != getattr(config, 'debug_api_key', ''):
            return https_fn.Response(
                json.dumps({"error": "Unauthorized"}),
                status=401,
                mimetype='application/json'
            )
        
        # Initialize repository and service
        repository = FirestoreRepository(
            project_id=config.firebase.project_id,
            credentials_path=config.firebase.credentials_path
        )
        
        # Initialize warning service
        warning_service = WarningService(repository)
        
        # Get all warnings across all workspaces
        warnings = warning_service.get_all_warnings()
        
        # Return results
        return https_fn.Response(
            json.dumps({
                "success": True,
                "warnings_count": len(warnings),
                "warnings": [
                    {
                        "user_id": w["user_id"],
                        "user_name": w["user_name"],
                        "warning_type": w["warning_type"],
                        "duration": w["duration"]
                    } for w in warnings
                ]
            }),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        return https_fn.Response(
            json.dumps({
                "error": "Internal Server Error",
                "message": str(e)
            }),
            status=500,
            mimetype='application/json'
        )