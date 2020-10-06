#Appdaemon app adding SSL certificate sensor to your Home Assistant

Please refer to corresponding products documentation to get more info on that (sorry guys, this just works and I'm to lazy to give more details on how to set this up)

You set your HASS, connect it with Appdaemon, and provide the path to your PEM-formatted SSL cert to app config

Cert days left until expiration and some additional data sent to HASS sensor named `sensor.ssl_expiration_days`. Feel free to finetune this.