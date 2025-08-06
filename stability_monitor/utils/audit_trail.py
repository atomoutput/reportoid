"""
Audit Trail System for tracking manual data quality corrections and reviews
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

class AuditAction:
    """Represents an audit trail action"""
    
    def __init__(self, action_id: str, action_type: str, user: str, timestamp: datetime,
                 description: str, details: Dict[str, Any], affected_tickets: List[str]):
        self.action_id = action_id
        self.action_type = action_type  # 'merge_duplicates', 'dismiss_duplicates', 'manual_correction'
        self.user = user
        self.timestamp = timestamp
        self.description = description
        self.details = details
        self.affected_tickets = affected_tickets
        self.reversible = action_type in ['merge_duplicates', 'dismiss_duplicates']

class AuditTrailManager:
    """Manages audit trail for data quality operations"""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Database configuration
        audit_config = settings.get("audit_trail", {
            "enabled": True,
            "database_path": "data_quality_audit.db",
            "max_entries": 10000,
            "retention_days": 365
        })
        
        self.enabled = audit_config.get("enabled", True)
        self.db_path = audit_config.get("database_path", "data_quality_audit.db")
        self.max_entries = audit_config.get("max_entries", 10000)
        self.retention_days = audit_config.get("retention_days", 365)
        
        if self.enabled:
            self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database for audit trail"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS audit_trail (
                        action_id TEXT PRIMARY KEY,
                        action_type TEXT NOT NULL,
                        user_name TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        description TEXT NOT NULL,
                        details TEXT NOT NULL,
                        affected_tickets TEXT NOT NULL,
                        reversible BOOLEAN NOT NULL,
                        reversed BOOLEAN DEFAULT FALSE,
                        reversed_by TEXT,
                        reversed_at DATETIME
                    )
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_trail(timestamp)
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_action_type ON audit_trail(action_type)
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_user ON audit_trail(user_name)
                ''')
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize audit database: {e}")
            self.enabled = False
    
    def log_action(self, action: AuditAction) -> bool:
        """Log an audit action to the database"""
        if not self.enabled:
            return True
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO audit_trail 
                    (action_id, action_type, user_name, timestamp, description, details, 
                     affected_tickets, reversible)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    action.action_id,
                    action.action_type,
                    action.user,
                    action.timestamp.isoformat(),
                    action.description,
                    json.dumps(action.details),
                    json.dumps(action.affected_tickets),
                    action.reversible
                ))
                conn.commit()
                
            self.logger.info(f"Audit action logged: {action.action_type} by {action.user}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log audit action: {e}")
            return False
    
    def get_audit_history(self, limit: int = 100, action_type: str = None, 
                         user: str = None) -> List[AuditAction]:
        """Retrieve audit history with optional filters"""
        if not self.enabled:
            return []
        
        try:
            query = '''
                SELECT action_id, action_type, user_name, timestamp, description, 
                       details, affected_tickets, reversible, reversed, reversed_by, reversed_at
                FROM audit_trail
                WHERE 1=1
            '''
            params = []
            
            if action_type:
                query += " AND action_type = ?"
                params.append(action_type)
            
            if user:
                query += " AND user_name = ?"
                params.append(user)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                actions = []
                for row in rows:
                    action_id, action_type, user_name, timestamp, description, details, affected_tickets, reversible, reversed, reversed_by, reversed_at = row
                    
                    action = AuditAction(
                        action_id=action_id,
                        action_type=action_type,
                        user=user_name,
                        timestamp=datetime.fromisoformat(timestamp),
                        description=description,
                        details=json.loads(details),
                        affected_tickets=json.loads(affected_tickets)
                    )
                    action.reversible = bool(reversible)
                    action.reversed = bool(reversed)
                    action.reversed_by = reversed_by
                    action.reversed_at = datetime.fromisoformat(reversed_at) if reversed_at else None
                    
                    actions.append(action)
                
                return actions
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve audit history: {e}")
            return []
    
    def reverse_action(self, action_id: str, user: str, reason: str) -> bool:
        """Reverse a previously logged action"""
        if not self.enabled:
            return True
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if action exists and is reversible
                cursor = conn.execute('''
                    SELECT action_type, reversible, reversed 
                    FROM audit_trail 
                    WHERE action_id = ?
                ''', (action_id,))
                
                row = cursor.fetchone()
                if not row:
                    self.logger.warning(f"Action {action_id} not found for reversal")
                    return False
                
                action_type, reversible, reversed = row
                
                if not reversible:
                    self.logger.warning(f"Action {action_id} is not reversible")
                    return False
                
                if reversed:
                    self.logger.warning(f"Action {action_id} already reversed")
                    return False
                
                # Mark as reversed
                conn.execute('''
                    UPDATE audit_trail 
                    SET reversed = TRUE, reversed_by = ?, reversed_at = ?
                    WHERE action_id = ?
                ''', (user, datetime.now().isoformat(), action_id))
                
                # Log the reversal as a new action
                reversal_action = AuditAction(
                    action_id=f"REV_{action_id}",
                    action_type="reversal",
                    user=user,
                    timestamp=datetime.now(),
                    description=f"Reversed action {action_id}: {reason}",
                    details={"original_action_id": action_id, "reason": reason},
                    affected_tickets=[]
                )
                
                conn.execute('''
                    INSERT INTO audit_trail 
                    (action_id, action_type, user_name, timestamp, description, details, 
                     affected_tickets, reversible)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    reversal_action.action_id,
                    reversal_action.action_type,
                    reversal_action.user,
                    reversal_action.timestamp.isoformat(),
                    reversal_action.description,
                    json.dumps(reversal_action.details),
                    json.dumps(reversal_action.affected_tickets),
                    False  # Reversals are not reversible
                ))
                
                conn.commit()
                
            self.logger.info(f"Action {action_id} reversed by {user}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reverse action {action_id}: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit trail statistics"""
        if not self.enabled:
            return {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total actions
                cursor = conn.execute("SELECT COUNT(*) FROM audit_trail")
                total_actions = cursor.fetchone()[0]
                
                # Actions by type
                cursor = conn.execute('''
                    SELECT action_type, COUNT(*) 
                    FROM audit_trail 
                    GROUP BY action_type 
                    ORDER BY COUNT(*) DESC
                ''')
                actions_by_type = dict(cursor.fetchall())
                
                # Actions by user
                cursor = conn.execute('''
                    SELECT user_name, COUNT(*) 
                    FROM audit_trail 
                    GROUP BY user_name 
                    ORDER BY COUNT(*) DESC
                ''')
                actions_by_user = dict(cursor.fetchall())
                
                # Recent activity (last 7 days)
                seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
                cursor = conn.execute('''
                    SELECT COUNT(*) 
                    FROM audit_trail 
                    WHERE timestamp > ?
                ''', (seven_days_ago,))
                recent_activity = cursor.fetchone()[0]
                
                # Reversed actions
                cursor = conn.execute("SELECT COUNT(*) FROM audit_trail WHERE reversed = TRUE")
                reversed_actions = cursor.fetchone()[0]
                
                return {
                    "total_actions": total_actions,
                    "actions_by_type": actions_by_type,
                    "actions_by_user": actions_by_user,
                    "recent_activity_7days": recent_activity,
                    "reversed_actions": reversed_actions,
                    "database_size": os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get audit statistics: {e}")
            return {}
    
    def cleanup_old_entries(self) -> int:
        """Clean up old audit entries beyond retention period"""
        if not self.enabled:
            return 0
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    DELETE FROM audit_trail 
                    WHERE timestamp < ? AND reversed = FALSE
                ''', (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old audit entries")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old audit entries: {e}")
            return 0
    
    def export_audit_log(self, output_path: str, format: str = "csv") -> bool:
        """Export audit log to CSV or JSON format"""
        if not self.enabled:
            return False
        
        try:
            actions = self.get_audit_history(limit=10000)  # Get all actions
            
            if format.lower() == "csv":
                import csv
                
                with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['action_id', 'action_type', 'user', 'timestamp', 
                                'description', 'affected_tickets', 'reversed']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for action in actions:
                        writer.writerow({
                            'action_id': action.action_id,
                            'action_type': action.action_type,
                            'user': action.user,
                            'timestamp': action.timestamp.isoformat(),
                            'description': action.description,
                            'affected_tickets': ', '.join(action.affected_tickets),
                            'reversed': getattr(action, 'reversed', False)
                        })
                        
            elif format.lower() == "json":
                export_data = []
                for action in actions:
                    export_data.append({
                        'action_id': action.action_id,
                        'action_type': action.action_type,
                        'user': action.user,
                        'timestamp': action.timestamp.isoformat(),
                        'description': action.description,
                        'details': action.details,
                        'affected_tickets': action.affected_tickets,
                        'reversed': getattr(action, 'reversed', False)
                    })
                
                with open(output_path, 'w', encoding='utf-8') as jsonfile:
                    json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Exported {len(actions)} audit entries to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export audit log: {e}")
            return False

from datetime import timedelta  # Add missing import