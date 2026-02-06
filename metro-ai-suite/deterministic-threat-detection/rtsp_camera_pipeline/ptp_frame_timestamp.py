# 
# Copyright (C) 2026 Intel Corporation. 
# 
# SPDX-License-Identifier: Apache-2.0 
#

import json
from time import ctime, sleep
import ntplib
import requests
from datetime import datetime

class PTPFrameTimeStamp:
    def __init__(self):
        pass

    def _get_timestamp(self):
        return datetime.now().timestamp()

    def process(self, frame):
        frame.add_message(json.dumps({'ptp_timestamp': self._get_timestamp()}))
        return True
