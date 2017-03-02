#!/usr/bin/env python
# Copyright 2015-2017 Yelp Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import
from __future__ import unicode_literals

from paasta_tools.utils import paasta_print
from paasta_tools.frameworks.native_scheduler import NativeScheduler

class AdhocScheduler(NativeScheduler):
    def __init__(self, *args, **kwargs):
        self.dry_run = kwargs.pop('dry_run')
        self.number_of_runs = 0
        super(AdhocScheduler, self).__init__(*args, **kwargs)

    def need_more_tasks(self, *args, **kwargs):
        if self.number_of_runs == 0:
            self.number_of_runs += 1
            return True
        else:
            return False

    def kill_tasks_if_necessary(self, *args, **kwargs):
        return

    def statusUpdate(self, driver, update):
        super(AdhocScheduler, self).statusUpdate(driver, update)

        # task ran and finished
        if self.number_of_runs > 0 and len(self.tasks_with_flags) == 0:
            driver.stop()
