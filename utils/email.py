"""
Email utility module for Let Me Mug You.
Currently stubbed - will send emails when SMTP is configured.
"""
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


def send_email(to_email, subject, html_body, text_body=None):
    """
    Send an email using SMTP.

    Returns True if sent successfully, False otherwise.
    Currently stubbed if MAIL_USERNAME is not configured.
    """
    mail_username = os.getenv('MAIL_USERNAME')
    mail_password = os.getenv('MAIL_PASSWORD')

    if not mail_username or not mail_password:
        # Stub mode - just log the email
        current_app.logger.info(f"[EMAIL STUB] Would send email to: {to_email}")
        current_app.logger.info(f"[EMAIL STUB] Subject: {subject}")
        current_app.logger.info(f"[EMAIL STUB] Body preview: {html_body[:200]}...")
        return True

    try:
        mail_server = os.getenv('MAIL_SERVER', 'box2335.bluehost.com')
        mail_port = int(os.getenv('MAIL_PORT', '465'))
        use_ssl = os.getenv('MAIL_USE_SSL', 'true').lower() == 'true'

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = mail_username
        msg['To'] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        context = ssl.create_default_context()

        if use_ssl:
            with smtplib.SMTP_SSL(mail_server, mail_port, context=context) as server:
                server.login(mail_username, mail_password)
                server.sendmail(mail_username, to_email, msg.as_string())
        else:
            with smtplib.SMTP(mail_server, mail_port) as server:
                server.starttls(context=context)
                server.login(mail_username, mail_password)
                server.sendmail(mail_username, to_email, msg.as_string())

        current_app.logger.info(f"Email sent to {to_email}: {subject}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def send_order_confirmation(order):
    """Send order confirmation email to customer."""
    subject = f"Order Confirmation - {order.order_number}"

    items_html = ""
    for item in order.items:
        items_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{item.product_name}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{item.quantity}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">${item.line_total:.2f}</td>
        </tr>
        """

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #2c3e50; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">&#9749; Let Me Mug You</h1>
        </div>

        <div style="padding: 30px;">
            <h2>Thank you for your order!</h2>
            <p>Hi {order.customer_name},</p>
            <p>We've received your order and will begin processing it shortly.</p>

            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <strong>Order Number:</strong> {order.order_number}
            </div>

            <h3>Order Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f5f5f5;">
                        <th style="padding: 10px; text-align: left;">Item</th>
                        <th style="padding: 10px; text-align: left;">Qty</th>
                        <th style="padding: 10px; text-align: left;">Price</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="2" style="padding: 10px; text-align: right;"><strong>Subtotal:</strong></td>
                        <td style="padding: 10px;">${order.subtotal:.2f}</td>
                    </tr>
                    <tr>
                        <td colspan="2" style="padding: 10px; text-align: right;"><strong>Tax:</strong></td>
                        <td style="padding: 10px;">${order.tax:.2f}</td>
                    </tr>
                    <tr style="font-size: 1.2em;">
                        <td colspan="2" style="padding: 10px; text-align: right;"><strong>Total:</strong></td>
                        <td style="padding: 10px;"><strong>${order.total:.2f}</strong></td>
                    </tr>
                </tfoot>
            </table>

            <h3>Shipping Address</h3>
            <p>
                {order.customer_name}<br>
                {order.address_line1}<br>
                {(order.address_line2 + '<br>') if order.address_line2 else ''}
                {order.city}, {order.state} {order.zip_code}
            </p>

            <p style="margin-top: 30px;">
                If you have any questions, please reply to this email.
            </p>

            <p>Thank you for choosing Let Me Mug You!</p>
        </div>

        <div style="background: #f5f5f5; padding: 20px; text-align: center; color: #666; font-size: 12px;">
            <p>&copy; 2024 Let Me Mug You. All rights reserved.</p>
        </div>
    </body>
    </html>
    """

    return send_email(order.email, subject, html_body)


def send_admin_notification(order):
    """Send new order notification to admin."""
    from models import AdminSettings

    admin_email = AdminSettings.get('admin_email')
    if not admin_email:
        current_app.logger.info("No admin email configured - skipping admin notification")
        return True

    subject = f"New Order: {order.order_number}"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>New Order Received</h2>
        <p><strong>Order Number:</strong> {order.order_number}</p>
        <p><strong>Customer:</strong> {order.customer_name} ({order.email})</p>
        <p><strong>Total:</strong> ${order.total:.2f}</p>
        <p><strong>Items:</strong> {len(order.items)}</p>
        <p><a href="https://letmemugyou.com/admin/orders/{order.id}">View Order in Admin</a></p>
    </body>
    </html>
    """

    return send_email(admin_email, subject, html_body)
