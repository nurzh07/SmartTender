import os
import resend
from app.config import get_settings

settings = get_settings()

# Initialize Resend with API key from environment
resend.api_key = os.getenv("RESEND_API_KEY")


def send_welcome_email(to_email: str, username: str) -> dict:
    """Send welcome email using Resend"""
    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": [to_email],
            "subject": "Тіркелу сәтті өтті!",
            "html": f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f4f4f4; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #333;">Сәлем, {username}!</h2>
                        <p style="color: #666;">Сіз SmartTender платформасына сәтті тіркелдіңіз.</p>
                        <p style="color: #666;">
                            Біздің платформада тендерлерге қатысу, ұсыныстар жіберу және 
                            басқа да мүмкіндіктерді пайдалана аласыз.
                        </p>
                        <p style="color: #666;">
                            Платформаға кіру үшін <a href="http://localhost:3000/login" style="color: #007bff;">осы сілтемеге</a> өтіңіз.
                        </p>
                        <p style="color: #666;">Сұрақтарыңыз болса, бізге хабарласыңыз.</p>
                        <p style="color: #666; margin-top: 20px;">SmartTender командасы</p>
                    </div>
                </body>
                </html>
            """
        }
        
        result = resend.Emails.send(params)
        return {"status": "sent", "email": to_email, "result": result}
    except Exception as e:
        return {"status": "failed", "email": to_email, "error": str(e)}


def send_password_reset_email(to_email: str, reset_link: str) -> dict:
    """Send password reset email using Resend"""
    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": [to_email],
            "subject": "SmartTender — құпия сөзді қалпына келтіру",
            "html": f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f4f4f4; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #333;">Сәлем!</h2>
                        <p style="color: #666;">
                            SmartTender-ге құпия сөзді қалпына келтіру сұрауы қабылданды.
                        </p>
                        <p style="color: #666;">
                            Келесі сілтеме арқылы жаңа құпия сөз қойыңыз (1 сағат бойы жарамды):
                        </p>
                        <p style="margin: 20px 0;">
                            <a href="{reset_link}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">
                                Құпия сөзді қалпына келтіру
                            </a>
                        </p>
                        <p style="color: #666;">
                            Егер сіз бұл сұрауды жібермеген болсаңыз, бұл хатты елемеуге болады.
                        </p>
                        <p style="color: #666; margin-top: 20px;">SmartTender командасы</p>
                    </div>
                </body>
                </html>
            """
        }
        
        result = resend.Emails.send(params)
        return {"status": "sent", "email": to_email, "result": result}
    except Exception as e:
        return {"status": "failed", "email": to_email, "error": str(e)}


def send_verification_email(to_email: str, verify_link: str) -> dict:
    """Send email verification email using Resend"""
    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": [to_email],
            "subject": "SmartTender — email растау",
            "html": f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f4f4f4; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #333;">Сәлем!</h2>
                        <p style="color: #666;">
                            SmartTender-ге тіркелгеніңіз үшін рахмет!
                        </p>
                        <p style="color: #666;">
                            Email-ді растау үшін сілтемеге өтіңіз (24 сағат бойы жарамды):
                        </p>
                        <p style="margin: 20px 0;">
                            <a href="{verify_link}" style="display: inline-block; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">
                                Email-ді растау
                            </a>
                        </p>
                        <p style="color: #666; margin-top: 20px;">SmartTender командасы</p>
                    </div>
                </body>
                </html>
            """
        }
        
        result = resend.Emails.send(params)
        return {"status": "sent", "email": to_email, "result": result}
    except Exception as e:
        return {"status": "failed", "email": to_email, "error": str(e)}


def send_tender_published_email(to_email: str, tender_title: str, tender_id: int) -> dict:
    """Send email when tender is published using Resend"""
    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": [to_email],
            "subject": f"SmartTender — Жаңа тендер: {tender_title}",
            "html": f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f4f4f4; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #333;">Жаңа тендер жарияланды!</h2>
                        <p style="color: #666;">
                            <strong>Тендер:</strong> {tender_title}
                        </p>
                        <p style="color: #666;">
                            <strong>ID:</strong> {tender_id}
                        </p>
                        <p style="color: #666;">
                            Ұсыныс жіберу үшін SmartTender платформасына кіріңіз.
                        </p>
                        <p style="color: #666; margin-top: 20px;">SmartTender командасы</p>
                    </div>
                </body>
                </html>
            """
        }
        
        result = resend.Emails.send(params)
        return {"status": "sent", "email": to_email, "result": result}
    except Exception as e:
        return {"status": "failed", "email": to_email, "error": str(e)}


def send_new_proposal_email(to_email: str, tender_title: str, supplier_name: str) -> dict:
    """Send email when new proposal is received using Resend"""
    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": [to_email],
            "subject": f"SmartTender — Жаңа ұсыныс: {tender_title}",
            "html": f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f4f4f4; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #333;">Жаңа ұсыныс келді!</h2>
                        <p style="color: #666;">
                            <strong>Тендер:</strong> {tender_title}
                        </p>
                        <p style="color: #666;">
                            <strong>Жеткізуші:</strong> {supplier_name}
                        </p>
                        <p style="color: #666;">
                            Ұсыныстарды қарау үшін SmartTender платформасына кіріңіз.
                        </p>
                        <p style="color: #666; margin-top: 20px;">SmartTender командасы</p>
                    </div>
                </body>
                </html>
            """
        }
        
        result = resend.Emails.send(params)
        return {"status": "sent", "email": to_email, "result": result}
    except Exception as e:
        return {"status": "failed", "email": to_email, "error": str(e)}


def send_deadline_reminder_email(to_email: str, tender_title: str, deadline: str, days_left: int) -> dict:
    """Send deadline reminder email using Resend"""
    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": [to_email],
            "subject": f"SmartTender — Дедлайн ескерту ({days_left} күн қалды): {tender_title}",
            "html": f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #fff3cd; padding: 20px; border-radius: 5px; border: 1px solid #ffeeba;">
                        <h2 style="color: #856404;">Ескерту!</h2>
                        <p style="color: #666;">
                            Тендер дедлайнына {days_left} күн қалды:
                        </p>
                        <p style="color: #666;">
                            <strong>Тендер:</strong> {tender_title}
                        </p>
                        <p style="color: #666;">
                            <strong>Дедлайн:</strong> {deadline}
                        </p>
                        <p style="color: #666;">
                            Уақытты өткізіп алмаңыз!
                        </p>
                        <p style="color: #666; margin-top: 20px;">SmartTender командасы</p>
                    </div>
                </body>
                </html>
            """
        }
        
        result = resend.Emails.send(params)
        return {"status": "sent", "email": to_email, "result": result}
    except Exception as e:
        return {"status": "failed", "email": to_email, "error": str(e)}


def send_winner_selected_email(to_email: str, tender_title: str, is_winner: bool) -> dict:
    """Send email when winner is selected using Resend"""
    try:
        subject = f"SmartTender — Құттықтаймыз! Сіз жеңдіңіз: {tender_title}" if is_winner \
            else f"SmartTender — Қайғырмыз, сіз жеңілдіңіз: {tender_title}"
        
        bg_color = '#d4edda' if is_winner else '#f8d7da'
        border_color = '#c3e6cb' if is_winner else '#f5c6cb'
        text_color = '#155724' if is_winner else '#721c24'
        title_text = 'Құттықтаймыз!' if is_winner else 'Қайғырмыз'
        message_text = 'Сіз жеңдіңіз! Келесі қадамдар туралы ақпаратты кейін аласыз.' if is_winner \
            else 'Бұл тапсырманы жеңе алмадыңыз. Басқа мүмкіндіктерді көріңіз.'
        
        html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: {bg_color}; padding: 20px; border-radius: 5px; border: 1px solid {border_color};">
                        <h2 style="color: {text_color};">
                            {title_text}
                        </h2>
                        <p style="color: #666;">
                            Тендер бойынша нәтиже анықталды:
                        </p>
                        <p style="color: #666;">
                            <strong>Тендер:</strong> {tender_title}
                        </p>
                        <p style="color: #666;">
                            {message_text}
                        </p>
                        <p style="color: #666; margin-top: 20px;">SmartTender командасы</p>
                    </div>
                </body>
                </html>
            """
        
        params = {
            "from": "onboarding@resend.dev",
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        result = resend.Emails.send(params)
        return {"status": "sent", "email": to_email, "result": result}
    except Exception as e:
        return {"status": "failed", "email": to_email, "error": str(e)}


def send_tender_closed_email(to_email: str, tender_title: str, pdf_url: str) -> dict:
    """Send email when tender is closed using Resend"""
    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": [to_email],
            "subject": f"SmartTender — Тендер жабылды: {tender_title}",
            "html": f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #d1ecf1; padding: 20px; border-radius: 5px; border: 1px solid #bee5eb;">
                        <h2 style="color: #0c5460;">Тендер жабылды</h2>
                        <p style="color: #666;">
                            Тендер сәтті жабылды:
                        </p>
                        <p style="color: #666;">
                            <strong>Тендер:</strong> {tender_title}
                        </p>
                        <p style="color: #666;">
                            Есепті жүктеу: <a href="{pdf_url}" style="color: #007bff;">{pdf_url}</a>
                        </p>
                        <p style="color: #666;">
                            Рахмет SmartTender-ді қолданғаныңыз үшін!
                        </p>
                        <p style="color: #666; margin-top: 20px;">SmartTender командасы</p>
                    </div>
                </body>
                </html>
            """
        }
        
        result = resend.Emails.send(params)
        return {"status": "sent", "email": to_email, "result": result}
    except Exception as e:
        return {"status": "failed", "email": to_email, "error": str(e)}
