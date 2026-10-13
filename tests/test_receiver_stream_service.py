from pathlib import Path
import sys,unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from receiver_stream_service import StreamCoordinator
from ntrip_routing import ReceiverSource

class CoordinatorTests(unittest.TestCase):
    def spec(self,port=5016):return ReceiverSource('um980','UM980','rtcm3',port,'/dev/serial/by-id/usb-FTDI-id')
    def test_multiple_channels_share_one_source_and_last_stop_closes(self):
        stream=Mock(error=None);factory=Mock(return_value=stream);coordinator=StreamCoordinator(factory)
        source=self.spec();coordinator.reconcile({'um980':source},0);coordinator.reconcile({'um980':source},2)
        factory.assert_called_once_with(source);stream.close.assert_not_called()
        coordinator.reconcile({},4);stream.close.assert_called_once();self.assertEqual(coordinator.streams,{})
    def test_changed_source_is_closed_before_replacement(self):
        events=[]
        def factory(spec):
            events.append(('open',spec.port));return Mock(error=None,close=lambda:events.append(('close',spec.port)))
        coordinator=StreamCoordinator(factory);coordinator.reconcile({'um980':self.spec()},0);coordinator.reconcile({'um980':self.spec(5017)},2)
        self.assertEqual(events,[('open',5016),('close',5016),('open',5017)]);coordinator.close()
    def test_busy_input_backoff_preserves_other_sources(self):
        healthy=Mock(error=None)
        def factory(spec):
            if spec.identity=='um980':raise RuntimeError('port busy')
            return healthy
        factory=Mock(side_effect=factory);coordinator=StreamCoordinator(factory)
        other=ReceiverSource('x20p','X20P','ubx',5017,'/dev/serial/by-id/usb-u-blox')
        desired={'um980':self.spec(),'x20p':other};coordinator.reconcile(desired,0);coordinator.reconcile(desired,2)
        self.assertEqual(factory.call_count,2);self.assertIn('um980',coordinator.errors);self.assertIn('x20p',coordinator.streams)
        coordinator.reconcile(desired,31);self.assertEqual(factory.call_count,3);coordinator.close();healthy.close.assert_called_once()
    def test_reader_error_closes_and_retries_later(self):
        stream=Mock(error=None);factory=Mock(return_value=stream);coordinator=StreamCoordinator(factory)
        desired={'um980':self.spec()};coordinator.reconcile(desired,0);stream.error='disconnected';coordinator.reconcile(desired,2)
        stream.close.assert_called_once();self.assertNotIn('um980',coordinator.streams);coordinator.reconcile(desired,4);factory.assert_called_once()

    def test_usb_loss_and_recovery_leave_other_receiver_open(self):
        failed=Mock(error=None);recovered=Mock(error=None);healthy=Mock(error=None)
        attempts=[]
        def factory(spec):
            attempts.append(spec.identity)
            if spec.identity=='x20p':return healthy
            return failed if attempts.count('um980')==1 else recovered
        coordinator=StreamCoordinator(factory)
        other=ReceiverSource('x20p','X20P','ubx',5017,'/dev/serial/by-id/usb-u-blox')
        desired={'um980':self.spec(),'x20p':other}
        coordinator.reconcile(desired,0)
        failed.error='USB disconnected'
        coordinator.reconcile(desired,2)
        failed.close.assert_called_once();healthy.close.assert_not_called()
        self.assertIs(coordinator.streams['x20p'][1],healthy)
        coordinator.reconcile(desired,31)
        self.assertEqual(attempts,['um980','x20p'])
        coordinator.reconcile(desired,32)
        self.assertEqual(attempts,['um980','x20p','um980'])
        self.assertIs(coordinator.streams['um980'][1],recovered)
        healthy.close.assert_not_called();self.assertNotIn('um980',coordinator.errors)
        coordinator.close()

if __name__=='__main__':unittest.main()
