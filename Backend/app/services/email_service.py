"""
Email service for sending transactional emails via Zoho SMTP
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using Zoho SMTP"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME

    def _create_message(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> MIMEMultipart:
        """Create email message"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = to_email
        msg['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

        # Add text version (fallback)
        if text_content:
            part1 = MIMEText(text_content, 'plain')
            msg.attach(part1)

        # Add HTML version
        part2 = MIMEText(html_content, 'html')
        msg.attach(part2)

        return msg

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email via Zoho SMTP

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            msg = self._create_message(to_email, subject, html_content, text_content)

            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_verification_email(self, to_email: str, verification_token: str, user_name: str = "") -> bool:
        """Send email verification link"""
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email - Divine Whispers</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Divine Whispers</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0;">Fortune & Wisdom Platform</p>
            </div>

            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #667eea; margin-top: 0;">Welcome{' ' + user_name if user_name else ''}!</h2>

                <p>Thank you for registering with Divine Whispers. Please verify your email address to activate your account.</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}"
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                              color: white;
                              padding: 15px 40px;
                              text-decoration: none;
                              border-radius: 5px;
                              display: inline-block;
                              font-weight: bold;">
                        Verify Email Address
                    </a>
                </div>

                <p style="color: #666; font-size: 14px;">Or copy and paste this link into your browser:</p>
                <p style="background: white; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 12px;">
                    {verification_url}
                </p>

                <p style="color: #666; font-size: 13px; margin-top: 30px;">
                    This verification link will expire in 24 hours.<br>
                    If you didn't create an account with Divine Whispers, please ignore this email.
                </p>
            </div>

            <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
                <p>&copy; {datetime.utcnow().year} Divine Whispers. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to Divine Whispers!

        Please verify your email address by clicking the link below:
        {verification_url}

        This link will expire in 24 hours.

        If you didn't create an account, please ignore this email.
        """

        return self.send_email(
            to_email=to_email,
            subject="Verify Your Email - Divine Whispers",
            html_content=html_content,
            text_content=text_content
        )

    def send_contact_notification(
        self,
        support_email: str,
        contact_info: dict
    ) -> bool:
        """Send notification about new contact form submission to support team"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>New Contact Form Submission</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #667eea; padding: 20px; color: white;">
                <h2 style="margin: 0;">New Contact Form Submission</h2>
            </div>

            <div style="background: #f9f9f9; padding: 20px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold; width: 150px;">Name:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{contact_info['name']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Email:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{contact_info['email']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Subject:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{contact_info.get('subject', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Category:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{contact_info.get('category', 'general')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">User ID:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{contact_info.get('user_id', 'Anonymous')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Submitted:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{contact_info.get('submitted_at', 'N/A')}</td>
                    </tr>
                </table>

                <div style="margin-top: 20px;">
                    <h3 style="color: #667eea;">Message:</h3>
                    <div style="background: white; padding: 15px; border-left: 4px solid #667eea; border-radius: 5px;">
                        {contact_info['message'].replace('\n', '<br>')}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        New Contact Form Submission

        Name: {contact_info['name']}
        Email: {contact_info['email']}
        Subject: {contact_info.get('subject', 'N/A')}
        Category: {contact_info.get('category', 'general')}
        User ID: {contact_info.get('user_id', 'Anonymous')}
        Submitted: {contact_info.get('submitted_at', 'N/A')}

        Message:
        {contact_info['message']}
        """

        return self.send_email(
            to_email=support_email,
            subject=f"Contact Form: {contact_info.get('subject', 'New Inquiry')}",
            html_content=html_content,
            text_content=text_content
        )

    def send_contact_acknowledgment(
        self,
        to_email: str,
        contact_info: dict
    ) -> bool:
        """Send acknowledgment email to user who submitted contact form"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>We Received Your Message</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Divine Whispers</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0;">Support Team</p>
            </div>

            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #667eea; margin-top: 0;">Thank You for Contacting Us!</h2>

                <p>Dear {contact_info['name']},</p>

                <p>We have received your message regarding: <strong>{contact_info.get('subject', 'your inquiry')}</strong></p>

                <div style="background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0; border-radius: 5px;">
                    <p style="margin: 0; color: #666; font-size: 14px;"><strong>Your message:</strong></p>
                    <p style="margin: 10px 0 0 0;">{contact_info['message'][:200]}{'...' if len(contact_info['message']) > 200 else ''}</p>
                </div>

                <p>Our support team will review your inquiry and respond within <strong>24-48 hours</strong>.</p>

                <p style="color: #666; font-size: 13px; margin-top: 30px;">
                    If you have additional questions, please feel free to reply to this email or submit another contact form.
                </p>
            </div>

            <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
                <p>&copy; {datetime.utcnow().year} Divine Whispers. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Thank You for Contacting Divine Whispers!

        Dear {contact_info['name']},

        We have received your message regarding: {contact_info.get('subject', 'your inquiry')}

        Your message:
        {contact_info['message'][:200]}{'...' if len(contact_info['message']) > 200 else ''}

        Our support team will review your inquiry and respond within 24-48 hours.

        If you have additional questions, please feel free to reply to this email.
        """

        return self.send_email(
            to_email=to_email,
            subject="We Received Your Message - Divine Whispers Support",
            html_content=html_content,
            text_content=text_content
        )


# Global email service instance
email_service = EmailService()
