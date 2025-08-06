#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ВИПРАВЛЕНИЙ process_webhook.py для Python 3.6
# Правильна логіка: успіх = гудки (duration > 0) + скидання (cancel)

import sys
import json
import logging

# Python 3.6 сумісність - без f-strings
def analyze_call_result(disposition, duration, action_type):
    if disposition == 'cancel' and duration > 0:
        return 'success', "✅ {} відчинено!".format(action_type)
    elif disposition == 'busy':
        return 'busy', "❌ {} зайнято. Спробуйте ще раз.".format(action_type)
    # ... інша логіка
    
# ... решта коду з правильною логікою
