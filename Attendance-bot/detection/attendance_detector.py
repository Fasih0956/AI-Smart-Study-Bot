"""
Attendance Detector - Delta-based. Fully debugged.
"""

import re
import time
from typing import Literal
from core.logger import setup_logger

logger = setup_logger("AttendanceDetector")

ATTENDANCE_EXACT = [
    "اٹینڈنس", "ٹینڈنس", "اٹینڈینس",
    "اٹندڈن", "ٹندڈنس", "اٹندڈنس",
    "پریزنٹ", "پرزنٹ", "رول نمبر",
    "اٹینڈنس مارک", "اٹینڈنس مارک کروا لیں",
    "اٹینڈنس مارک کر رہا ہوں","انٹرنس","ہنڈرنس","اٹینڈنس مارک کر رہی ہوں",
    "attendance", "attendance mark",
    "attendance mark kar raha hun", "attendance mark kar rahi hun",
    "attendance lgwa lain", "attendance lagwa lain",
    "attendance call kar raha hun", "attendance call kar rahi hun",
]

NAME_EXACT = [
    "سی احمد", "وسی احمد", "وسیع احمد",  #replace these with your urdu + english name variants by test and run on google meet.
    "فاصی احمد", "فاسی احمد", "فاصح احمد", "فاسح احمد",
    "فصیح احمد", "فسی احمد", "فصی احمد", "فسیح احمد",
    "فرسی احمد", "پسی احمد", "بس یہ احمد",
    "فرسٹ احمد", "فرسٹ یہ احمد",
    "فاصح", "فاصی", "فاسی", "فصیح", "فسی", "فصی", "فسیح",
    "fasih ahmed", "fasih","فری","فرسی","فارسی"
]

# Specific to roll 24K0956 only
# Urdu STT renders: 24کے09 56, 24کے ز9 فاس, 24کے زیرو9 56 etc
ROLL_PATTERNS = [
    # English/digits: 24K0956, 24K-0956
    re.compile("24\s*[kK]\s*0\s*9\s*5\s*6"),
    # Urdu: 24کے + 09 + 5/56/فاس/فائز/س
    re.compile("24\s*کے\s*09\s*5"),
    re.compile("24\s*کے\s*09\s*فاس"),
    re.compile("24\s*کے\s*09\s*فائز"),
    re.compile("24\s*کے\s*09\s*س"),
    # Urdu: 24کے + زیرو9 + 5/56/فاس etc
    re.compile("24\s*کے\s*زیرو\s*9\s*5"),
    re.compile("24\s*کے\s*زیرو\s*9\s*فاس"),
    re.compile("24\s*کے\s*زیرو\s*9\s*فز"),
    re.compile("24\s*کے\s*زیرو\s*9\s*س"),
    re.compile("24\s*کے\s*زیرو\s*95"),
    # Urdu: 24کے + ز9 + 5/56/فاس (ز = zero shorthand)
    re.compile("24\s*کے\s*ز\s*9\s*5"),
    re.compile("24\s*کے\s*ز\s*9\s*فاس"),
    re.compile("24\s*کے\s*ز\s*95"),
    # Fragment: just 0956
    re.compile("0\s*9\s*5\s*6"),
]


def _is_growing(new, old):
    if not old or len(new) <= len(old):
        return False
    check = min(20, len(old))
    return new[:check] == old[:check]


class AttendanceDetector:
    def __init__(self, config):
        self.student       = config["student"]
        self._prev         = ""
        self._att_on       = False
        self._att_time     = 0.0       # when attendance trigger was set
        self._att_timeout  = 300       # 5 minutes to find name
        self._mic_sent     = False
        self._present_sent = False

    def add_caption(self, text):
        pass  # no-op, logic in analyze

    def analyze(self, caption_text):
        if caption_text == self._prev:
            return "nothing"

        prev       = self._prev
        self._prev = caption_text
        growing    = _is_growing(caption_text, prev)
        delta      = caption_text[len(prev):] if growing else caption_text

        # Reset mic on new caption block (new speaker/topic)
        if not growing and not self._att_on:
            self._mic_sent = False

        att  = self._is_att(delta)
        name = self._is_name(delta)

        logger.info(
            f"[Detector] delta='{delta[-60:]}' "
            f"att={att} name={name} "
            f"att_on={self._att_on} mic={self._mic_sent} present={self._present_sent}"
        )

        # Present already sent — only mic kharab for questions, ignore att
        if self._present_sent:
            if att:
                logger.debug("[Detector] Att seen but present already sent — ignoring")
                return "nothing"
            if name and not self._mic_sent:
                self._mic_sent = True
                time.sleep(1.5)
                logger.info("[Detector] Post-present question → Mic kharab hai")
                return "question_asked"
            return "nothing"

        # Attendance trigger
        if att and not self._att_on:
            self._att_on   = True
            self._att_time = time.time()
            self._mic_sent = False
            logger.info("[Detector] ✓ Attendance triggered — watching for name (5 min)")
            if name:
                self._att_on       = False
                self._att_time     = 0.0
                self._present_sent = True
                time.sleep(1)
                logger.info("[Detector] ✓ PRESENT (att+name together)")
                return "mark_present"
            return "nothing"

        # Waiting for name — check timeout
        if self._att_on:
            elapsed = time.time() - self._att_time
            if elapsed > self._att_timeout:
                logger.info(f"[Detector] ✗ 5min timeout — no name found, resetting")
                self._att_on   = False
                self._att_time = 0.0
                self._mic_sent = False  # allow mic kharab again after timeout

        if self._att_on and name:
            self._att_on       = False
            self._att_time     = 0.0
            self._present_sent = True
            time.sleep(0.3)
            logger.info("[Detector] ✓ PRESENT (name after att)")
            return "mark_present"

        # Name only → mic kharab
        if name and not self._att_on:
            if not self._mic_sent:
                self._mic_sent = True
                time.sleep(1)
                logger.info("[Detector] Mic kharab hai")
                return "question_asked"
            return "nothing"

        return "nothing"

    def reset(self):
        self._att_on       = False
        self._att_time     = 0.0       # when attendance trigger was set
        self._att_timeout  = 420       # 5 minutes to find name
        self._mic_sent     = False
        self._present_sent = False
        self._prev         = ""

    def _is_att(self, text):
        t = text.lower()
        return any(p.lower() in t for p in ATTENDANCE_EXACT)

    def _is_name(self, text):
        t = text.lower()
        if any(n.lower() in t for n in NAME_EXACT):
            return True
        return any(p.search(text) for p in ROLL_PATTERNS)