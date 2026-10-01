#!/usr/bin/env python3
"""Verify an APK's targeted changes after apktool disassembly; no APK/source in Git."""
import argparse
import re
from pathlib import Path

UTILITY = 'de/mash/android/calendar/core/utility/Utility.smali'
CREATE = 'public static createPromotionEvent(Landroid/content/Context;ILjava/util/List;)V'
PRODUCT = 'public static isProVersion(Landroid/content/Context;Lde/mash/android/calendar/core/purchase/InAppProduct;)Z'
DATABASE = 'public static isProVersion(Landroid/content/Context;Landroid/database/sqlite/SQLiteDatabase;)Z'


def methods(path):
    text = path.read_text()
    return {m.group(1): m.group(2) for m in re.finditer(
        r'^\.method ([^\n]*)\n(.*?)^\.end method', text, re.M | re.S)}


def instructions(body):
    # Exclude annotations/debug metadata, retaining only real opcodes and operands.
    body = re.sub(r'\.annotation\b.*?\.end annotation', '', body, flags=re.S)
    return [line.strip() for line in body.splitlines()
            if line.strip() and not line.strip().startswith(('.', ':', '#'))]


def verify(original, patched, premium=False):
    before = methods(next(original.glob('smali*/' + UTILITY)))
    after = methods(next(patched.glob('smali*/' + UTILITY)))
    assert set(before) == set(after), 'Utility methods changed unexpectedly'
    assert instructions(after[CREATE])[0] == 'return-void', 'Free Edition events still generated'
    targets = {CREATE}
    if premium:
        targets |= {PRODUCT, DATABASE}
        for name in (PRODUCT, DATABASE):
            assert instructions(after[name])[:2] == ['const/4 v0, 0x1', 'return v0'], name
    # Compare real instruction streams, independent of decompiler debug formatting.
    for name in set(before) - targets:
        assert instructions(before[name]) == instructions(after[name]), 'Unexpected change: ' + name
    print('PASS: promotion generation disabled; ' +
          ('two premium checks enabled; ' if premium else 'premium checks unchanged; ') +
          'all other Utility instruction streams unchanged')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('original', type=Path)
    p.add_argument('patched', type=Path)
    p.add_argument('--premium', action='store_true')
    args = p.parse_args()
    verify(args.original, args.patched, args.premium)
