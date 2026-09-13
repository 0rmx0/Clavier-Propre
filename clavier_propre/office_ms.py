"""Pilotage de la correction automatique de Microsoft Office (Word) via COM.

On utilise l'API COM Word (``Options.CheckSpellingAsYouType``,
``Options.CheckGrammarAsYouType``, ``AutoCorrect``) au travers de ``win32com``.
Ces réglages sont globaux à l'application Word ; ils sont donc appliqués à
l'instance en cours si elle existe, ou à une instance transiente créée pour
l'occasion (les modifications persistent ensuite pour tous les documents).

    active=True  -> on DÉSACTIVE la correction (mode « propre »)
    active=False -> on RÉACTIVE la correction (comportement normal)
"""
from __future__ import annotations

import logging
import platform

log = logging.getLogger(__name__)

_IS_WINDOWS = platform.system() == "Windows"


def _get_word_app():
    """Retourne une instance COM de Word, en réutilisant celle en cours si elle
    existe, sinon en lançant une instance éphémère."""
    if not _IS_WINDOWS:
        return None
    try:
        import win32com.client  # type: ignore[import-not-found]
        import pythoncom  # type: ignore[import-not-found]
    except ImportError:
        log.warning("pywin32 indisponible : gestion Word ignorée.")
        return None

    try:
        pythoncom.CoInitialize()
    except Exception:  # pragma: no cover
        pass
    try:
        return win32com.client.GetActiveObject("Word.Application")
    except Exception:
        try:
            return win32com.client.DispatchEx("Word.Application")
        except Exception as exc:
            log.warning("Word indisponible via COM: %s", exc)
            return None


def _get_excel_app():
    if not _IS_WINDOWS:
        return None
    try:
        import win32com.client  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        return win32com.client.GetActiveObject("Excel.Application")
    except Exception:
        try:
            return win32com.client.DispatchEx("Excel.Application")
        except Exception:
            return None


def _get_powerpoint_app():
    if not _IS_WINDOWS:
        return None
    try:
        import win32com.client  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        return win32com.client.GetActiveObject("PowerPoint.Application")
    except Exception:
        try:
            return win32com.client.DispatchEx("PowerPoint.Application")
        except Exception:
            return None


def _set_word_options(app, active: bool) -> None:
    # active=True => on désactive la correction (suggestions off)
    value = not active
    try:
        app.Options.CheckSpellingAsYouType = value
    except Exception as exc:  # pragma: no cover
        log.debug("CheckSpellingAsYouType: %s", exc)
    try:
        app.Options.CheckGrammarAsYouType = value
    except Exception as exc:  # pragma: no cover
        log.debug("CheckGrammarAsYouType: %s", exc)
    try:
        app.AutoCorrect.AutoCorrectReplace = value
        app.AutoCorrect.AutoCorrectCorrectCapsLock = value
        app.AutoCorrect.ReplaceText = value
    except Exception as exc:  # pragma: no cover
        log.debug("AutoCorrect: %s", exc)
    try:
        app.Application.ScreenRefresh()
    except Exception:
        pass


def _set_excel_options(app, active: bool) -> None:
    value = not active
    try:
        app.Application.CheckSpellingAsYouType = False if active else True
    except Exception as exc:  # pragma: no cover
        log.debug("Excel CheckSpellingAsYouType: %s", exc)


def _set_powerpoint_options(app, active: bool) -> None:
    value = not active
    try:
        app.Options.SpellingInfo = value
    except Exception as exc:  # pragma: no cover
        log.debug("PowerPoint SpellingInfo: %s", exc)


def apply_office_protection(active: bool) -> None:
    """``active=True`` : désactive la correction automatique de Microsoft Office.
    ``active=False`` : la réactive."""
    if not _IS_WINDOWS:
        log.info("Hors Windows : gestion Office ignorée.")
        return

    word = _get_word_app()
    launched_word = False
    if word is not None:
        try:
            visible = word.Visible
            if not visible:
                launched_word = True
        except Exception:
            launched_word = True
        _set_word_options(word, active)
        if launched_word:
            try:
                word.Quit()
            except Exception:
                pass
    else:
        log.info("Word non trouvé : aucune correction Word à piloter.")

    excel = _get_excel_app()
    if excel is not None:
        _set_excel_options(excel, active)

    ppt = _get_powerpoint_app()
    if ppt is not None:
        _set_powerpoint_options(ppt, active)

    log.info("Protection Microsoft Office réglée sur active=%s", active)
