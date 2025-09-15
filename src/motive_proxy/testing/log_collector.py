"""Log collection and analysis for E2E testing."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class LogCollector:
    """Collects and manages logs during E2E testing."""
    
    def __init__(self):
        """Initialize log collector."""
        self.logs: List[Dict[str, Any]] = []
    
    def add_log(self, session_id: str, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a log entry.
        
        Args:
            session_id: Session identifier
            level: Log level (info, warning, error, debug)
            message: Log message
            metadata: Additional metadata
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "level": level,
            "message": message,
            "metadata": metadata or {}
        }
        self.logs.append(log_entry)
    
    def filter_logs(self, session_id: Optional[str] = None, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filter logs by criteria.
        
        Args:
            session_id: Filter by session ID
            level: Filter by log level
            
        Returns:
            Filtered log entries
        """
        filtered_logs = self.logs
        
        if session_id:
            filtered_logs = [log for log in filtered_logs if log["session_id"] == session_id]
        
        if level:
            filtered_logs = [log for log in filtered_logs if log["level"] == level]
        
        return filtered_logs
    
    def export_logs(self, output_path: Path) -> None:
        """Export logs to centralized logs directory and specified path.
        
        Args:
            output_path: Path to output file (for backward compatibility)
        """
        # Save to centralized logs directory
        logs_dir = Path("logs/e2e-tests")
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        centralized_log_file = logs_dir / f"e2e_test_{timestamp}.json"
        
        with open(centralized_log_file, 'w') as f:
            json.dump(self.logs, f, indent=2)
        
        # Also save to specified output path for backward compatibility
        with open(output_path, 'w') as f:
            json.dump(self.logs, f, indent=2)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get log summary statistics.
        
        Returns:
            Summary statistics
        """
        if not self.logs:
            return {"total_logs": 0}
        
        levels = {}
        sessions = set()
        
        for log in self.logs:
            level = log["level"]
            levels[level] = levels.get(level, 0) + 1
            sessions.add(log["session_id"])
        
        return {
            "total_logs": len(self.logs),
            "unique_sessions": len(sessions),
            "log_levels": levels,
            "first_log": self.logs[0]["timestamp"] if self.logs else None,
            "last_log": self.logs[-1]["timestamp"] if self.logs else None
        }
    
    def clear(self) -> None:
        """Clear all logs."""
        self.logs.clear()
