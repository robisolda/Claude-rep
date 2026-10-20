import Toybox.Activity;
import Toybox.ActivityMonitor;
import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Time;
import Toybox.Time.Gregorian;
import Toybox.WatchUi;

// Segmenti accesi per ogni cifra: bit0=a (alto) ... bit6=g (centrale)
const SEGMENT_MAP = [0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F] as Array<Number>;

// Inclinazione delle cifre, come sui display LCD Casio
const SLANT = 0.08;

const DAY_NAMES = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"] as Array<String>;

// Colori: [sfondo, logo, accento 1, accento 2, cornice LCD, LCD, segmento acceso, segmento spento]
const THEMES = [
    [0x000000, 0xFFFFFF, 0xE8A33D, 0x4C8DD6, 0x2E2E2E, 0xA7B394, 0x1B2016, 0x97A385], // Classico F-91W
    [0x000000, 0xFFFFFF, 0xD04030, 0x8C8C8C, 0x3A3A3A, 0x0E0F0E, 0xE6D9A8, 0x1E201C], // Negativo
    [0xC8A044, 0x1A1408, 0x3B2A08, 0x5A4310, 0x8A6A20, 0xA7B394, 0x1B2016, 0x97A385], // Oro A168
    [0x000000, 0xFFFFFF, 0xE8A33D, 0x4C8DD6, 0x2E2E2E, 0x5FC7B0, 0x0D2A24, 0x52B39E]  // Illuminator
] as Array<Array<Number>>;

class CasioRetroView extends WatchUi.WatchFace {

    private var mW as Number = 0;
    private var mH as Number = 0;

    // Area del display LCD
    private var mLcdX as Float = 0.0;
    private var mLcdY as Float = 0.0;
    private var mLcdW as Float = 0.0;
    private var mLcdH as Float = 0.0;

    // Geometria cifre principali (ore e minuti)
    private var mDigitW as Float = 0.0;
    private var mDigitH as Float = 0.0;
    private var mDigitY as Float = 0.0;
    private var mTimeX as Float = 0.0;
    private var mSpacing as Float = 0.0;
    private var mColonW as Float = 0.0;

    // Geometria secondi
    private var mSecX as Float = 0.0;
    private var mSecY as Float = 0.0;
    private var mSecW as Float = 0.0;
    private var mSecH as Float = 0.0;
    private var mSecSpacing as Float = 0.0;

    private var mSleeping as Boolean = false;

    // Colori correnti
    private var mOn as Number = 0;
    private var mGhost as Number? = null;
    private var mTheme as Array<Number> = THEMES[0];

    function initialize() {
        WatchFace.initialize();
    }

    function onLayout(dc as Graphics.Dc) as Void {
        mW = dc.getWidth();
        mH = dc.getHeight();

        mLcdW = mW * 0.80;
        mLcdH = mH * 0.33;
        mLcdX = (mW - mLcdW) / 2.0;
        mLcdY = mH * 0.335;

        mDigitH = mLcdH * 0.56;
        mDigitW = mDigitH * 0.52;
        mSpacing = mDigitW * 0.22;
        mColonW = mDigitW * 0.45;
        mDigitY = mLcdY + mLcdH * 0.33;

        mSecH = mDigitH * 0.6;
        mSecW = mSecH * 0.55;
        mSecSpacing = mSecW * 0.22;

        var secGap = mDigitW * 0.30;
        var totalW = 4 * mDigitW + 2 * mSpacing + mColonW + secGap + 2 * mSecW + mSecSpacing;
        mTimeX = mLcdX + (mLcdW - totalW) / 2.0;
        mSecX = mTimeX + 4 * mDigitW + 2 * mSpacing + mColonW + secGap;
        mSecY = mDigitY + mDigitH - mSecH;
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        loadTheme();

        var clock = System.getClockTime();
        var settings = System.getDeviceSettings();

        if (mSleeping && settings.requiresBurnInProtection) {
            drawAlwaysOn(dc, clock, settings.is24Hour);
            return;
        }

        drawFrame(dc);
        drawLcd(dc, clock, settings.is24Hour);
    }

    // Su display MIP aggiorna i secondi anche in modalita' a basso consumo
    function onPartialUpdate(dc as Graphics.Dc) as Void {
        if (System.getDeviceSettings().requiresBurnInProtection) {
            return;
        }
        var clipX = (mSecX - 2).toNumber();
        var clipY = (mSecY - 2).toNumber();
        var clipW = (2 * mSecW + mSecSpacing + mSecH * SLANT + 4).toNumber();
        var clipH = (mSecH + 4).toNumber();
        dc.setClip(clipX, clipY, clipW, clipH);
        dc.setColor(mTheme[5], mTheme[5]);
        dc.fillRectangle(clipX, clipY, clipW, clipH);
        drawSeconds(dc, System.getClockTime().sec);
        dc.clearClip();
    }

    function onEnterSleep() as Void {
        mSleeping = true;
        WatchUi.requestUpdate();
    }

    function onExitSleep() as Void {
        mSleeping = false;
        WatchUi.requestUpdate();
    }

    private function loadTheme() as Void {
        var idx = 0;
        var ghost = true;
        try {
            var t = Application.Properties.getValue("Theme");
            if (t instanceof Number && t >= 0 && t < THEMES.size()) {
                idx = t;
            }
            var g = Application.Properties.getValue("ShowGhost");
            if (g instanceof Boolean) {
                ghost = g;
            }
        } catch (e) {
        }
        mTheme = THEMES[idx];
        mOn = mTheme[6];
        mGhost = ghost ? mTheme[7] : null;
    }

    // Cassa: logo, scritte e dati sotto il display
    private function drawFrame(dc as Graphics.Dc) as Void {
        var cx = mW / 2;
        var justify = Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER;

        dc.setColor(mTheme[0], mTheme[0]);
        dc.clear();

        dc.setColor(mTheme[1], Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, mH * 0.17, Graphics.FONT_MEDIUM, "CASIO", justify);

        dc.setColor(mTheme[2], Graphics.COLOR_TRANSPARENT);
        dc.drawText(mLcdX + mLcdW * 0.04, mH * 0.275, Graphics.FONT_XTINY, "LIGHT",
            Graphics.TEXT_JUSTIFY_LEFT | Graphics.TEXT_JUSTIFY_VCENTER);
        dc.setColor(mTheme[3], Graphics.COLOR_TRANSPARENT);
        dc.drawText(mLcdX + mLcdW * 0.96, mH * 0.275, Graphics.FONT_XTINY, "ALARM CHRONOGRAPH",
            Graphics.TEXT_JUSTIFY_RIGHT | Graphics.TEXT_JUSTIFY_VCENTER);

        // Cornice del display
        var pad = mW * 0.018;
        dc.setColor(mTheme[4], mTheme[4]);
        dc.fillRoundedRectangle(mLcdX - pad, mLcdY - pad, mLcdW + 2 * pad, mLcdH + 2 * pad, pad * 1.5);
        dc.setColor(mTheme[2], Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(2);
        dc.drawRoundedRectangle(mLcdX - pad, mLcdY - pad, mLcdW + 2 * pad, mLcdH + 2 * pad, pad * 1.5);
        dc.setPenWidth(1);

        dc.setColor(mTheme[3], Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, mH * 0.725, Graphics.FONT_XTINY, "WATER  WR  RESIST", justify);

        dc.setColor(mTheme[2], Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, mH * 0.80, Graphics.FONT_XTINY, getStatsLine(), justify);

        dc.setColor(mTheme[1], Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, mH * 0.875, Graphics.FONT_XTINY, "LITHIUM", justify);
    }

    private function getStatsLine() as String {
        var hr = "--";
        var info = Activity.getActivityInfo();
        if (info != null && info.currentHeartRate != null) {
            hr = info.currentHeartRate.toString();
        } else {
            var it = ActivityMonitor.getHeartRateHistory(1, true);
            var sample = it.next();
            if (sample != null && sample.heartRate != ActivityMonitor.INVALID_HR_SAMPLE) {
                hr = sample.heartRate.toString();
            }
        }

        var steps = "--";
        var am = ActivityMonitor.getInfo();
        if (am.steps != null) {
            steps = am.steps.toString();
        }

        var bat = System.getSystemStats().battery.toNumber();
        return "HR " + hr + "   STEP " + steps + "   " + bat + "%";
    }

    private function drawLcd(dc as Graphics.Dc, clock as System.ClockTime, is24 as Boolean) as Void {
        dc.setColor(mTheme[5], mTheme[5]);
        dc.fillRoundedRectangle(mLcdX, mLcdY, mLcdW, mLcdH, mW * 0.012);

        // Riga superiore: giorno della settimana, indicatore PM/24H, data
        var now = Gregorian.info(Time.now(), Time.FORMAT_SHORT);
        var rowY = mLcdY + mLcdH * 0.17;
        dc.setColor(mOn, Graphics.COLOR_TRANSPARENT);
        dc.drawText(mLcdX + mLcdW * 0.06, rowY, Graphics.FONT_SMALL, DAY_NAMES[(now.day_of_week as Number) - 1],
            Graphics.TEXT_JUSTIFY_LEFT | Graphics.TEXT_JUSTIFY_VCENTER);

        var mode = is24 ? "24H" : (clock.hour >= 12 ? "PM" : "");
        if (mode.length() > 0) {
            dc.drawText(mLcdX + mLcdW * 0.30, rowY, Graphics.FONT_XTINY, mode,
                Graphics.TEXT_JUSTIFY_LEFT | Graphics.TEXT_JUSTIFY_VCENTER);
        }

        var dh = mLcdH * 0.2;
        var dw = dh * 0.55;
        var dateX = mLcdX + mLcdW * 0.94 - 2 * dw - dw * 0.25;
        var dateY = rowY - dh / 2;
        var day = now.day as Number;
        drawDigit(dc, dateX, dateY, dw, dh, day >= 10 ? day / 10 : -1);
        drawDigit(dc, dateX + dw * 1.25, dateY, dw, dh, day % 10);

        drawTime(dc, mTimeX, mDigitY, clock, is24);
        drawSeconds(dc, clock.sec);
    }

    private function drawTime(dc as Graphics.Dc, x as Float, y as Float, clock as System.ClockTime, is24 as Boolean) as Void {
        var hour = clock.hour;
        if (!is24) {
            hour = hour % 12;
            if (hour == 0) {
                hour = 12;
            }
        }
        var step = mDigitW + mSpacing;

        // Come sui Casio, lo zero iniziale dell'ora non viene mostrato
        drawDigit(dc, x, y, mDigitW, mDigitH, hour >= 10 ? hour / 10 : -1);
        drawDigit(dc, x + step, y, mDigitW, mDigitH, hour % 10);
        var colonX = x + 2 * mDigitW + mSpacing;
        drawColon(dc, colonX, y, mColonW, mDigitH);
        var mx = colonX + mColonW;
        drawDigit(dc, mx, y, mDigitW, mDigitH, clock.min / 10);
        drawDigit(dc, mx + step, y, mDigitW, mDigitH, clock.min % 10);
    }

    private function drawSeconds(dc as Graphics.Dc, sec as Number) as Void {
        drawDigit(dc, mSecX, mSecY, mSecW, mSecH, sec / 10);
        drawDigit(dc, mSecX + mSecW + mSecSpacing, mSecY, mSecW, mSecH, sec % 10);
    }

    // Always-on per AMOLED: solo i segmenti accesi, attenuati e spostati ogni minuto
    private function drawAlwaysOn(dc as Graphics.Dc, clock as System.ClockTime, is24 as Boolean) as Void {
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();

        mOn = 0x707070;
        mGhost = null;

        var shiftX = ((clock.min % 5) - 2) * mW * 0.012;
        var shiftY = (((clock.min / 5) % 5) - 2) * mH * 0.012;
        var timeW = 4 * mDigitW + 2 * mSpacing + mColonW;
        var x = (mW - timeW) / 2.0 + shiftX;
        var y = (mH - mDigitH) / 2.0 + shiftY;
        drawTime(dc, x, y, clock, is24);
    }

    // --- Display a 7 segmenti ---

    private function drawDigit(dc as Graphics.Dc, x as Float, y as Float, w as Float, h as Float, value as Number) as Void {
        var t = w * 0.2;
        var g = t * 0.15 + 0.5;
        var mask = value >= 0 ? SEGMENT_MAP[value] : 0;

        var l = x + t / 2;
        var r = x + w - t / 2;
        var top = y + t / 2;
        var mid = y + h / 2;
        var bot = y + h - t / 2;
        var base = y + h;

        for (var s = 0; s < 7; s++) {
            var on = (mask & (1 << s)) != 0;
            if (on) {
                dc.setColor(mOn, Graphics.COLOR_TRANSPARENT);
            } else if (mGhost != null) {
                dc.setColor(mGhost, Graphics.COLOR_TRANSPARENT);
            } else {
                continue;
            }

            if (s == 0) {
                hSeg(dc, l + g, r - g, top, t, base);
            } else if (s == 1) {
                vSeg(dc, r, top + g, mid - g, t, base);
            } else if (s == 2) {
                vSeg(dc, r, mid + g, bot - g, t, base);
            } else if (s == 3) {
                hSeg(dc, l + g, r - g, bot, t, base);
            } else if (s == 4) {
                vSeg(dc, l, mid + g, bot - g, t, base);
            } else if (s == 5) {
                vSeg(dc, l, top + g, mid - g, t, base);
            } else {
                hSeg(dc, l + g, r - g, mid, t, base);
            }
        }
    }

    private function drawColon(dc as Graphics.Dc, x as Float, y as Float, w as Float, h as Float) as Void {
        var size = mDigitW * 0.18;
        var cx = x + w / 2;
        var base = y + h;
        dc.setColor(mOn, Graphics.COLOR_TRANSPARENT);
        dotAt(dc, cx, y + h * 0.32, size, base);
        dotAt(dc, cx, y + h * 0.70, size, base);
    }

    private function dotAt(dc as Graphics.Dc, cx as Float, cy as Float, size as Float, base as Float) as Void {
        var hs = size / 2;
        dc.fillPolygon([
            pt(cx - hs, cy - hs, base), pt(cx + hs, cy - hs, base),
            pt(cx + hs, cy + hs, base), pt(cx - hs, cy + hs, base)
        ]);
    }

    // Segmento orizzontale a forma esagonale
    private function hSeg(dc as Graphics.Dc, x1 as Float, x2 as Float, y as Float, t as Float, base as Float) as Void {
        var h2 = t / 2;
        dc.fillPolygon([
            pt(x1, y, base), pt(x1 + h2, y - h2, base), pt(x2 - h2, y - h2, base),
            pt(x2, y, base), pt(x2 - h2, y + h2, base), pt(x1 + h2, y + h2, base)
        ]);
    }

    // Segmento verticale a forma esagonale
    private function vSeg(dc as Graphics.Dc, x as Float, y1 as Float, y2 as Float, t as Float, base as Float) as Void {
        var h2 = t / 2;
        dc.fillPolygon([
            pt(x, y1, base), pt(x + h2, y1 + h2, base), pt(x + h2, y2 - h2, base),
            pt(x, y2, base), pt(x - h2, y2 - h2, base), pt(x - h2, y1 + h2, base)
        ]);
    }

    private function pt(x as Float, y as Float, base as Float) as Graphics.Point2D {
        return [x + (base - y) * SLANT, y];
    }
}
