"""
Email notification service using AWS SES
Handles role-based notifications for inspection workflow
"""
import boto3
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from botocore.exceptions import ClientError
from jinja2 import Template
import json

logger = logging.getLogger(__name__)

class EmailService:
    """AWS SES email service for Fire Safety Suite notifications"""
    
    def __init__(self):
        self.sender_email = os.environ.get('SENDER_EMAIL', 'noreply@madoc.gov')
        self.region = os.environ.get('AWS_SES_REGION', 'us-east-1')
        
        # Initialize SES client
        self.ses_client = boto3.client(
            'ses',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=self.region
        )
        
        # Email templates
        self.templates = self._load_email_templates()
    
    def _load_email_templates(self) -> Dict[str, Dict[str, str]]:
        """Load email templates for different notification types"""
        return {
            "inspection_submitted": {
                "subject": "Fire Safety Inspection Submitted - #{{ inspection_id }}",
                "html": """
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                            <h1 style="margin: 0; font-size: 24px;">Massachusetts Department of Correction</h1>
                            <p style="margin: 10px 0 0 0; font-size: 16px;">Fire and Environmental Safety Suite</p>
                        </div>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                            <h2 style="color: #1e3a8a; margin-bottom: 15px;">Inspection Submitted for Review</h2>
                            
                            <p>A fire safety inspection has been submitted and requires your review:</p>
                            
                            <div style="background: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                                <strong>Inspection Details:</strong><br>
                                Inspection ID: #{{ inspection_id }}<br>
                                Facility: {{ facility_name }}<br>
                                Inspector: {{ inspector_name }}<br>
                                Date: {{ inspection_date }}<br>
                                Type: {{ inspection_type }}
                            </div>
                            
                            {% if citations_count > 0 %}
                            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #ffc107;">
                                <strong>⚠️ Citations Found:</strong> {{ citations_count }} safety violations identified
                            </div>
                            {% endif %}
                            
                            <div style="margin: 20px 0;">
                                <a href="{{ review_url }}" style="background: #f59e0b; color: #1e3a8a; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                    Review Inspection
                                </a>
                            </div>
                            
                            <p style="margin-top: 20px; font-size: 14px; color: #666;">
                                Please review this inspection within 24 hours to ensure compliance with fire safety regulations.
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                "text": """
                Massachusetts Department of Correction
                Fire and Environmental Safety Suite
                
                Inspection Submitted for Review
                
                A fire safety inspection has been submitted and requires your review:
                
                Inspection Details:
                - Inspection ID: #{{ inspection_id }}
                - Facility: {{ facility_name }}
                - Inspector: {{ inspector_name }}
                - Date: {{ inspection_date }}
                - Type: {{ inspection_type }}
                
                {% if citations_count > 0 %}
                ⚠️ Citations Found: {{ citations_count }} safety violations identified
                {% endif %}
                
                Please review this inspection within 24 hours to ensure compliance with fire safety regulations.
                
                Review URL: {{ review_url }}
                """
            },
            
            "inspection_approved": {
                "subject": "Fire Safety Inspection Approved - #{{ inspection_id }}",
                "html": """
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                            <h1 style="margin: 0; font-size: 24px;">Massachusetts Department of Correction</h1>
                            <p style="margin: 10px 0 0 0; font-size: 16px;">Fire and Environmental Safety Suite</p>
                        </div>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                            <h2 style="color: #059669; margin-bottom: 15px;">✅ Inspection Approved</h2>
                            
                            <p>Your fire safety inspection has been approved:</p>
                            
                            <div style="background: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                                <strong>Inspection Details:</strong><br>
                                Inspection ID: #{{ inspection_id }}<br>
                                Facility: {{ facility_name }}<br>
                                Inspector: {{ inspector_name }}<br>
                                Date: {{ inspection_date }}<br>
                                Approved By: {{ reviewer_name }}<br>
                                Approved On: {{ approval_date }}
                            </div>
                            
                            {% if reviewer_comments %}
                            <div style="background: #e0f2fe; padding: 15px; border-radius: 5px; margin: 15px 0;">
                                <strong>Reviewer Comments:</strong><br>
                                {{ reviewer_comments }}
                            </div>
                            {% endif %}
                            
                            <div style="margin: 20px 0;">
                                <a href="{{ pdf_url }}" style="background: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                    Download PDF Report
                                </a>
                            </div>
                            
                            <p style="margin-top: 20px; font-size: 14px; color: #666;">
                                This inspection report has been archived and will be retained for 7 years as required by regulations.
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                "text": """
                Massachusetts Department of Correction
                Fire and Environmental Safety Suite
                
                ✅ Inspection Approved
                
                Your fire safety inspection has been approved:
                
                Inspection Details:
                - Inspection ID: #{{ inspection_id }}
                - Facility: {{ facility_name }}
                - Inspector: {{ inspector_name }}
                - Date: {{ inspection_date }}
                - Approved By: {{ reviewer_name }}
                - Approved On: {{ approval_date }}
                
                {% if reviewer_comments %}
                Reviewer Comments:
                {{ reviewer_comments }}
                {% endif %}
                
                This inspection report has been archived and will be retained for 7 years as required by regulations.
                
                PDF Report URL: {{ pdf_url }}
                """
            },
            
            "inspection_rejected": {
                "subject": "Fire Safety Inspection Requires Revision - #{{ inspection_id }}",
                "html": """
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                            <h1 style="margin: 0; font-size: 24px;">Massachusetts Department of Correction</h1>
                            <p style="margin: 10px 0 0 0; font-size: 16px;">Fire and Environmental Safety Suite</p>
                        </div>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                            <h2 style="color: #dc2626; margin-bottom: 15px;">❌ Inspection Requires Revision</h2>
                            
                            <p>Your fire safety inspection requires revision before approval:</p>
                            
                            <div style="background: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                                <strong>Inspection Details:</strong><br>
                                Inspection ID: #{{ inspection_id }}<br>
                                Facility: {{ facility_name }}<br>
                                Inspector: {{ inspector_name }}<br>
                                Date: {{ inspection_date }}<br>
                                Reviewed By: {{ reviewer_name }}<br>
                                Reviewed On: {{ review_date }}
                            </div>
                            
                            <div style="background: #fee2e2; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #dc2626;">
                                <strong>Required Revisions:</strong><br>
                                {{ reviewer_comments }}
                            </div>
                            
                            <div style="margin: 20px 0;">
                                <a href="{{ edit_url }}" style="background: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                    Edit Inspection
                                </a>
                            </div>
                            
                            <p style="margin-top: 20px; font-size: 14px; color: #666;">
                                Please address the comments above and resubmit the inspection for approval.
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                "text": """
                Massachusetts Department of Correction
                Fire and Environmental Safety Suite
                
                ❌ Inspection Requires Revision
                
                Your fire safety inspection requires revision before approval:
                
                Inspection Details:
                - Inspection ID: #{{ inspection_id }}
                - Facility: {{ facility_name }}
                - Inspector: {{ inspector_name }}
                - Date: {{ inspection_date }}
                - Reviewed By: {{ reviewer_name }}
                - Reviewed On: {{ review_date }}
                
                Required Revisions:
                {{ reviewer_comments }}
                
                Please address the comments above and resubmit the inspection for approval.
                
                Edit Inspection URL: {{ edit_url }}
                """
            },
            
            "monthly_reminder": {
                "subject": "Monthly Fire Safety Inspection Due - {{ facility_name }}",
                "html": """
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                            <h1 style="margin: 0; font-size: 24px;">Massachusetts Department of Correction</h1>
                            <p style="margin: 10px 0 0 0; font-size: 16px;">Fire and Environmental Safety Suite</p>
                        </div>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                            <h2 style="color: #f59e0b; margin-bottom: 15px;">📅 Monthly Inspection Reminder</h2>
                            
                            <p>This is a reminder that your monthly fire safety inspection is due:</p>
                            
                            <div style="background: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                                <strong>Facility Information:</strong><br>
                                Facility: {{ facility_name }}<br>
                                Inspector: {{ inspector_name }}<br>
                                Due Date: {{ due_date }}<br>
                                Last Inspection: {{ last_inspection_date }}
                            </div>
                            
                            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #ffc107;">
                                <strong>Compliance Requirements:</strong><br>
                                • Monthly inspections are required by 105 CMR 451<br>
                                • Inspections must be completed within the first 5 days of each month<br>
                                • All violations must be documented and corrected promptly
                            </div>
                            
                            <div style="margin: 20px 0;">
                                <a href="{{ new_inspection_url }}" style="background: #f59e0b; color: #1e3a8a; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                    Start Monthly Inspection
                                </a>
                            </div>
                            
                            <p style="margin-top: 20px; font-size: 14px; color: #666;">
                                Please complete your monthly inspection by {{ due_date }} to maintain compliance.
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                "text": """
                Massachusetts Department of Correction
                Fire and Environmental Safety Suite
                
                📅 Monthly Inspection Reminder
                
                This is a reminder that your monthly fire safety inspection is due:
                
                Facility Information:
                - Facility: {{ facility_name }}
                - Inspector: {{ inspector_name }}
                - Due Date: {{ due_date }}
                - Last Inspection: {{ last_inspection_date }}
                
                Compliance Requirements:
                • Monthly inspections are required by 105 CMR 451
                • Inspections must be completed within the first 5 days of each month
                • All violations must be documented and corrected promptly
                
                Please complete your monthly inspection by {{ due_date }} to maintain compliance.
                
                Start Inspection URL: {{ new_inspection_url }}
                """
            },
            
            "system_alert": {
                "subject": "Fire Safety System Alert - {{ alert_type }}",
                "html": """
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #dc2626, #ef4444); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                            <h1 style="margin: 0; font-size: 24px;">🚨 SYSTEM ALERT</h1>
                            <p style="margin: 10px 0 0 0; font-size: 16px;">Fire and Environmental Safety Suite</p>
                        </div>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                            <h2 style="color: #dc2626; margin-bottom: 15px;">{{ alert_type }}</h2>
                            
                            <div style="background: #fee2e2; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #dc2626;">
                                <strong>Alert Details:</strong><br>
                                {{ alert_message }}
                            </div>
                            
                            <div style="background: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                                <strong>System Information:</strong><br>
                                Timestamp: {{ timestamp }}<br>
                                Severity: {{ severity }}<br>
                                Component: {{ component }}
                            </div>
                            
                            <p style="margin-top: 20px; font-size: 14px; color: #666;">
                                This is an automated alert from the Fire and Environmental Safety Suite monitoring system.
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                "text": """
                🚨 SYSTEM ALERT
                Fire and Environmental Safety Suite
                
                {{ alert_type }}
                
                Alert Details:
                {{ alert_message }}
                
                System Information:
                - Timestamp: {{ timestamp }}
                - Severity: {{ severity }}
                - Component: {{ component }}
                
                This is an automated alert from the Fire and Environmental Safety Suite monitoring system.
                """
            }
        }
    
    async def send_inspection_submitted_notification(self, 
                                                   inspection_data: Dict[str, Any],
                                                   reviewer_email: str) -> bool:
        """Send notification when inspection is submitted"""
        try:
            template_data = {
                "inspection_id": inspection_data["id"],
                "facility_name": inspection_data.get("facility_name", "Unknown Facility"),
                "inspector_name": inspection_data.get("inspector_name", "Unknown Inspector"),
                "inspection_date": inspection_data.get("inspection_date", ""),
                "inspection_type": inspection_data.get("inspection_type", "Fire Safety Inspection"),
                "citations_count": len(inspection_data.get("citations", [])),
                "review_url": f"https://fire-safety.madoc.gov/inspections/{inspection_data['id']}/review"
            }
            
            return await self._send_templated_email(
                recipient=reviewer_email,
                template_name="inspection_submitted",
                template_data=template_data
            )
        except Exception as e:
            logger.error(f"Error sending inspection submitted notification: {e}")
            return False
    
    async def send_inspection_approved_notification(self,
                                                  inspection_data: Dict[str, Any],
                                                  inspector_email: str) -> bool:
        """Send notification when inspection is approved"""
        try:
            template_data = {
                "inspection_id": inspection_data["id"],
                "facility_name": inspection_data.get("facility_name", "Unknown Facility"),
                "inspector_name": inspection_data.get("inspector_name", "Unknown Inspector"),
                "inspection_date": inspection_data.get("inspection_date", ""),
                "reviewer_name": inspection_data.get("reviewer_name", "Unknown Reviewer"),
                "approval_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                "reviewer_comments": inspection_data.get("reviewer_comments", ""),
                "pdf_url": f"https://fire-safety.madoc.gov/api/inspections/{inspection_data['id']}/pdf"
            }
            
            return await self._send_templated_email(
                recipient=inspector_email,
                template_name="inspection_approved",
                template_data=template_data
            )
        except Exception as e:
            logger.error(f"Error sending inspection approved notification: {e}")
            return False
    
    async def send_inspection_rejected_notification(self,
                                                  inspection_data: Dict[str, Any],
                                                  inspector_email: str) -> bool:
        """Send notification when inspection is rejected"""
        try:
            template_data = {
                "inspection_id": inspection_data["id"],
                "facility_name": inspection_data.get("facility_name", "Unknown Facility"),
                "inspector_name": inspection_data.get("inspector_name", "Unknown Inspector"),
                "inspection_date": inspection_data.get("inspection_date", ""),
                "reviewer_name": inspection_data.get("reviewer_name", "Unknown Reviewer"),
                "review_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                "reviewer_comments": inspection_data.get("reviewer_comments", "Please address the issues found."),
                "edit_url": f"https://fire-safety.madoc.gov/inspections/{inspection_data['id']}/edit"
            }
            
            return await self._send_templated_email(
                recipient=inspector_email,
                template_name="inspection_rejected",
                template_data=template_data
            )
        except Exception as e:
            logger.error(f"Error sending inspection rejected notification: {e}")
            return False
    
    async def send_monthly_reminder(self, 
                                  facility_data: Dict[str, Any],
                                  inspector_email: str) -> bool:
        """Send monthly inspection reminder"""
        try:
            template_data = {
                "facility_name": facility_data.get("name", "Unknown Facility"),
                "inspector_name": facility_data.get("inspector_name", "Unknown Inspector"),
                "due_date": facility_data.get("due_date", ""),
                "last_inspection_date": facility_data.get("last_inspection_date", "None"),
                "new_inspection_url": "https://fire-safety.madoc.gov/inspections/new"
            }
            
            return await self._send_templated_email(
                recipient=inspector_email,
                template_name="monthly_reminder",
                template_data=template_data
            )
        except Exception as e:
            logger.error(f"Error sending monthly reminder: {e}")
            return False
    
    async def send_system_alert(self,
                              alert_data: Dict[str, Any],
                              admin_emails: List[str]) -> bool:
        """Send system alert to administrators"""
        try:
            template_data = {
                "alert_type": alert_data.get("type", "System Alert"),
                "alert_message": alert_data.get("message", ""),
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "severity": alert_data.get("severity", "Medium"),
                "component": alert_data.get("component", "Unknown")
            }
            
            success_count = 0
            for email in admin_emails:
                if await self._send_templated_email(
                    recipient=email,
                    template_name="system_alert",
                    template_data=template_data
                ):
                    success_count += 1
            
            return success_count > 0
        except Exception as e:
            logger.error(f"Error sending system alert: {e}")
            return False
    
    async def _send_templated_email(self,
                                  recipient: str,
                                  template_name: str,
                                  template_data: Dict[str, Any]) -> bool:
        """Send email using template"""
        try:
            template = self.templates.get(template_name)
            if not template:
                logger.error(f"Template not found: {template_name}")
                return False
            
            # Render templates
            subject = Template(template["subject"]).render(**template_data)
            html_body = Template(template["html"]).render(**template_data)
            text_body = Template(template["text"]).render(**template_data)
            
            # Send email
            response = self.ses_client.send_email(
                Source=self.sender_email,
                Destination={
                    'ToAddresses': [recipient]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': text_body,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': html_body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
            logger.info(f"Email sent successfully to {recipient}: {response['MessageId']}")
            return True
            
        except ClientError as e:
            logger.error(f"SES error sending email to {recipient}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {recipient}: {e}")
            return False
    
    async def verify_email_address(self, email: str) -> bool:
        """Verify email address with SES"""
        try:
            self.ses_client.verify_email_identity(EmailAddress=email)
            logger.info(f"Email verification initiated for: {email}")
            return True
        except ClientError as e:
            logger.error(f"Error verifying email {email}: {e}")
            return False
    
    async def get_send_quota(self) -> Dict[str, Any]:
        """Get SES send quota and statistics"""
        try:
            response = self.ses_client.get_send_quota()
            return {
                "max_24_hour": response['Max24HourSend'],
                "max_send_rate": response['MaxSendRate'],
                "sent_last_24_hours": response['SentLast24Hours']
            }
        except ClientError as e:
            logger.error(f"Error getting send quota: {e}")
            return {}
    
    async def get_send_statistics(self) -> List[Dict[str, Any]]:
        """Get SES send statistics"""
        try:
            response = self.ses_client.get_send_statistics()
            return response.get('SendDataPoints', [])
        except ClientError as e:
            logger.error(f"Error getting send statistics: {e}")
            return []