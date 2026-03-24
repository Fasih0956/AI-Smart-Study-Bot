"""
Caption Selector Config
Centralizes all DOM selectors so they can be updated in ONE place
when Google/Zoom pushes UI changes — no need to hunt through code.
"""

# ============================================================
# GOOGLE MEET SELECTORS
# Update these if captions stop working after a Google Meet update
# ============================================================
MEET = {
    # Caption container (primary)
    "caption_container": '[jsname="tgaKEf"]',

    # Caption container (fallbacks)
    "caption_fallbacks": [
        ".a4cQT",
        '[aria-live="polite"]',
        '[class*="caption"]',
        '[data-message-text]',
    ],

    # Chat panel
    "chat_button": '[aria-label*="Chat"], [data-tooltip*="Chat"]',
    "chat_messages": '[jsname="xySENc"], .GDhqjd',
    "chat_input": '[aria-label*="Send a message"], [contenteditable="true"]',

    # Controls
    "mic_button": '[aria-label*="microphone"], [jsname="BOHaEe"]',
    "camera_button": '[aria-label*="camera"], [jsname="R3RXj"]',
    "join_button": 'button[jsname="Qx7uuf"], button:has-text("Join now"), button:has-text("Ask to join")',
    "leave_button": '[aria-label*="Leave call"], [jsname="CQylAd"]',
    "more_options": '[aria-label*="More options"]',
    "captions_menu_item": 'li:has-text("Captions")',

    # Meeting ended indicators
    "meeting_ended": [
        ':has-text("The meeting has ended")',
        ':has-text("You\'ve left the meeting")',
        ':has-text("Meeting ended")',
    ],
}

# ============================================================
# ZOOM WEB CLIENT SELECTORS
# ============================================================
ZOOM = {
    "join_from_browser": 'a:has-text("Join from your Browser")',
    "name_input": 'input#inputname, input[placeholder*="name"]',
    "join_button": 'button#joinBtn, button:has-text("Join")',
    "mute_button": '[aria-label*="Mute"]',
    "stop_video": '[aria-label*="Stop Video"]',
    "join_audio": 'button:has-text("Join Audio")',
    "chat_button": '[aria-label*="Chat"]',
    "chat_input": 'textarea.chat-box__chat-textarea',
    "leave_button": 'button:has-text("Leave")',
    "leave_confirm": 'button:has-text("Leave Meeting")',
    "meeting_ended": ':has-text("This meeting has been ended")',
}
