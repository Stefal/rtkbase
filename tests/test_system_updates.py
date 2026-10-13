import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from system_updates import Store, queue, worker, status, PLAN, REFRESH, UPGRADE, parse_plan, redact


class FixtureStore(Store):
    def ensure(self):
        # Private test directory; production ownership checks remain enabled.
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)


class SystemUpdatesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = FixtureStore(self.temp.name)
        self.calls = []

    def control(self, *args):
        if '--property=LoadState' in args:
            return 'loaded'
        if '--property=ActiveState' in args:
            return 'inactive'
        return ''

    def runner(self, command, progress):
        self.calls.append(command)
        progress('working')
        return 'Inst example [1.0] (2.0 Debian:stable [arm64])\n' if command == PLAN else ''

    def refresh(self):
        queue('refresh', store=self.store, control=self.control)
        return worker(self.store, self.runner)

    def test_review_then_install(self):
        ready = self.refresh()
        self.assertEqual(ready['state'], 'ready')
        self.assertEqual(self.calls, [REFRESH, PLAN])
        queue('upgrade', ready['review']['id'], self.store, self.control)
        self.assertEqual(worker(self.store, self.runner)['state'], 'succeeded')
        self.assertEqual(self.calls, [REFRESH, PLAN, PLAN, UPGRADE])
        self.assertEqual(self.store.read('review'), {})

    def test_changed_plan_never_installs(self):
        ready = self.refresh()
        queue('upgrade', ready['review']['id'], self.store, self.control)
        result = worker(self.store, lambda command, progress: 'Inst other (1.0 Debian)')
        self.assertEqual(result['state'], 'failed')
        self.assertNotIn(UPGRADE, self.calls)

    def test_no_review_no_upgrade(self):
        with self.assertRaises(ValueError):
            queue('upgrade', store=self.store, control=self.control)

    def test_removal_rejected(self):
        with self.assertRaises(ValueError):
            parse_plan('Remv example [1.0]')

    def test_lock_failure_preserves_failure(self):
        queue('refresh', store=self.store, control=self.control)
        def failed(command, progress):
            raise RuntimeError('APT failed (exit 100)')
        self.assertEqual(worker(self.store, failed)['state'], 'failed')
        self.assertEqual(self.store.read('review'), {})

    def test_duplicate_request_not_replayed(self):
        self.refresh()
        with self.assertRaises(ValueError):
            worker(self.store, self.runner)

    def test_queued_request_blocks_second_request(self):
        queue('refresh', store=self.store, control=self.control)
        with self.assertRaises(ValueError):
            queue('refresh', store=self.store, control=self.control)

    def test_redaction(self):
        self.assertEqual(redact('Fetch https://user:password@host/path?token=secret done'), 'Fetch [repository] done')

    def test_unknown_action_rejected(self):
        with self.assertRaises(ValueError):
            queue('autoremove', store=self.store, control=self.control)

    def test_expired_review_does_not_install(self):
        ready = self.refresh()
        review = self.store.read('review')
        review['created'] = time.time() - 3601
        self.store.write('review', review)
        queue('upgrade', ready['review']['id'], self.store, self.control)
        self.assertEqual(worker(self.store, self.runner)['state'], 'failed')
        self.assertNotIn(UPGRADE, self.calls)

    def test_failed_service_start_allows_retry(self):
        def control(*args):
            if 'start' in args:
                raise RuntimeError('unavailable')
            return self.control(*args)
        with self.assertRaises(RuntimeError):
            queue('refresh', store=self.store, control=control)
        self.assertEqual(self.store.read('status')['state'], 'failed')
        queue('refresh', store=self.store, control=self.control)

    def test_interrupted_worker_is_reported_without_replay(self):
        self.store.write('status', dict(state='running', created=time.time()-60))
        self.assertEqual(status(self.store, self.control)['state'], 'failed')
        self.assertEqual(self.calls, [])

    def test_live_worker_is_not_marked_interrupted(self):
        self.store.write('status', dict(state='running', created=time.time()-60))
        def control(*args):
            return 'active' if '--property=ActiveState' in args else 'loaded'
        self.assertEqual(status(self.store, control)['state'], 'running')

    def test_progress_is_bounded(self):
        queue('refresh', store=self.store, control=self.control)
        def runner(command, progress):
            for i in range(100):
                progress(str(i))
            return self.runner(command, progress)
        self.assertEqual(len(worker(self.store, runner)['progress']), 40)

    def test_single_action_refreshes_then_installs(self):
        queue('update', store=self.store, control=self.control)
        result = worker(self.store, self.runner)
        self.assertEqual(result['state'], 'succeeded')
        self.assertEqual(self.calls, [REFRESH, PLAN, UPGRADE])
        self.assertEqual(self.store.read('review'), {})

    def test_single_action_refresh_failure_never_installs(self):
        queue('update', store=self.store, control=self.control)
        def failed(command, progress):
            self.calls.append(command)
            raise RuntimeError('repository failed')
        self.assertEqual(worker(self.store, failed)['state'], 'failed')
        self.assertEqual(self.calls, [REFRESH])

    def test_success_date_survives_later_failure_and_restart(self):
        queue('update', store=self.store, control=self.control)
        worker(self.store, self.runner)
        date = self.store.read('last-update')['completed_at']
        queue('update', store=self.store, control=self.control)
        def failed(command, progress):
            raise RuntimeError('upgrade failed')
        worker(self.store, failed)
        reloaded = FixtureStore(self.temp.name)
        self.assertEqual(status(reloaded, self.control)['last_successful_update'], date)

    def test_refresh_alone_does_not_record_installation(self):
        self.refresh()
        self.assertIsNone(status(self.store, self.control)['last_successful_update'])

    def test_no_available_packages_preserves_prior_date(self):
        self.store.write('last-update', {'completed_at': 1234567890})
        queue('update', store=self.store, control=self.control)
        self.assertEqual(worker(self.store, lambda command, progress: '')['state'], 'succeeded')
        self.assertEqual(status(self.store, self.control)['last_successful_update'], 1234567890)


if __name__ == '__main__':
    unittest.main()
