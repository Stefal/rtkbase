import configparser
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ntrip_routing import source_catalog,route_settings,resolve_route,ex_command,settings_context,desired_sources,validate_channel_update,register_source

class RoutingTests(unittest.TestCase):
    def config(self):
        c=configparser.ConfigParser(interpolation=None)
        c['main']={'receiver_format':"'sbf'",'tcp_port':"'5015'"}
        for channel in 'ABCDEF':
            k=channel.lower();c['ntrip_'+channel]={'svr_addr_'+k:"'crtk.net'",'svr_port_'+k:"'2101'",'svr_pwd_'+k:"'secret:&'",'mnt_name_'+k:"'TEST'",'rtcm_msg_'+k:"'1005(10),1077'"}
        c['receiver_stream_um980']={'stream_um980_device':'/dev/serial/by-id/usb-FTDI-identity','stream_um980_port':'5016','stream_um980_format':'rtcm3','stream_um980_label':'UM980'}
        return c
    def test_legacy_routes_keep_main_receiver(self):
        c=self.config()
        for channel in 'ABCDEF':self.assertEqual(resolve_route(c,channel).source.identity,'main')
    def test_primary_saved_model_labels_profile_and_ntrip_without_changing_route(self):
        c=self.config();before=resolve_route(c,'A')
        c['main']['receiver']="'Septentrio_Mosaic-X5'"
        after=resolve_route(c,'A')
        self.assertEqual(after.source.label,'Septentrio_Mosaic-X5')
        self.assertEqual((after.source.identity,after.source.port,after.source.format),
                         (before.source.identity,before.source.port,before.source.format))
        self.assertEqual(settings_context(c)['receiver_sources'][0].label,'Septentrio_Mosaic-X5')
        c['main']['receiver']="''"
        self.assertEqual(source_catalog(c)['main'].label,'Main receiver')
    def test_channel_selection_and_messages_are_independent(self):
        c=self.config();c['ntrip_B']['ntrip_b_source']='um980';c['ntrip_B']['rtcm_msg_b']='1005(5),1077,1087'
        a=resolve_route(c,'A');b=resolve_route(c,'B')
        self.assertEqual(a.source.port,5015);self.assertEqual(b.source.port,5016)
        self.assertNotEqual(a.messages,b.messages);self.assertEqual(a.port,b.port)
    def test_command_order_encoding_and_no_receiver_write_options(self):
        route=resolve_route(self.config(),'A');cmd=ex_command('/private/str2str',route,'48 2 170')
        self.assertLess(cmd.index('-msg'),cmd.index('-out'))
        self.assertIn('secret:&@',cmd[cmd.index('-out')+1])
        self.assertNotIn('secret',repr(route));self.assertNotIn('-b',cmd);self.assertNotIn('-c',cmd)
    def test_duplicate_ports_and_devices_rejected(self):
        c=self.config();c['receiver_stream_um980']['stream_um980_port']='5015'
        with self.assertRaises(ValueError):source_catalog(c)
        c=self.config();c['receiver_stream_second']={'stream_second_device':'/dev/serial/by-id/usb-FTDI-identity','stream_second_port':'5017','stream_second_format':'rtcm3'}
        with self.assertRaises(ValueError):source_catalog(c)
    def test_missing_receiver_is_not_silently_replaced(self):
        c=self.config();c['ntrip_A']['ntrip_a_source']='unplugged'
        with self.assertRaises(ValueError):resolve_route(c,'A')
    def test_mountpoints_empty_by_default(self):
        c=self.config();c.remove_section('ntrip_F');self.assertEqual(route_settings(c,'F')['mnt_name_f'],'')
    def test_invalid_input_rejected(self):
        for key,value in [('svr_port_a','65536'),('rtcm_msg_a','1077(0)'),('rtcm_msg_a','1077,-out'),('svr_addr_a','host/name'),('mnt_name_a','')]:
            c=self.config();c['ntrip_A'][key]=value
            with self.assertRaises(ValueError):resolve_route(c,'A')
        with self.assertRaises(ValueError):ex_command('/private/str2str',resolve_route(self.config(),'A'),'nan 2 170')

    def test_settings_context_retains_values_and_reports_missing_sources(self):
        c=self.config();c['ntrip_C']['ntrip_c_source']='missing'
        context=settings_context(c,('A','B'))
        self.assertEqual(len(context['ntrip_channels']),6)
        self.assertTrue(context['ntrip_channels'][0]['installed'])
        self.assertFalse(context['ntrip_channels'][2]['installed'])
        self.assertTrue(context['ntrip_channels'][2]['source_missing'])
        self.assertEqual(context['ntrip_channels'][2]['source'],'missing')
        self.assertEqual(context['ntrip_channels'][0]['fields'][2]['type'],'password')
        self.assertEqual(c['ntrip_C']['ntrip_c_source'],'missing')

    def test_only_active_receivers_are_opened_once(self):
        c=self.config();c['ntrip_B']['ntrip_b_source']='um980';c['ntrip_E']['ntrip_e_source']='um980'
        self.assertEqual(list(desired_sources(c,['A','B','E'])),['um980'])
        self.assertEqual(desired_sources(c,['A']),{})
    def test_invalid_update_does_not_change_existing_configuration(self):
        c=self.config()
        with self.assertRaises(ValueError):validate_channel_update(c,'A',{'ntrip_a_source':'missing'})
        self.assertNotIn('ntrip_a_source',c['ntrip_A'])
        candidate=validate_channel_update(c,'A',{'ntrip_a_source':'um980'})
        self.assertEqual(resolve_route(candidate,'A').source.identity,'um980')
        self.assertEqual(resolve_route(c,'A').source.identity,'main')
    def test_password_delimiters_are_rejected_without_invented_encoding(self):
        c=self.config();c['ntrip_A']['svr_pwd_a']='password@caster'
        with self.assertRaises(ValueError):ex_command('/private/str2str',resolve_route(c,'A'),'48 2 170')

    def test_registration_is_validated_and_keeps_existing_config(self):
        c=self.config();payload={'identity':'x20p','label':'u-blox ZED-X20P','device':'/dev/serial/by-id/usb-u-blox-data','format':'ubx','port':5017}
        candidate=register_source(c,payload)
        self.assertEqual(source_catalog(candidate)['x20p'].port,5017)
        self.assertNotIn('receiver_stream_x20p',c.sections())
        for changes in ({'port':5015},{'identity':'main'},{'device':'/dev/ttyACM0'},{'device':'/dev/serial/by-id/usb-Septentrio-123-if04'},{'label':"invalid'name"},{'format':'unknown'}):
            with self.assertRaises(ValueError):register_source(c,{**payload,**changes})
    def test_first_time_configuration_can_render_without_receiver_format(self):
        c=self.config();c['main']['receiver_format']="''"
        self.assertEqual(len(settings_context(c)['ntrip_channels']),6)
        with self.assertRaises(ValueError):resolve_route(c,'A')

if __name__=='__main__':unittest.main()
