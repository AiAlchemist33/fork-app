"""Email templates — HTML + plain-text pairs.

Three transactional templates:
  - confirm — "Подтверди email"  (sent after register / email change)
  - reset   — "Сброс пароля"        (sent on password-reset/request)
  - welcome — "Добро пожаловать"    (sent after email is verified)

Each public function returns a dict { subject, html, text } that the
calling endpoint passes straight to send_email().

Phase 8 redesign — three canonical templates rebuilt to match the
brutalist cream/dark mockups in `Email Mockups/`. New design system:
  - Cream page bg #ebe5d8, light card #f6f1e6, dark accent #0e0d0a
  - Ochre kicker dot #b54a1f for editorial accent
  - Fraunces serif headlines (300-weight, italic emphasis), Inter body,
    JetBrains Mono labels — loaded via Google Fonts in <head> with
    system fallbacks for clients that strip web fonts
  - Personalization: every template takes a `user_name` parameter that
    falls back through display_name → username → "Гость"
  - Dynamic dates: topbar month/year is rendered fresh per send, never
    hardcoded
  - Recipient + sender pulled from runtime params, never inlined

Design constraints baked in:
  - Inline CSS only — email clients (Outlook, Yandex, Mail.ru) strip
    <style> tags or apply them inconsistently. The template uses an
    inline <style> block which Gmail/Yandex DO honor; older Outlook
    falls back to single-column block layout, which still reads
    correctly (just without the flex-aligned topbar/addressed rows).
  - Single column, 580px max — mobile-first; desktop centres it
  - One primary CTA per email — focused action, no decision fatigue
  - Plain-text alternative for every HTML — required for inbox
    deliverability (anti-spam scoring penalises HTML-only mail)
  - No tracking pixels, no remote images — the only remote asset is
    the Google Fonts stylesheet (graceful fallback if blocked)
  - Russian copy throughout, polite "вы" address, soft warm tone
"""

from datetime import datetime, timezone, timedelta

from server.config import (
    OPERATOR_NAME, OPERATOR_CITY, UNISENDER_FROM_EMAIL, UNISENDER_FROM_NAME,
)


# Telegram support — kept as a constant so a future channel rename
# is one edit. Inline rather than a config var because it's a brand
# fact, not an env-tunable.
_TELEGRAM_SUPPORT_URL    = "https://t.me/ForkWorkBro"
_TELEGRAM_SUPPORT_HANDLE = "@ForkWorkBro"


# Russian month names in nominative — used by the dated topbar
# "Май · 2026" pattern. The mockups hardcoded "Май · 2026"; this
# helper renders the actual current month so recipients always see
# the correct date regardless of when the template was authored.
_RU_MONTHS = (
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
)


# Moscow time — operator data localisation requires Russian-locale
# dates. UTC+3, no DST.
_MSK_TZ = timezone(timedelta(hours=3))


def _current_month_year_ru() -> str:
    """Return e.g. "Май · 2026" for the topbar dated slot. Computed at
    send time, in Moscow time, so the recipient sees the month they
    actually received the mail — not whenever the template literal
    was authored."""
    now = datetime.now(_MSK_TZ)
    return f"{_RU_MONTHS[now.month - 1]} · {now.year}"


def _resolve_user_name(user: dict | None) -> str:
    """Returns the friendliest available name for greeting. Fallback
    chain:
      1. display_name (the user's chosen friendly name in profile)
      2. username (login identifier — always exists on a real account)
      3. "Гость" (defensive last resort; shouldn't trigger because users
         with emails always have usernames, but covers None inputs)
    """
    if not user:
        return "Гость"
    for key in ("display_name", "username"):
        name = (user.get(key) or "").strip()
        if name:
            return name
    return "Гость"


def _shared_head(title: str) -> str:
    """The <head> block reused across all three templates. Includes
    Google Fonts link and the meta tags every modern email client
    respects."""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
"""


def _shared_styles() -> str:
    """The complete inline <style> block that powers the brutalist
    cream/dark layout. Identical across all three templates so a
    cosmetic change ships once."""
    return """<style>
  body, table, td, a { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }
  table, td { mso-table-lspace: 0pt; mso-table-rspace: 0pt; }
  img { border: 0; outline: none; display: block; }
  body { margin: 0; padding: 0; width: 100% !important; }
  a { color: inherit; text-decoration: none; }

  body {
    background: #ebe5d8;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #0e0d0a;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  .page { width: 100%; background: #ebe5d8; padding: 32px 16px 48px 16px; }
  .container { max-width: 580px; margin: 0 auto; }

  .topbar {
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 4px 28px 4px;
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase; color: #6f6a5d;
  }

  .topbar .logo-mark { width: 88px; height: auto; color: #0e0d0a; display: block; }
  .topbar-right { text-align: right; line-height: 1.6; }

  .card { background: #f6f1e6; border: 1px solid #0e0d0a; position: relative; }

  .hero { padding: 56px 44px 36px 44px; border-bottom: 1px solid #0e0d0a; }

  .kicker {
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase;
    color: #0e0d0a; margin: 0 0 32px 0;
    display: flex; align-items: center; gap: 10px;
  }

  .kicker-dot { width: 6px; height: 6px; background: #b54a1f; display: inline-block; }

  h1 {
    font-family: 'Fraunces', 'Cormorant Garamond', Georgia, serif;
    font-weight: 300; font-size: 56px; line-height: 0.96; letter-spacing: -0.035em;
    color: #0e0d0a; margin: 0;
  }

  h1 .ital { font-style: italic; font-weight: 300; }

  .greeting {
    margin: 0 0 14px 0;
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase;
    color: #6f6a5d;
  }

  .lede { margin: 28px 0 0 0; font-size: 15px; line-height: 1.6; color: #2a2823; max-width: 460px; font-weight: 400; }

  .addressed {
    padding: 24px 44px; border-bottom: 1px solid #0e0d0a;
    display: flex; justify-content: space-between; align-items: baseline; gap: 16px;
  }
  .addressed-label {
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase;
    color: #6f6a5d; flex-shrink: 0;
  }
  .addressed-value {
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 13px; color: #0e0d0a; font-weight: 500; text-align: right; word-break: break-all;
  }

  .action { padding: 44px; border-bottom: 1px solid #0e0d0a; }
  .cta {
    display: block; width: 100%; box-sizing: border-box;
    background: #0e0d0a; color: #f6f1e6 !important;
    text-decoration: none; text-align: center;
    font-family: 'Inter', sans-serif; font-weight: 500;
    font-size: 15px; letter-spacing: 0.04em; text-transform: uppercase;
    padding: 22px 28px; line-height: 1; border: 0;
    transition: background 0.18s ease;
  }
  .cta:hover { background: #b54a1f; }

  .action-meta {
    margin: 18px 0 0 0;
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 11px; letter-spacing: 0.06em; color: #6f6a5d;
    display: flex; justify-content: space-between; text-transform: uppercase;
  }

  .fallback { padding: 28px 44px; border-bottom: 1px solid #0e0d0a; }
  .fallback-label {
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase;
    color: #6f6a5d; margin: 0 0 10px 0;
  }
  .fallback-url {
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 12.5px; color: #0e0d0a; word-break: break-all; line-height: 1.55;
  }

  .security, .tip { padding: 28px 44px; background: #0e0d0a; color: #d6d1c2; }
  .security-label, .tip-label {
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase;
    color: #8a8678; margin: 0 0 10px 0;
  }
  .security-text, .tip-text { font-size: 14px; line-height: 1.55; color: #ebe5d8; margin: 0; font-weight: 400; }
  .security-text strong, .tip-text strong { color: #ffffff; font-weight: 500; }

  .steps { padding: 8px 44px 28px 44px; border-bottom: 1px solid #0e0d0a; }
  .steps-label {
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase;
    color: #6f6a5d; margin: 24px 0 24px 0;
  }
  .step {
    display: flex; gap: 20px; padding: 20px 0;
    border-top: 1px solid rgba(14, 13, 10, 0.12);
  }
  .step:first-of-type { border-top: 0; padding-top: 4px; }
  .step-num {
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 11px; letter-spacing: 0.06em;
    color: #6f6a5d; flex-shrink: 0; width: 28px; padding-top: 2px;
  }
  .step-body { flex: 1; }
  .step-title {
    font-family: 'Inter', sans-serif; font-weight: 500;
    font-size: 15px; color: #0e0d0a; margin: 0 0 4px 0;
    letter-spacing: -0.005em;
  }
  .step-text { font-size: 13.5px; line-height: 1.55; color: #4d4940; margin: 0; }

  .footer { padding: 28px 4px 0 4px; }
  .footer-grid {
    display: flex; justify-content: space-between; gap: 24px;
    padding-bottom: 20px; border-bottom: 1px solid #0e0d0a;
  }
  .footer-col { flex: 1; }
  .footer-label {
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 9.5px; letter-spacing: 0.18em; text-transform: uppercase;
    color: #6f6a5d; margin: 0 0 6px 0;
  }
  .footer-value { font-size: 12.5px; color: #0e0d0a; line-height: 1.55; margin: 0; }
  .footer-value a { color: #0e0d0a; border-bottom: 1px solid #0e0d0a; padding-bottom: 1px; }

  .footer-fine {
    margin-top: 18px;
    font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
    font-size: 10px; letter-spacing: 0.06em; line-height: 1.7;
    color: #6f6a5d; text-transform: uppercase;
  }
  .footer-fine a { color: #0e0d0a; border-bottom: 1px solid #0e0d0a; }

  @media (max-width: 540px) {
    .page { padding: 20px 12px 36px 12px; }
    .hero { padding: 40px 24px 28px 24px; }
    .addressed, .action, .fallback, .security, .tip, .steps { padding-left: 24px; padding-right: 24px; }
    h1 { font-size: 40px; }
    .addressed { flex-direction: column; align-items: flex-start; gap: 6px; }
    .addressed-value { text-align: left; }
    .footer-grid { flex-direction: column; gap: 16px; }
    .action-meta { flex-direction: column; gap: 6px; }
    .step-num { width: 22px; }
  }
</style>"""


def _logo_svg() -> str:
    """The fork wordmark — same monoline geometric SVG used in the app
    header. Color via currentColor so the topbar's `color: #0e0d0a`
    inherits down to the strokes."""
    return """<svg class="logo-mark" viewBox="0 0 78 32" fill="none" stroke="currentColor" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="fork">
          <path d="M 17 5 Q 12 5 12 8.5 L 12 28"/>
          <path d="M 5 14 L 18 14"/>
          <circle cx="30" cy="19" r="9"/>
          <path d="M 44 28 L 44 12 Q 44 9.5 47 9.5 Q 52 9.5 54 13"/>
          <path d="M 60 5 L 60 28"/>
          <path d="M 60 20 L 72 12"/>
          <path d="M 60 20 L 72 28"/>
        </svg>"""


def _format_account_id(user: dict | None) -> str:
    """Mirror the in-app account-id format: `№ 000061` (6-digit
    zero-padded user.id with the `№` letterhead prefix). Matches the
    `#000061` shown on the user's Account Settings page so the topbar
    is recognisable as "your account" not a fake send sequence."""
    if not user:
        return "№ ——"
    uid = user.get("id")
    if uid is None:
        return "№ ——"
    return f"№ {str(uid).zfill(6)}"


def _topbar(user: dict | None, issue_label: str) -> str:
    """The dated brutalist letterhead. The left "№ 000061" slot is the
    recipient's actual account number (matching the `#000061` shown
    inside the app's Account Settings page). `issue_label` is the
    email-type tag — "Подтверждение" / "Сброс пароля" / "Добро
    пожаловать". Month/year is dynamic via _current_month_year_ru()."""
    return f"""<div class="topbar">
        {_logo_svg()}
        <div class="topbar-right">
          {_format_account_id(user)} · {issue_label}<br>
          {_current_month_year_ru()}
        </div>
      </div>"""


def _footer(*, recipient: str, sender_email: str = "", footer_note: str = "") -> str:
    """Three-column metadata footer + fine print. `sender_email`
    defaults to the configured Unisender FROM address; pass a
    different one for the welcome email which is conceptually from
    `hello@` not `noreply@`."""
    sender = sender_email or UNISENDER_FROM_EMAIL
    return f"""<div class="footer">
        <div class="footer-grid">
          <div class="footer-col">
            <p class="footer-label">Поддержка</p>
            <p class="footer-value"><a href="{_TELEGRAM_SUPPORT_URL}">{_TELEGRAM_SUPPORT_HANDLE}</a></p>
          </div>
          <div class="footer-col">
            <p class="footer-label">Отправитель</p>
            <p class="footer-value">{sender}</p>
          </div>
          <div class="footer-col">
            <p class="footer-label">Получатель</p>
            <p class="footer-value">{recipient}</p>
          </div>
        </div>
        <p class="footer-fine">
          {footer_note or "Служебное сообщение. Отвечать не нужно."}<br>
          Оператор данных — {OPERATOR_NAME}, {OPERATOR_CITY}.
        </p>
      </div>"""


# ── Plain-text wrapper ────────────────────────────────────────────────────
# Plain text is what most spam filters score; getting it right is more
# important than the HTML being beautiful. Keep lines under ~72 chars,
# spell out URLs in full (no link text + URL split — many text clients
# won't auto-detect that pattern reliably).

def _render_text(
    *,
    title:        str,
    greeting:     str,
    body:         str,
    button_text:  str | None = None,
    button_url:   str | None = None,
    closing:      str = "",
) -> str:
    cta_block = ""
    if button_text and button_url:
        cta_block = f"\n{button_text}:\n{button_url}\n"
    closing_block = f"\n{closing}\n" if closing else "\n"

    return (
        f"FORK\n\n"
        f"{greeting}\n\n"
        f"{title}\n"
        f"{'=' * min(len(title), 60)}\n\n"
        f"{body}\n"
        f"{cta_block}"
        f"{closing_block}"
        f"---\n"
        f"Поддержка: {_TELEGRAM_SUPPORT_URL}\n"
        f"Оператор данных: {OPERATOR_NAME}, {OPERATOR_CITY}.\n"
        f"Это служебное письмо, отвечать на него не нужно.\n"
    )


# ── Public templates ──────────────────────────────────────────────────────


def confirm_email_template(
    verify_url: str,
    *,
    user: dict | None = None,
    recipient: str,
) -> dict:
    """Email-confirmation message. Sent after register or email change.
    Link is consumed by GET /api/auth/email/verify?token=… which sets
    email_verified=1, fires the welcome email, and redirects to
    /?verified=1.

    Phase 8 redesign — brutalist cream/dark per Email Mockups/fork-email-v3.
    Personalized greeting via user.display_name → username → "Гость".
    """
    name      = _resolve_user_name(user)
    subject   = "Подтвердите email — FORK"
    title     = "Подтверждение email"

    html = (
        f"{_shared_head(title)}"
        f"{_shared_styles()}"
        "</head>\n<body>\n"
        '  <div class="page">\n'
        '    <div class="container">\n'
        f"      {_topbar(user, 'Подтверждение')}\n"
        '      <div class="card">\n'
        '        <div class="hero">\n'
        '          <p class="kicker"><span class="kicker-dot"></span> Один шаг до старта</p>\n'
        f'          <p class="greeting">Привет, {name}</p>\n'
        '          <h1>Подтвердите<br>ваш <span class="ital">email</span>.</h1>\n'
        '          <p class="lede">Спасибо, что выбрали FORK. Чтобы завершить регистрацию и защитить аккаунт, подтвердите, что этот адрес действительно принадлежит вам.</p>\n'
        '        </div>\n'
        '        <div class="addressed">\n'
        '          <span class="addressed-label">Адрес</span>\n'
        f'          <span class="addressed-value">{recipient}</span>\n'
        '        </div>\n'
        '        <div class="action">\n'
        f'          <a href="{verify_url}" class="cta">Подтвердить email →</a>\n'
        '          <div class="action-meta">\n'
        '            <span>Срок действия</span>\n'
        '            <span>24 часа</span>\n'
        '          </div>\n'
        '        </div>\n'
        '        <div class="fallback">\n'
        '          <p class="fallback-label">Или вставьте ссылку в браузер</p>\n'
        f'          <div class="fallback-url">{verify_url}</div>\n'
        '        </div>\n'
        '        <div class="security">\n'
        '          <p class="security-label">Безопасность</p>\n'
        '          <p class="security-text"><strong>Если вы не регистрировались в FORK</strong> — просто проигнорируйте это письмо. Без подтверждения аккаунт не активируется, и никто не получит к нему доступ.</p>\n'
        '        </div>\n'
        '      </div>\n'
        f"      {_footer(recipient=recipient)}\n"
        '    </div>\n'
        '  </div>\n'
        '</body>\n</html>'
    )

    text = _render_text(
        title=title,
        greeting=f"Привет, {name}!",
        body=(
            "Спасибо, что выбрали FORK. Чтобы завершить регистрацию и "
            "защитить аккаунт, подтвердите, что этот email действительно "
            "ваш."
        ),
        button_text="Подтвердить email",
        button_url=verify_url,
        closing=(
            "Если вы не регистрировались — просто проигнорируйте это "
            "письмо. Ссылка действует 24 часа."
        ),
    )

    return {"subject": subject, "html": html, "text": text}


def reset_email_template(
    reset_url: str,
    *,
    user: dict | None = None,
    recipient: str,
) -> dict:
    """Password-reset message. Sent in response to a public POST
    /api/auth/password-reset/request. Link points at the /reset page
    where the user enters a new password.

    Phase 8 redesign — brutalist cream/dark per Email Mockups/fork-02.
    """
    name      = _resolve_user_name(user)
    subject   = "Сброс пароля — FORK"
    title     = "Сброс пароля"

    html = (
        f"{_shared_head(title)}"
        f"{_shared_styles()}"
        "</head>\n<body>\n"
        '  <div class="page">\n'
        '    <div class="container">\n'
        f"      {_topbar(user, 'Сброс пароля')}\n"
        '      <div class="card">\n'
        '        <div class="hero">\n'
        '          <p class="kicker"><span class="kicker-dot"></span> Запрос получен</p>\n'
        f'          <p class="greeting">Привет, {name}</p>\n'
        '          <h1>Сбросьте<br>ваш <span class="ital">пароль</span>.</h1>\n'
        '          <p class="lede">Мы получили запрос на сброс пароля для вашего аккаунта. Нажмите на кнопку ниже, чтобы задать новый пароль.</p>\n'
        '        </div>\n'
        '        <div class="addressed">\n'
        '          <span class="addressed-label">Аккаунт</span>\n'
        f'          <span class="addressed-value">{recipient}</span>\n'
        '        </div>\n'
        '        <div class="action">\n'
        f'          <a href="{reset_url}" class="cta">Задать новый пароль →</a>\n'
        '          <div class="action-meta">\n'
        '            <span>Срок действия</span>\n'
        '            <span>1 час</span>\n'
        '          </div>\n'
        '        </div>\n'
        '        <div class="fallback">\n'
        '          <p class="fallback-label">Или вставьте ссылку в браузер</p>\n'
        f'          <div class="fallback-url">{reset_url}</div>\n'
        '        </div>\n'
        '        <div class="security">\n'
        '          <p class="security-label">Безопасность</p>\n'
        '          <p class="security-text"><strong>Если вы не запрашивали сброс пароля</strong> — просто проигнорируйте это письмо. Ваш пароль останется прежним, и никаких изменений в аккаунте не произойдёт.</p>\n'
        '        </div>\n'
        '      </div>\n'
        f"      {_footer(recipient=recipient)}\n"
        '    </div>\n'
        '  </div>\n'
        '</body>\n</html>'
    )

    text = _render_text(
        title=title,
        greeting=f"Привет, {name}!",
        body=(
            "Кто-то (надеемся, вы) попросил сбросить пароль аккаунта FORK. "
            "Чтобы создать новый пароль, откройте ссылку ниже."
        ),
        button_text="Задать новый пароль",
        button_url=reset_url,
        closing=(
            "Если это не вы — просто проигнорируйте письмо, текущий "
            "пароль останется прежним. Ссылка действует 1 час."
        ),
    )

    return {"subject": subject, "html": html, "text": text}


def welcome_email_template(
    app_url: str,
    *,
    user: dict | None = None,
    recipient: str,
) -> dict:
    """Welcome message — sent automatically after email_verified flips
    to 1. Three numbered onboarding steps + a porting tip. Single CTA
    back to the scanner.

    Phase 8 redesign — brutalist cream/dark per Email Mockups/fork-03.
    """
    name      = _resolve_user_name(user)
    subject   = "Добро пожаловать в FORK"
    title     = "Добро пожаловать в FORK"

    html = (
        f"{_shared_head(title)}"
        f"{_shared_styles()}"
        "</head>\n<body>\n"
        '  <div class="page">\n'
        '    <div class="container">\n'
        f"      {_topbar(user, 'Добро пожаловать')}\n"
        '      <div class="card">\n'
        '        <div class="hero">\n'
        '          <p class="kicker"><span class="kicker-dot"></span> Аккаунт активирован</p>\n'
        f'          <p class="greeting">Привет, {name}</p>\n'
        '          <h1>Добро пожаловать<br>в <span class="ital">FORK</span>.</h1>\n'
        '          <p class="lede">Спасибо, что присоединились. FORK помогает понимать, что вы едите — без таблиц и подсчётов вручную. Просто сфотографируйте тарелку, остальное мы возьмём на себя.</p>\n'
        '        </div>\n'
        '        <div class="action">\n'
        f'          <a href="{app_url}" class="cta">Сделать первый скан →</a>\n'
        '        </div>\n'
        '        <div class="steps">\n'
        '          <p class="steps-label">С чего начать</p>\n'
        '          <div class="step">\n'
        '            <div class="step-num">01</div>\n'
        '            <div class="step-body">\n'
        '              <p class="step-title">Сфотографируйте еду</p>\n'
        '              <p class="step-text">Откройте FORK, наведите камеру на тарелку под углом примерно 45°. Чем лучше освещение, тем точнее результат.</p>\n'
        '            </div>\n'
        '          </div>\n'
        '          <div class="step">\n'
        '            <div class="step-num">02</div>\n'
        '            <div class="step-body">\n'
        '              <p class="step-title">Получите разбор</p>\n'
        '              <p class="step-text">За пару секунд вы увидите калории, белки, жиры и углеводы — для каждого блюда на тарелке отдельно.</p>\n'
        '            </div>\n'
        '          </div>\n'
        '          <div class="step">\n'
        '            <div class="step-num">03</div>\n'
        '            <div class="step-body">\n'
        '              <p class="step-title">Следите за прогрессом</p>\n'
        '              <p class="step-text">Все приёмы пищи сохраняются в дневнике. Через неделю вы увидите свои привычки в цифрах.</p>\n'
        '            </div>\n'
        '          </div>\n'
        '        </div>\n'
        '        <div class="tip">\n'
        '          <p class="tip-label">Совет</p>\n'
        '          <p class="tip-text"><strong>Положите вилку рядом с тарелкой</strong> перед съёмкой — это помогает FORK точнее оценить размер порции. Маленькая деталь, которая повышает точность примерно на 20%.</p>\n'
        '        </div>\n'
        '      </div>\n'
        f"      {_footer(recipient=recipient, footer_note='Письмо отправлено после подтверждения email.')}\n"
        '    </div>\n'
        '  </div>\n'
        '</body>\n</html>'
    )

    text = _render_text(
        title=title,
        greeting=f"Привет, {name}!",
        body=(
            "Аккаунт защищён, всё готово. FORK помогает понимать, что вы "
            "едите — без таблиц и подсчётов вручную. Несколько советов:\n\n"
            "1. Сфотографируйте еду — наведите камеру на тарелку под углом "
            "примерно 45°. Чем лучше освещение, тем точнее результат.\n"
            "2. Получите разбор — калории, белки, жиры и углеводы для "
            "каждого блюда отдельно.\n"
            "3. Следите за прогрессом — все приёмы пищи сохраняются в "
            "дневнике.\n\n"
            "Совет: положите вилку рядом с тарелкой перед съёмкой — это "
            "повышает точность оценки порции примерно на 20%."
        ),
        button_text="Открыть приложение",
        button_url=app_url,
    )

    return {"subject": subject, "html": html, "text": text}
