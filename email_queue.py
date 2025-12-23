"""
Persistent email queue for guaranteed delivery.

This module provides a persistent queue system for failed email attempts,
ensuring that PDF reports are eventually delivered even if initial attempts fail.

The EmailQueue class:
- Stores failed email metadata and PDF data in JSON and filesystem
- Supports retry processing on application startup
- Provides persistence across application restarts
"""

import json
import os
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class EmailQueue:
    """Manages persistent queue of failed email attempts."""
    
    QUEUE_FILE = "failed_emails.json"
    
    def __init__(self, queue_dir: str = "SMTP logs"):
        """
        Initialize email queue.
        
        Args:
            queue_dir: Directory to store queue file and PDFs (default: "SMTP logs")
        """
        self.queue_path = Path(queue_dir) / self.QUEUE_FILE
        self.queue_dir = Path(queue_dir)
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Email queue initialized at: {self.queue_path}")
        
    def add(self, pdf_data: bytes, filename: str, recipient: str, 
            student_name: str, session_type: str) -> str:
        """
        Add failed email to queue.
        
        Args:
            pdf_data: Raw PDF file data as bytes
            filename: Name of the PDF file
            recipient: Email recipient address (Box email)
            student_name: Name of the student
            session_type: Type of MI session
            
        Returns:
            Queue entry ID (UUID)
        """
        queue = self._load()
        entry_id = str(uuid.uuid4())
        
        # Save PDF to disk
        pdf_path = self._save_pdf(entry_id, pdf_data)
        
        entry = {
            'id': entry_id,
            'filename': filename,
            'recipient': recipient,
            'student_name': student_name,
            'session_type': session_type,
            'timestamp': datetime.now().isoformat(),
            'retry_count': 0,
            'pdf_path': str(pdf_path)
        }
        
        queue.append(entry)
        self._save(queue)
        
        logger.info(f"Added email to queue: {entry_id} - {filename} for {student_name}")
        return entry_id
    
    def get_pending(self) -> List[Dict]:
        """
        Get all pending emails in queue.
        
        Returns:
            List of queue entry dictionaries
        """
        queue = self._load()
        logger.info(f"Retrieved {len(queue)} pending emails from queue")
        return queue
    
    def remove(self, entry_id: str) -> bool:
        """
        Remove processed email from queue.
        
        Args:
            entry_id: Queue entry ID to remove
            
        Returns:
            True if entry was found and removed, False otherwise
        """
        queue = self._load()
        original_len = len(queue)
        
        # Find and remove entry
        removed_entry = None
        queue = [e for e in queue if e.get('id') != entry_id]
        
        if len(queue) < original_len:
            # Delete associated PDF file
            for entry in self._load():
                if entry.get('id') == entry_id:
                    removed_entry = entry
                    break
            
            if removed_entry and 'pdf_path' in removed_entry:
                pdf_path = Path(removed_entry['pdf_path'])
                if pdf_path.exists():
                    try:
                        pdf_path.unlink()
                        logger.debug(f"Deleted PDF file: {pdf_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete PDF file {pdf_path}: {e}")
            
            self._save(queue)
            logger.info(f"Removed email from queue: {entry_id}")
            return True
        
        logger.warning(f"Email queue entry not found: {entry_id}")
        return False
    
    def increment_retry_count(self, entry_id: str) -> Optional[int]:
        """
        Increment retry count for a queue entry.
        
        Args:
            entry_id: Queue entry ID
            
        Returns:
            New retry count, or None if entry not found
        """
        queue = self._load()
        
        for entry in queue:
            if entry.get('id') == entry_id:
                entry['retry_count'] = entry.get('retry_count', 0) + 1
                entry['last_retry'] = datetime.now().isoformat()
                self._save(queue)
                logger.info(f"Incremented retry count for {entry_id}: {entry['retry_count']}")
                return entry['retry_count']
        
        return None
    
    def _load(self) -> List[Dict]:
        """Load queue from JSON file."""
        if self.queue_path.exists():
            try:
                with open(self.queue_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode queue file: {e}. Starting with empty queue.")
                return []
            except Exception as e:
                logger.error(f"Failed to load queue file: {e}. Starting with empty queue.")
                return []
        return []
    
    def _save(self, queue: List[Dict]) -> None:
        """Save queue to JSON file."""
        try:
            with open(self.queue_path, 'w') as f:
                json.dump(queue, f, indent=2)
            logger.debug(f"Saved queue with {len(queue)} entries")
        except Exception as e:
            logger.error(f"Failed to save queue file: {e}")
    
    def _save_pdf(self, entry_id: str, pdf_data: bytes) -> Path:
        """
        Save PDF data to disk.
        
        Args:
            entry_id: Queue entry ID
            pdf_data: Raw PDF bytes
            
        Returns:
            Path to saved PDF file
        """
        pdf_path = self.queue_dir / f"queued_{entry_id}.pdf"
        
        try:
            with open(pdf_path, 'wb') as f:
                f.write(pdf_data)
            logger.debug(f"Saved PDF to: {pdf_path}")
            return pdf_path
        except Exception as e:
            logger.error(f"Failed to save PDF {pdf_path}: {e}")
            raise
    
    def get_queue_size(self) -> int:
        """Get number of pending emails in queue."""
        return len(self._load())
    
    def clear_all(self) -> int:
        """
        Clear all entries from queue (for maintenance/testing).
        
        Returns:
            Number of entries cleared
        """
        queue = self._load()
        count = len(queue)
        
        # Delete all PDF files
        for entry in queue:
            if 'pdf_path' in entry:
                pdf_path = Path(entry['pdf_path'])
                if pdf_path.exists():
                    try:
                        pdf_path.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to delete PDF {pdf_path}: {e}")
        
        # Clear queue
        self._save([])
        logger.info(f"Cleared {count} entries from queue")
        return count
