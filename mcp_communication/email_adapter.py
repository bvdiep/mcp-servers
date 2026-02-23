"""
Email Adapter - Standalone version for MCP Communication Server
"""
import imaplib
import email
from email.header import decode_header
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class EmailAdapter:
    """Adapter for reading emails via IMAP"""
    
    def __init__(self, imap_server: str, username: str, password: str):
        self.imap_server = imap_server
        self.username = username
        self.password = password
        self.mailbox = None
    
    def connect(self):
        """Connect to email server"""
        try:
            self.mailbox = imaplib.IMAP4_SSL(self.imap_server)
            self.mailbox.login(self.username, self.password)
            return True
        except Exception as e:
            logger.error(f"Email connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from email server"""
        if self.mailbox:
            try:
                self.mailbox.logout()
            except:
                pass
    
    def get_recent_emails(self, folders: List[str] = None, n_hours: int = 12) -> List[Dict]:
        """Get recent emails from specified folders"""
        if not folders:
            folders = ['INBOX', 'Notification', 'Newsletter']
        
        if not self.mailbox and not self.connect():
            return []
        
        emails = []
        now_utc = datetime.now(timezone.utc)
        threshold_time = now_utc - timedelta(hours=n_hours)
        
        for folder in folders:
            try:
                status, _ = self.mailbox.select(folder)
                if status != 'OK':
                    continue
                
                # Search for recent emails
                search_date = (threshold_time - timedelta(days=1)).strftime("%d-%b-%Y")
                status, message_ids = self.mailbox.search(None, f'SINCE {search_date}')
                
                if status != 'OK':
                    continue
                
                for msg_id in message_ids[0].split()[-30:]:  # Limit to 30 most recent
                    status, msg_data = self.mailbox.fetch(msg_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    # Parse email
                    subject = self._get_subject(msg)
                    from_addr = msg.get('From', '')
                    date = msg.get('Date', '')
                    
                    # Get body
                    body = self._get_body(msg)
                    
                    # Parse date
                    try:
                        email_date = email.utils.parsedate_to_datetime(date)
                        if email_date.replace(tzinfo=timezone.utc) >= threshold_time:
                            emails.append({
                                "folder": folder,
                                "subject": subject,
                                "from": from_addr,
                                "date": date,
                                "body": body[:2000]  # Limit body length
                            })
                    except:
                        pass
            
            except Exception as e:
                logger.error(f"Error reading folder {folder}: {e}")
        
        self.disconnect()
        return emails
    
    def _get_subject(self, msg) -> str:
        """Decode email subject"""
        subject = msg.get('Subject', '')
        if subject:
            decoded = decode_header(subject)
            subject = ''
            for part, encoding in decoded:
                if isinstance(part, bytes):
                    subject += part.decode(encoding or 'utf-8', errors='replace')
                else:
                    subject += part
        return subject or "No Subject"
    
    def _get_body(self, msg) -> str:
        """Extract email body"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors='replace')
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors='replace')
        
        return body


async def read_emails(
    imap_server: str,
    username: str,
    password: str,
    n_hours: int = 12
) -> Dict[str, Any]:
    """Read recent emails"""
    if not username or not password:
        return {
            "type": "text",
            "text": "Chưa cấu hình EMAIL_USERNAME và EMAIL_APP_PASSWORD",
            "photos": []
        }
    
    adapter = EmailAdapter(imap_server, username, password)
    emails = adapter.get_recent_emails(n_hours=n_hours)
    
    if not emails:
        return {
            "type": "text",
            "text": f"Không tìm thấy email mới nào trong {n_hours} giờ qua",
            "photos": []
        }
    
    output = f"Tìm thấy {len(emails)} email trong {n_hours} giờ qua:\n\n"
    
    for i, email_data in enumerate(emails[:10], 1):
        output += f"--- Email {i} ---\n"
        output += f"Thư mục: {email_data['folder']}\n"
        output += f"Tiêu đề: {email_data['subject']}\n"
        output += f"Từ: {email_data['from']}\n"
        output += f"Nội dung: {email_data['body'][:500]}...\n\n"
    
    return {
        "type": "text",
        "text": output,
        "photos": []
    }
