import hassapi as hass
import datetime
import ssl
import copy
from typing import Union

_default_sensor_name = "sensor.ssl_expiration_days"


class SSLCertificate:
    """
    unpacks PEM cert into attributes
    """

    _default_data_dict = {
        'subject': None,
        'issuer': None,
        'version': None,
        'serialNumber': None,
        'notBefore': None,
        'notAfter': None,
        'subjectAltName': None,
        'OCSP': None,
        'caIssuers': None,
    }

    _ssl_date_fmt = r'%b %d %H:%M:%S %Y %Z'

    @property
    def date_before(self):
        return self._to_datetime(self.notBefore) if self.notBefore else None

    @property
    def date_after(self):
        return self._to_datetime(self.notAfter) if self.notAfter else None

    @property
    def is_started(self) -> bool:
        """
        checks if notBefore < now()
        """
        return (datetime.datetime.now() - self._to_datetime(self.notBefore)).days > 0

    def __init__(self, pem_filename):
        self.filename = pem_filename
        self.exists = True
        self._data_dict = copy.deepcopy(self._default_data_dict)
        self.refresh()

    def refresh(self):
        """
        reload cert data
        """
        self._data_dict = copy.deepcopy(self._default_data_dict)
        try:
            cert_dict = ssl._ssl._test_decode_cert(self.filename)
            self._data_dict.update(cert_dict)
            for field, value in self._data_dict.items():
                setattr(self, field, value)
        except Exception:
            self.exists = False

    def expiration_days(self):
        if not self.date_after:
            return -1
        days_left = (self.date_after - datetime.datetime.now()).days
        return days_left if days_left > 0 else 0

    def _to_datetime(self, date_str):
        return datetime.datetime.strptime(date_str, self._ssl_date_fmt)

    def state(self) -> Union[int, str]:
        """
        returns readable cert state: `unknown` or `not started` -> <days left to expiration> -> `expired`
        """
        if not self.exists:
            return "unknown"

        if not self.is_started:
            return "not started"

        exp_days = self.expiration_days()

        return exp_days if exp_days else "expired"


class SSLExpiration(hass.Hass):
  """
  App adding the SSL certificate sensor for HASS
  """
  #initialize() function which will be called at startup and reload
  def initialize(self):
    self.cert = SSLCertificate(self.args["cert_file"])
    # Create a time object for 00:01:00
    time = datetime.time(0, 1, 0)
    self.run_daily(self.update_sensor, time)
    self.listen_event(self.update_sensor, "SSL_REFRESH")

  # update sensor state
  def update_sensor(self, event, data, kwargs):
    self.log(f"{datetime.datetime.now()}: SSL update triggered by {event}")
    self.cert.refresh()
    attrs = {
      "subject": self.cert.subject,
      "issuer": self.cert.issuer,
      "version": self.cert.version,
      "start_date": self.cert.date_before,
      "end_date": self.cert.date_after
    }
    self.set_state(_default_sensor_name, state=self.cert.state(), attributes=attrs, replace=True)
  