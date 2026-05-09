"""Email templates — HTML + plain-text pairs.

Three transactional templates:
  - confirm — "Подтвердите email"  (sent after register / email change)
  - reset   — "Сброс пароля"        (sent on password-reset/request)
  - welcome — "Добро пожаловать"    (sent after email is verified)

Each public function returns a dict { subject, html, text } that the
calling endpoint passes straight to send_email().

Phase 8 — redesigned to match the brutalist cream/dark mockups in
`Email Mockups/`. Personalization, dynamic dates, account-id topbar.

Phase 9 — layout converted from CSS flexbox to table-based markup.
The mockups looked great in browsers but Gmail mobile / Yandex /
Mail.ru / Outlook all stripped or mishandled `display: flex`,
producing the "АДРЕС stacked above email", "Срок действия24 часа"
joined-without-space, and "Поддержка Отправитель Получатель" smashed-
to-one-line failures. Tables are the only horizontal-layout
primitive 100% of email clients render correctly (the entire
transactional-email industry uses them for this reason).
Plus `color-scheme: light only` meta tags to prevent Gmail Android
from inverting the cream/dark palette in dark mode.

Design system:
  - Cream page bg #ebe5d8, light card #f6f1e6, dark accent #0e0d0a
  - Ochre kicker dot #b54a1f for editorial accent
  - Fraunces serif headlines (300-weight, italic emphasis), Inter body,
    JetBrains Mono labels — loaded via Google Fonts in <head> with
    system fallbacks for clients that strip web fonts
  - 580px max width, mobile-first @media query stacks horizontal
    rows into single-column blocks below 540px

Constraints:
  - Inline <style> block (Gmail/Yandex honor it; older Outlook
    falls back to default styling, layout still works because tables)
  - Single column at the page level, no nested complex layouts
  - One primary CTA per email — focused action
  - Plain-text alternative for every HTML — required for inbox
    deliverability (anti-spam scoring penalises HTML-only mail)
  - No tracking pixels, no remote images — only Google Fonts CSS
  - Russian copy throughout, polite "вы" address, soft warm tone
"""

from datetime import datetime, timezone, timedelta

from server.config import (
    OPERATOR_NAME, OPERATOR_CITY, UNISENDER_FROM_EMAIL, UNISENDER_FROM_NAME,
)


_TELEGRAM_SUPPORT_URL    = "https://t.me/ForkWorkBro"
_TELEGRAM_SUPPORT_HANDLE = "@ForkWorkBro"


_RU_MONTHS = (
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
)


# Moscow time — operator data localisation requires Russian-locale
# dates. UTC+3, no DST.
_MSK_TZ = timezone(timedelta(hours=3))


def _current_month_year_ru() -> str:
    """e.g. "Май · 2026" rendered fresh per send in Moscow time."""
    now = datetime.now(_MSK_TZ)
    return f"{_RU_MONTHS[now.month - 1]} · {now.year}"


def _resolve_user_name(user: dict | None) -> str:
    """display_name → username → "Гость" fallback chain."""
    if not user:
        return "Гость"
    for key in ("display_name", "username"):
        name = (user.get(key) or "").strip()
        if name:
            return name
    return "Гость"


def _format_account_id(user: dict | None) -> str:
    """`№ 000061` — mirrors the in-app `#000061` Account Settings format."""
    if not user:
        return "№ ——"
    uid = user.get("id")
    if uid is None:
        return "№ ——"
    return f"№ {str(uid).zfill(6)}"


# ── Common font stacks (used so often it's worth aliasing) ──────────────
_F_BODY = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
_F_DISP = "'Fraunces', 'Cormorant Garamond', Georgia, 'Times New Roman', serif"
_F_MONO = "'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace"


def _shared_head(title: str) -> str:
    """The <head> block reused across all templates. Phase 9 added
    the `color-scheme: light only` meta pair to stop Gmail Android
    from auto-inverting the cream/dark palette in dark mode."""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light only">
<meta name="supported-color-schemes" content="light only">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
"""


def _shared_styles() -> str:
    """Inline <style> block. Phase 9 stripped every `display: flex`
    rule — horizontal rows are now tables, which is the only layout
    primitive 100% of email clients render reliably. Typography,
    colors, padding, borders all stay; only layout primitives changed."""
    return f"""<style>
  body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
  table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-collapse: collapse; }}
  img {{ border: 0; outline: none; display: block; }}
  body {{ margin: 0; padding: 0; width: 100% !important; }}
  a {{ color: inherit; text-decoration: none; }}

  body {{
    background: #ebe5d8;
    font-family: {_F_BODY};
    color: #0e0d0a;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }}

  .page {{ width: 100%; background: #ebe5d8; padding: 32px 16px 48px 16px; }}
  .container {{ max-width: 580px; margin: 0 auto; }}

  /* Topbar — 2-col table now. Logo left, dated meta right. */
  .topbar {{ padding: 8px 4px 28px 4px; }}
  .topbar td {{ vertical-align: middle; }}
  .topbar .logo-mark {{ width: 88px; height: auto; color: #0e0d0a; display: block; }}
  .topbar-meta {{
    text-align: right; line-height: 1.6;
    font-family: {_F_MONO};
    font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase; color: #6f6a5d;
  }}

  .card {{ background: #f6f1e6; border: 1px solid #0e0d0a; }}

  .hero {{ padding: 56px 44px 36px 44px; border-bottom: 1px solid #0e0d0a; }}

  /* Kicker — inline-block dot for guaranteed spacing across clients.
     The `&nbsp;` after the closing span enforces ≥ 1 space-width gap
     even when CSS margin/padding gets stripped. */
  .kicker {{
    margin: 0 0 16px 0;
    font-family: {_F_MONO};
    font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase;
    color: #0e0d0a;
  }}
  .kicker-dot {{
    display: inline-block;
    width: 8px; height: 8px; background: #b54a1f;
    vertical-align: middle;
    margin-right: 12px;
    margin-bottom: 2px;
  }}

  .greeting {{
    margin: 0 0 14px 0;
    font-family: {_F_MONO};
    font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase;
    color: #6f6a5d;
  }}

  h1 {{
    font-family: {_F_DISP};
    font-weight: 300; font-size: 56px; line-height: 0.96; letter-spacing: -0.035em;
    color: #0e0d0a; margin: 0;
  }}
  h1 .ital {{ font-style: italic; font-weight: 300; }}

  .lede {{ margin: 28px 0 0 0; font-size: 15px; line-height: 1.6; color: #2a2823; max-width: 460px; font-weight: 400; }}

  /* Addressed row — 2-col table */
  .addressed {{ padding: 24px 44px; border-bottom: 1px solid #0e0d0a; }}
  .addressed-label {{
    font-family: {_F_MONO};
    font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase;
    color: #6f6a5d; padding-right: 16px;
  }}
  .addressed-value {{
    font-family: {_F_MONO};
    font-size: 13px; color: #0e0d0a; font-weight: 500; word-break: break-all;
  }}

  /* Action — CTA + meta row beneath */
  .action {{ padding: 44px; border-bottom: 1px solid #0e0d0a; }}
  .cta {{
    display: block; width: 100%; box-sizing: border-box;
    background: #0e0d0a; color: #f6f1e6 !important;
    text-decoration: none; text-align: center;
    font-family: {_F_BODY}; font-weight: 500;
    font-size: 15px; letter-spacing: 0.04em; text-transform: uppercase;
    padding: 22px 28px; line-height: 1; border: 0;
  }}
  .cta:hover {{ background: #b54a1f; }}

  .action-meta {{
    margin: 18px 0 0 0;
  }}
  .action-meta-cell {{
    font-family: {_F_MONO};
    font-size: 11px; letter-spacing: 0.06em; color: #6f6a5d;
    text-transform: uppercase;
  }}

  /* Fallback URL block */
  .fallback {{ padding: 28px 44px; border-bottom: 1px solid #0e0d0a; }}
  .fallback-label {{
    font-family: {_F_MONO};
    font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase;
    color: #6f6a5d; margin: 0 0 10px 0;
  }}
  .fallback-url {{
    font-family: {_F_MONO};
    font-size: 12.5px; color: #0e0d0a; word-break: break-all; line-height: 1.55;
  }}

  /* Inverted security/tip block at the bottom of the card */
  .security, .tip {{ padding: 28px 44px; background: #0e0d0a; color: #d6d1c2; }}
  .security-label, .tip-label {{
    font-family: {_F_MONO};
    font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase;
    color: #8a8678; margin: 0 0 10px 0;
  }}
  .security-text, .tip-text {{ font-size: 14px; line-height: 1.55; color: #ebe5d8; margin: 0; font-weight: 400; }}
  .security-text strong, .tip-text strong {{ color: #ffffff; font-weight: 500; }}

  /* Welcome onboarding — numbered steps. Each step is a 2-col table. */
  .steps {{ padding: 8px 44px 28px 44px; border-bottom: 1px solid #0e0d0a; }}
  .steps-label {{
    font-family: {_F_MONO};
    font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase;
    color: #6f6a5d; margin: 24px 0 24px 0;
  }}
  .step-row {{
    padding: 20px 0;
    border-top: 1px solid rgba(14, 13, 10, 0.12);
  }}
  .step-row.first {{ border-top: 0; padding-top: 4px; }}
  .step-num {{
    font-family: {_F_MONO};
    font-size: 11px; letter-spacing: 0.06em;
    color: #6f6a5d; padding-right: 20px; padding-top: 2px;
    width: 32px;
  }}
  .step-title {{
    font-family: {_F_BODY}; font-weight: 500;
    font-size: 15px; color: #0e0d0a; margin: 0 0 4px 0;
    letter-spacing: -0.005em;
  }}
  .step-text {{ font-size: 13.5px; line-height: 1.55; color: #4d4940; margin: 0; }}

  /* Footer — 3-col table */
  .footer {{ padding: 28px 4px 0 4px; }}
  .footer-grid {{
    padding-bottom: 20px; border-bottom: 1px solid #0e0d0a;
  }}
  .footer-cell {{
    vertical-align: top;
    padding-right: 24px;
  }}
  .footer-cell.last {{ padding-right: 0; }}
  .footer-label {{
    font-family: {_F_MONO};
    font-size: 9.5px; letter-spacing: 0.18em; text-transform: uppercase;
    color: #6f6a5d; margin: 0 0 6px 0;
  }}
  .footer-value {{ font-size: 12.5px; color: #0e0d0a; line-height: 1.55; margin: 0; word-break: break-all; }}
  .footer-value a {{ color: #0e0d0a; border-bottom: 1px solid #0e0d0a; padding-bottom: 1px; }}

  .footer-fine {{
    margin-top: 18px;
    font-family: {_F_MONO};
    font-size: 10px; letter-spacing: 0.06em; line-height: 1.7;
    color: #6f6a5d; text-transform: uppercase;
  }}

  /* Mobile <540px — collapse 2/3-col tables to single-column blocks. */
  @media (max-width: 540px) {{
    .page {{ padding: 20px 12px 36px 12px; }}
    .hero {{ padding: 40px 24px 28px 24px; }}
    .addressed, .action, .fallback, .security, .tip, .steps {{ padding-left: 24px; padding-right: 24px; }}
    h1 {{ font-size: 40px; }}
    .stack-on-mobile td {{
      display: block !important;
      width: 100% !important;
      text-align: left !important;
      padding-right: 0 !important;
      padding-bottom: 12px !important;
    }}
    .stack-on-mobile td.no-stack-pad {{ padding-bottom: 0 !important; }}
  }}
</style>"""


def _logo_svg() -> str:
    """The fork wordmark — same monoline geometric SVG used in the app
    header. currentColor inheritance keeps it brand-correct."""
    return """<svg class="logo-mark" viewBox="0 0 78 32" fill="none" stroke="currentColor" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="fork">
              <path d="M 17 5 Q 12 5 12 8.5 L 12 28"/>
              <path d="M 5 14 L 18 14"/>
              <circle cx="30" cy="19" r="9"/>
              <path d="M 44 28 L 44 12 Q 44 9.5 47 9.5 Q 52 9.5 54 13"/>
              <path d="M 60 5 L 60 28"/>
              <path d="M 60 20 L 72 12"/>
              <path d="M 60 20 L 72 28"/>
            </svg>"""


def _topbar(user: dict | None, issue_label: str) -> str:
    """Dated brutalist letterhead. Phase 9: 2-col table replacing
    flex. Left cell: fork wordmark. Right cell: account-id + issue
    label + dated month/year."""
    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="topbar stack-on-mobile">
        <tr>
          <td>{_logo_svg()}</td>
          <td class="topbar-meta" align="right">
            {_format_account_id(user)} · {issue_label}<br>
            {_current_month_year_ru()}
          </td>
        </tr>
      </table>"""


def _kicker(text: str) -> str:
    """Editorial kicker — orange dot + uppercase label. Phase 9 uses
    `display: inline-block` on the dot + a non-breaking space for
    guaranteed spacing in clients that strip CSS margins."""
    return f'<p class="kicker"><span class="kicker-dot"></span>&nbsp;{text}</p>'


def _addressed_row(label: str, value: str) -> str:
    """2-col label/value row. Phase 9: was flex with
    justify-content:space-between, which Gmail mobile collapsed —
    now a 2-col table that Gmail/Yandex/Outlook all render correctly."""
    return f"""<div class="addressed">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="stack-on-mobile">
          <tr>
            <td class="addressed-label" valign="middle">{label}</td>
            <td class="addressed-value" valign="middle" align="right">{value}</td>
          </tr>
        </table>
      </div>"""


def _action_meta(left: str, right: str) -> str:
    """Beneath the CTA — "Срок действия | 24 часа" style row. Phase 9:
    was flex space-between which Gmail rendered as "Срок действия24 часа"
    with no gap. Now a 2-col table with explicit left/right alignment."""
    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="action-meta stack-on-mobile">
        <tr>
          <td class="action-meta-cell" valign="middle">{left}</td>
          <td class="action-meta-cell" valign="middle" align="right">{right}</td>
        </tr>
      </table>"""


def _step(num: str, title: str, text: str, *, first: bool = False) -> str:
    """Welcome onboarding step — 2-col table. Number gutter on the
    left, title + body on the right."""
    cls = "step-row first" if first else "step-row"
    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="{cls}">
            <tr>
              <td class="step-num" valign="top">{num}</td>
              <td valign="top">
                <p class="step-title">{title}</p>
                <p class="step-text">{text}</p>
              </td>
            </tr>
          </table>"""


def _footer(*, recipient: str, sender_email: str = "", footer_note: str = "") -> str:
    """3-col metadata footer + fine print. Phase 9: was flex
    justify-content:space-between with gap, which Gmail collapsed to
    one line of crammed labels. Now a 3-col table; on mobile the
    `stack-on-mobile` class collapses to single column."""
    sender = sender_email or UNISENDER_FROM_EMAIL
    return f"""<div class="footer">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="footer-grid stack-on-mobile">
          <tr>
            <td class="footer-cell" width="33%">
              <p class="footer-label">Поддержка</p>
              <p class="footer-value"><a href="{_TELEGRAM_SUPPORT_URL}">{_TELEGRAM_SUPPORT_HANDLE}</a></p>
            </td>
            <td class="footer-cell" width="34%">
              <p class="footer-label">Отправитель</p>
              <p class="footer-value">{sender}</p>
            </td>
            <td class="footer-cell last" width="33%">
              <p class="footer-label">Получатель</p>
              <p class="footer-value">{recipient}</p>
            </td>
          </tr>
        </table>
        <p class="footer-fine">
          {footer_note or "Служебное сообщение. Отвечать не нужно."}<br>
          Оператор данных — {OPERATOR_NAME}, {OPERATOR_CITY}.
        </p>
      </div>"""


# ── Plain-text wrapper ────────────────────────────────────────────────────


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
        f'          {_kicker("Один шаг до старта")}\n'
        f'          <p class="greeting">Привет, {name}</p>\n'
        '          <h1>Подтвердите<br>ваш <span class="ital">email</span>.</h1>\n'
        '          <p class="lede">Спасибо, что выбрали FORK. Чтобы завершить регистрацию и защитить аккаунт, подтвердите, что этот адрес действительно принадлежит вам.</p>\n'
        '        </div>\n'
        f"        {_addressed_row('Адрес', recipient)}\n"
        '        <div class="action">\n'
        f'          <a href="{verify_url}" class="cta">Подтвердить email →</a>\n'
        f"          {_action_meta('Срок действия', '24 часа')}\n"
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
    /api/auth/password-reset/request.
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
        f'          {_kicker("Запрос получен")}\n'
        f'          <p class="greeting">Привет, {name}</p>\n'
        '          <h1>Сбросьте<br>ваш <span class="ital">пароль</span>.</h1>\n'
        '          <p class="lede">Мы получили запрос на сброс пароля для вашего аккаунта. Нажмите на кнопку ниже, чтобы задать новый пароль.</p>\n'
        '        </div>\n'
        f"        {_addressed_row('Аккаунт', recipient)}\n"
        '        <div class="action">\n'
        f'          <a href="{reset_url}" class="cta">Задать новый пароль →</a>\n'
        f"          {_action_meta('Срок действия', '1 час')}\n"
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
    to 1. Three numbered onboarding steps + a tip. Single CTA back
    to the scanner.
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
        f'          {_kicker("Аккаунт активирован")}\n'
        f'          <p class="greeting">Привет, {name}</p>\n'
        '          <h1>Добро пожаловать<br>в <span class="ital">FORK</span>.</h1>\n'
        '          <p class="lede">Спасибо, что присоединились. FORK помогает понимать, что вы едите — без таблиц и подсчётов вручную. Просто сфотографируйте тарелку, остальное мы возьмём на себя.</p>\n'
        '        </div>\n'
        '        <div class="action">\n'
        f'          <a href="{app_url}" class="cta">Сделать первый скан →</a>\n'
        '        </div>\n'
        '        <div class="steps">\n'
        '          <p class="steps-label">С чего начать</p>\n'
        f"          {_step('01', 'Сфотографируйте еду', 'Откройте FORK, наведите камеру на тарелку под углом примерно 45°. Чем лучше освещение, тем точнее результат.', first=True)}\n"
        f"          {_step('02', 'Получите разбор', 'За пару секунд вы увидите калории, белки, жиры и углеводы — для каждого блюда на тарелке отдельно.')}\n"
        f"          {_step('03', 'Следите за прогрессом', 'Все приёмы пищи сохраняются в дневнике. Через неделю вы увидите свои привычки в цифрах.')}\n"
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
