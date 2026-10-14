"""Default endpoint notification guards; all COM ownership is simulated."""
import threading
import unittest
import weakref
import gc

from hugin.errors import HuginError
from hugin.windows.audio_endpoints import AudioEndpointNotifications, DefaultDeviceChanges


class FakeCOM:
    def __init__(self):
        self.calls=[]
        self.fail=None
        self.enumerator=object()
        self.sink=object()
        self.pointer=object()
        self.messages=None
    def step(self,name):
        self.calls.append((name,threading.get_ident()))
        if self.fail==name:raise RuntimeError('PRIVATE device name')
    def initialize(self):self.step('initialize')
    def uninitialize(self):self.step('uninitialize')
    def create_enumerator(self):self.step('create');return self.enumerator
    def create_callback(self,messages):
        self.step('callback');self.messages=messages
        return self.sink,self.pointer
    def register(self,enumerator,pointer):
        assert enumerator is self.enumerator and pointer is self.pointer
        self.step('register')
    def unregister(self,enumerator,pointer):
        assert enumerator is self.enumerator and pointer is self.pointer
        self.step('unregister')
    def release(self,pointer):
        self.step('release_callback' if pointer is self.pointer else 'release_enumerator')


class AudioEndpointContracts(unittest.TestCase):
    def test_close_before_open_is_final(self):
        backend=FakeCOM();owner=AudioEndpointNotifications(backend=backend)
        owner.close()
        with self.assertRaises(HuginError):owner.open(lambda action:None)
        self.assertEqual(backend.calls,[])

    def test_failed_cleanup_has_strong_owner_until_successful_recovery(self):
        backend=FakeCOM();owner=AudioEndpointNotifications(backend=backend)
        owner.open(lambda action:None);backend.fail='unregister'
        with self.assertRaises(HuginError):owner.close()
        reference=weakref.ref(owner);del owner;gc.collect()
        self.assertIsNotNone(reference())
        backend.fail=None;reference().close();gc.collect()
        self.assertIsNone(reference())

    def test_failed_initialization_with_no_com_resource_does_not_leave_live_owner(self):
        backend=FakeCOM();backend.fail='initialize'
        owner=AudioEndpointNotifications(backend=backend)
        with self.assertRaises(HuginError):owner.open(lambda action:None)
        self.assertTrue(owner.closed)
        reference=weakref.ref(owner);del owner;gc.collect()
        self.assertIsNone(reference())

    def test_all_render_capture_roles_emit_only_action_and_ignore_unknown_values(self):
        actions=[];messages=DefaultDeviceChanges(actions.append)
        for flow in (0,1):
            for role in (0,1,2):self.assertEqual(messages.handle(flow,role),0)
        for flow,role in ((2,0),(-1,0),(0,3),(0,-1),(True,0),(0,'0')):
            self.assertEqual(messages.handle(flow,role),0)
        self.assertEqual(actions,['devices_changed']*6)
        messages.disable();messages.handle(0,0)
        self.assertEqual(len(actions),6)

    def test_callback_failures_are_sanitized_and_never_escape_native_boundary(self):
        errors=[]
        def notify(action):raise RuntimeError('PRIVATE device name')
        messages=DefaultDeviceChanges(notify,lambda code,phase:errors.append((code,phase)))
        self.assertLess(messages.handle(0,0),0)
        self.assertNotIn('PRIVATE',str(messages.error))
        self.assertEqual(errors,[('input_failed','audio_endpoints_callback')])
        self.assertEqual(messages.handle(0,0),0,'disabled after callback failure')

    def test_register_and_unregister_use_identical_held_pointer_on_owner_thread(self):
        backend=FakeCOM();owner=AudioEndpointNotifications(backend=backend)
        self.assertTrue(owner.closed);self.assertFalse(owner.ready)
        owner.open(lambda action:None)
        self.assertTrue(owner.ready);self.assertFalse(owner.closed)
        owner.close();owner.close()
        self.assertTrue(owner.closed)
        self.assertEqual([name for name,_ in backend.calls],['initialize','create','callback','register',
            'unregister','release_callback','release_enumerator','uninitialize'])
        self.assertEqual({thread for _,thread in backend.calls},{threading.get_ident()})
        with self.assertRaises(HuginError):owner.open(lambda action:None)

    def test_unregister_failure_keeps_com_and_callback_until_explicit_retry(self):
        backend=FakeCOM();owner=AudioEndpointNotifications(backend=backend)
        owner.open(lambda action:None);backend.fail='unregister'
        with self.assertRaises(HuginError):owner.close()
        self.assertFalse(owner.closed);self.assertFalse(owner.ready)
        self.assertNotIn('uninitialize',[name for name,_ in backend.calls])
        self.assertIs(owner._callback,backend.pointer)
        self.assertIs(owner._sink,backend.sink)
        self.assertIs(owner._enumerator,backend.enumerator)
        backend.fail=None;owner.close()
        self.assertTrue(owner.closed)
        self.assertNotIn('PRIVATE',str(owner.error))

    def test_partial_open_failures_release_only_acquired_resources(self):
        for phase in ('initialize','create','callback','register'):
            with self.subTest(phase=phase):
                backend=FakeCOM();backend.fail=phase
                owner=AudioEndpointNotifications(backend=backend)
                with self.assertRaises(HuginError):owner.open(lambda action:None)
                backend.fail=None;owner.close()
                self.assertTrue(owner.closed)
                names=[name for name,_ in backend.calls]
                self.assertNotIn('unregister',names)
                self.assertEqual(names.count('uninitialize'),int(phase!='initialize'))

    def test_release_failure_retains_remaining_resources_without_repeating_unregister(self):
        backend=FakeCOM();owner=AudioEndpointNotifications(backend=backend)
        owner.open(lambda action:None);backend.fail='release_callback'
        with self.assertRaises(HuginError):owner.close()
        self.assertFalse(owner.closed)
        backend.fail=None;owner.close()
        self.assertEqual([name for name,_ in backend.calls].count('unregister'),1)
        self.assertTrue(owner.closed)

    def test_callback_failure_invalidates_owner_and_keeps_sanitized_reason(self):
        backend=FakeCOM();owner=AudioEndpointNotifications(backend=backend)
        def notify(action):raise RuntimeError('PRIVATE device name')
        owner.open(notify)
        self.assertLess(backend.messages.handle(0,0),0)
        self.assertFalse(owner.ready)
        self.assertEqual(owner.error.code,'input_failed')
        self.assertNotIn('PRIVATE',str(owner.error))
        owner.close();self.assertTrue(owner.closed)

    def test_uninitialize_failure_retains_apartment_without_releasing_twice(self):
        backend=FakeCOM();owner=AudioEndpointNotifications(backend=backend)
        owner.open(lambda action:None);backend.fail='uninitialize'
        with self.assertRaises(HuginError):owner.close()
        self.assertFalse(owner.closed)
        backend.fail=None;owner.close()
        names=[name for name,_ in backend.calls]
        self.assertEqual(names.count('release_callback'),1)
        self.assertEqual(names.count('release_enumerator'),1)
        self.assertEqual(names.count('uninitialize'),2)
        self.assertTrue(owner.closed)

    def test_foreign_thread_cannot_open_again_or_release_com(self):
        backend=FakeCOM();owner=AudioEndpointNotifications(backend=backend)
        owner.open(lambda action:None)
        errors=[]
        def foreign():
            try:owner.close()
            except HuginError as error:errors.append(error)
        thread=threading.Thread(target=foreign);thread.start();thread.join(1)
        self.assertEqual(len(errors),1);self.assertTrue(owner.ready)
        self.assertNotIn('unregister',[name for name,_ in backend.calls])
        owner.close()


if __name__=='__main__':unittest.main()
