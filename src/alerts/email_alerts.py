import os
import smtplib
import schedule
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv
import threading

# Load environment variables
load_dotenv()

class EmailAlertSystem:
    def __init__(self, db_connection):
        """
        Initialize email alert system for insurance policy expiration notifications
        
        Args:
            db_connection: Database connection object
        """
        self.db = db_connection
        self.smtp_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.alert_email_1 = os.getenv('ALERT_EMAIL_1')
        self.alert_email_2 = os.getenv('ALERT_EMAIL_2')
        
        # Validate configuration
        if not all([self.email_user, self.email_password, self.alert_email_1, self.alert_email_2]):
            print("Warning: Email configuration incomplete. Alerts will not be sent.")
            print("Please set EMAIL_USER, EMAIL_PASSWORD, ALERT_EMAIL_1, and ALERT_EMAIL_2 in .env file")
        
        # Alert thresholds (days before expiration)
        self.alert_thresholds = [60, 30]  # 60 days and 30 days before expiration
        
        # Track sent alerts to avoid duplicates
        self.sent_alerts = set()
        
        # Start background scheduler
        self._start_scheduler()
    
    def _start_scheduler(self):
        """Start the background scheduler for periodic checks"""
        def run_scheduler():
            # Schedule daily checks
            schedule.every().day.at("09:00").do(self.check_expiring_policies)
            
            # Run scheduler
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print("Email alert scheduler started")
    
    def check_expiring_policies(self):
        """Check for policies expiring soon and send alerts"""
        print(f"Checking for expiring policies at {datetime.now()}")
        
        for threshold in self.alert_thresholds:
            expiring_policies = self.db.get_expiring_policies(threshold)
            
            if expiring_policies:
                self._send_expiration_alerts(expiring_policies, threshold)
    
    def _send_expiration_alerts(self, expiring_policies: List[Dict[str, Any]], days_threshold: int):
        """Send alerts for expiring policies"""
        if not self._is_email_configured():
            print("Email not configured, skipping alerts")
            return
        
        # Group policies by agent for better organization
        policies_by_agent = {}
        for policy in expiring_policies:
            agent_name = policy['agent_name']
            if agent_name not in policies_by_agent:
                policies_by_agent[agent_name] = []
            policies_by_agent[agent_name].append(policy)
        
        # Create alert message
        subject = f"Insurance Policy Expiration Alert - {days_threshold} Days"
        
        # Build message body
        message_body = self._create_expiration_alert_message(policies_by_agent, days_threshold)
        
        # Send to both alert recipients
        recipients = [self.alert_email_1, self.alert_email_2]
        
        for recipient in recipients:
            if recipient:
                try:
                    self._send_email(recipient, subject, message_body)
                    print(f"Expiration alert sent to {recipient}")
                except Exception as e:
                    print(f"Failed to send alert to {recipient}: {e}")
    
    def _create_expiration_alert_message(self, policies_by_agent: Dict[str, List[Dict[str, Any]]], 
                                       days_threshold: int) -> str:
        """Create the message body for expiration alerts"""
        message = f"""
Insurance Policy Expiration Alert

This is an automated notification that {len(sum(policies_by_agent.values(), []))} insurance policies 
are expiring in {days_threshold} days or less.

Please review and take appropriate action to ensure continuous coverage.

"""
        
        for agent_name, policies in policies_by_agent.items():
            message += f"\n{agent_name}:\n"
            message += "-" * (len(agent_name) + 1) + "\n"
            
            for policy in policies:
                exp_date = policy['exp_date']
                if isinstance(exp_date, str):
                    exp_date = datetime.strptime(exp_date, '%Y-%m-%d').date()
                
                days_until_expiry = (exp_date - datetime.now().date()).days
                
                message += f"• Building: {policy['building_code']} - {policy['building_name']}\n"
                message += f"  Policy: {policy['policy_number']}\n"
                message += f"  Carrier: {policy['carrier']}\n"
                message += f"  Expires: {exp_date} ({days_until_expiry} days)\n"
                message += f"  Premium: ${policy['premium']:,.2f}\n"
                message += "\n"
        
        message += """
Action Required:
1. Contact the policyholder to discuss renewal options
2. Review coverage needs and make recommendations
3. Process renewal applications if applicable
4. Update policy information in the system

This alert was generated automatically by the Insurance Master system.
Please do not reply to this email.

Best regards,
Insurance Master System
"""
        
        return message
    
    def _send_email(self, recipient: str, subject: str, message_body: str):
        """Send an email using SMTP"""
        if not self._is_email_configured():
            raise ValueError("Email not properly configured")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.email_user
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(message_body, 'plain'))
        
        # Send email
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
    
    def _is_email_configured(self) -> bool:
        """Check if email is properly configured"""
        return all([
            self.email_user,
            self.email_password,
            self.alert_email_1,
            self.alert_email_2
        ])
    
    def send_custom_alert(self, recipient: str, subject: str, message: str):
        """Send a custom alert message"""
        try:
            self._send_email(recipient, subject, message)
            print(f"Custom alert sent to {recipient}")
            return True
        except Exception as e:
            print(f"Failed to send custom alert: {e}")
            return False
    
    def send_test_email(self, recipient: str = None):
        """Send a test email to verify configuration"""
        if not recipient:
            recipient = self.alert_email_1
        
        if not recipient:
            print("No recipient specified for test email")
            return False
        
        subject = "Insurance Master - Test Email"
        message = """
This is a test email from the Insurance Master system.

If you received this email, the email configuration is working correctly.

Best regards,
Insurance Master System
"""
        
        try:
            self._send_email(recipient, subject, message)
            print(f"Test email sent successfully to {recipient}")
            return True
        except Exception as e:
            print(f"Test email failed: {e}")
            return False
    
    def get_alert_status(self) -> Dict[str, Any]:
        """Get the current status of the alert system"""
        status = {
            'email_configured': self._is_email_configured(),
            'smtp_host': self.smtp_host,
            'smtp_port': self.smtp_port,
            'email_user': self.email_user,
            'alert_recipients': [self.alert_email_1, self.alert_email_2],
            'alert_thresholds': self.alert_thresholds,
            'scheduler_running': True,
            'last_check': datetime.now().isoformat()
        }
        
        # Check for policies expiring soon
        try:
            expiring_60 = self.db.get_expiring_policies(60)
            expiring_30 = self.db.get_expiring_policies(30)
            
            status['policies_expiring_60_days'] = len(expiring_60)
            status['policies_expiring_30_days'] = len(expiring_30)
            status['total_expiring_soon'] = len(expiring_60) + len(expiring_30)
        except Exception as e:
            status['error'] = str(e)
        
        return status
    
    def manual_check_expiring_policies(self):
        """Manually trigger a check for expiring policies"""
        print("Manual check for expiring policies triggered")
        self.check_expiring_policies()
    
    def update_alert_thresholds(self, new_thresholds: List[int]):
        """Update the alert thresholds"""
        if not new_thresholds or not all(isinstance(t, int) and t > 0 for t in new_thresholds):
            raise ValueError("Thresholds must be a list of positive integers")
        
        self.alert_thresholds = sorted(new_thresholds, reverse=True)
        print(f"Alert thresholds updated to: {self.alert_thresholds}")
    
    def add_alert_recipient(self, email: str):
        """Add a new alert recipient"""
        if not self.alert_email_1:
            self.alert_email_1 = email
        elif not self.alert_email_2:
            self.alert_email_2 = email
        else:
            print("Maximum of 2 alert recipients allowed")
            return False
        
        print(f"Alert recipient added: {email}")
        return True
    
    def remove_alert_recipient(self, email: str):
        """Remove an alert recipient"""
        if self.alert_email_1 == email:
            self.alert_email_1 = None
            print(f"Alert recipient removed: {email}")
            return True
        elif self.alert_email_2 == email:
            self.alert_email_2 = None
            print(f"Alert recipient removed: {email}")
            return True
        else:
            print(f"Email {email} not found in alert recipients")
            return False
