import logging
from robot.libraries.BuiltIn import BuiltIn
from _common.libraries.dataprovider import dataprovider
from _common.libraries.requests.api_requests import send_request


class Notifications:
    """Klicova slova pro praci s notifikacemi."""

    def __init__(self):
        self.builtin = BuiltIn()
        self.session = self.builtin.get_variable_value('${SESSION_ID}')
        self.notif_dict = None

    def get_notification_list(self):
        """KW vraci python slovnik se vsemi notifikacemi prihlaseneho uzivatele pomoci GET /notifications."""
        service_method = 'get'
        service_name = 'notifications'
        service_url = dataprovider.get_api_url(self.builtin.get_variable_value('${API_NAME}'), service_name)
        resp = send_request(self.session, service_method, service_url)
        self.notif_dict = resp.json()
        return self.notif_dict

    def delete_notifications(self, name=None, notif_dict=None, cnt=None):
        """KW smaze 'cnt' notifikaci prihlaseneho uzivatele podle jmena 'name' v notifikaci. Notifikace se mazou pomoci
        volani PATCH /notifications/{notification_id}.
        :param name: jmeno uvedene v notifikaci
        :param notif_dict: python slovnik, ktery obsahuje vsechny notifikace prihlaseneho uzivatele
        :param cnt: pocet notifikaci ke smazani
        """
        name = name if name is not None else dataprovider.get_var(self.builtin.get_variable_value('${DEL_NOTIF}'),
                                                                  'name')
        cnt = cnt if cnt is not None else dataprovider.get_var(self.builtin.get_variable_value('${DEL_NOTIF}'), 'cnt')
        notif_dict = self._get_notif_dict(notif_dict)
        # zjisti, jestli je slovnik s notifikacemi prazdny a pokud ano test zastavi, protoze neni co mazat
        assert self._is_notif_dict_empty(name, notif_dict), 'Nejsou testovaci data, test konci.'
        # ulozi pocet notifikaci s vybranym jmenem pred mazanim notifikaci
        notif_cnt_before = self._get_notif_cnt_by_name(name, notif_dict)
        # vytvori novy slovnik pouze s notifikacemi se jmenem 'name'
        notif_dict_single = self._get_notif_dict_single(name, notif_dict)
        # na zaklade 'cnt' smaze n anebo vsechny notifikace podle vybraneho jmena
        self._dismiss_notification(name, notif_dict_single, cnt)
        # send-request: prenacte seznam notifikaci uzivatele pomoci GET /notifications
        notif_dict = self.get_notification_list()
        # ulozi pocet notifikaci s vybranym jmenem po smazani notifikaci
        notif_cnt_after = self._get_notif_cnt_by_name(name, notif_dict)
        # check: overi, jestli doslo ke smazani pozadovaneho poctu notifikaci s vybranym jmenem
        self._check_notif(notif_cnt_before, notif_cnt_after, name, cnt)

    def _is_notif_dict_empty(self, name, notif_dict):
        """Metoda nejprve overi, jestli je slovnik s notifikacemi 'notif_dict' prazdny. Pokud ne, potom dale overi,
        jestli ve slovniku existuji notifikace se jmenem 'name'. Pokud je slovnik prazdny anebo pokud neobsahuje
        notifikace se jmenem 'name', potom metoda vraci False a test konci, jelikoz neni co mazat.
        """
        if len(notif_dict['results']) > 0:
            return self._get_notif_cnt_by_name(name, notif_dict) > 0
        else:
            return False

    @staticmethod
    def _get_notif_cnt_by_name(name, notif_dict):
        """Metoda vraci pocet notifikaci s vybranym jmenem."""
        notif_cnt = 0
        notif_dict_len = len(notif_dict['results'])
        for i in range(notif_dict_len):
            if name in notif_dict['results'][i]['userFullName']:
                notif_cnt += 1
        if notif_cnt == 0:
            logging.warning(f'Uzivatel nema dalsi notifikace od: {name}')
        return notif_cnt

    @staticmethod
    def _get_notif_dict_single(name, notif_dict):
        """Metoda vraci novy python slovnik, ktery obsahuje pouze notifikace s jedinym jmenem."""
        notif_dict_single = {'results': []}
        notif_dict_len = len(notif_dict['results'])
        for i in range(notif_dict_len):
            if name in notif_dict['results'][i]['userFullName']:
                notif_dict_single['results'].append(notif_dict['results'][i])
        return notif_dict_single

    def _dismiss_notification(self, name, notif_dict_single, cnt):
        """Metoda odstrani jednu anebo vice notifikaci 'cnt' pro vybrane jmeno 'name' uvedene v notifikaci. Na vstupu
        je slovnik s notifikacemi, ktery obsahuje pouze notifikace s jedinym jmenem. Notifikace se mazou po jedne pomoci
        volani PATCH /notifications/{notification_id}.
        """
        service_method = 'patch'
        service_name = 'notification_id'
        service_url = dataprovider.get_api_url(self.builtin.get_variable_value('${API_NAME}'), service_name)
        service_body = dataprovider.get_var(self.builtin.get_variable_value('${DEL_NOTIF}'), 'body')
        notif_dict = notif_dict_single
        notif_dict_len = len(notif_dict['results'])
        del_notif_counter = 0
        if cnt == 'all':
            pass
        elif notif_dict_len - cnt >= 0:
            notif_dict_len = cnt
        # mazani notifikaci podle 'id' notifikace
        for i in range(notif_dict_len):
            if name in notif_dict['results'][i]['userFullName']:
                service_body['id'] = notif_dict['results'][i]['id']
                # send-request: pro kazdou notifikaci se posle jeden request PATCH /notifications/{notification_id}
                send_request(self.session, service_method, service_url.format(notif_dict['results'][i]['id']),
                             service_body)
                del_notif_counter += 1
                logging.warning(f"maze se notifikace se jmenem: {notif_dict['results'][i]['userFullName']}")
                logging.warning(f"maze se id-cko notifikace: {notif_dict['results'][i]['id']}")
        logging.warning(f'smazano: {del_notif_counter} notifikaci od: {name}')

    @staticmethod
    def _check_notif(notif_cnt_before, notif_cnt_after, name, cnt):
        """Metoda overi, jestli doslo ke smazani vsech notifikaci pro vybrane jmeno a v pozadovanem poctu."""
        if cnt == 'all':
            assert notif_cnt_after == 0, f'Notifikace uzivatele {name} se nesmazaly'
        else:
            if notif_cnt_before - cnt >= 0:
                assert notif_cnt_after == (notif_cnt_before - cnt), f'pred: {notif_cnt_before}, po: {notif_cnt_after}'
            else:
                assert notif_cnt_after == 0, f'pred: {notif_cnt_before}, po: {notif_cnt_after}'

    def _get_notif_dict(self, notif_dict):
        """Metoda vraci python slovnik s notifikacemi uzivatele. Nejdrive se snazi vratit slovnik predany jako argument
        v KW 'delete notifications', pokud tento neexistuje, snazi se vratit slovnik ulozeny v ramci KW
        'get notification list'. Pokud ani tento neexistuje, vygeneruje novy slovnik s aktualnim poctem notifikaci.
        """
        if notif_dict:
            logging.warning(f"slovnik 'notif_dict' predan jako argument v KW 'delete ...'")
            self.notif_dict = notif_dict
            return notif_dict
        elif self.notif_dict:
            logging.warning(f"slovnik 'notif_dict' ulozen v ramci KW 'get notifications'")
            return self.notif_dict
        else:
            logging.warning(f"generuju novy slovnik: 'notif_dict'")
            return self.get_notification_list()